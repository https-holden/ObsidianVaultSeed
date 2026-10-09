#!/usr/bin/env python3
"""Bring things into the vault: files, folders, web pages, emails. Standard library only.

    python3 bin/ingest.py add <file|folder|url> [...]     into Clippings/ (someone else wrote it)
    python3 bin/ingest.py add --mine <file|folder> [...]  into your own notes (you wrote it)
    python3 bin/ingest.py add --links links.txt           every URL in a text file, one per line
    python3 bin/ingest.py waiting                         what the librarian has not filed yet
    python3 bin/ingest.py rename "Old name" "New name"    rename a note that is still waiting

What it does with each thing:

    .md .markdown .txt   the text; a Notion export's long id is dropped from the name,
                         and images it links to are copied into Attachments/
    .html .htm, URLs     the page as Markdown, with its title, author and date
    .docx                the text, with headings, lists and tables
    .eml                 the email: subject, sender, date and body
    .pdf                 attached and embedded; its text too if `pypdf` is installed
                         (python3 -m pip install --user pypdf)
    .csv                 a Markdown table
    anything else        copied to Attachments/ and embedded (photos, audio, video)

Rules it keeps, like every script in this vault:

- It never overwrites. A name already in the vault gets " (2)", " (3)".
- The imported text sits between <!-- ingest:start --> and <!-- ingest:end -->.
  Whatever you write below the end marker is yours and is never touched again.
- En and em dashes become hyphens, because the lint refuses them.
- A note gets every property its folder's template has, so the lint passes, plus
  `ingested: <today>`. It has no `filed:` until the librarian files it, and that
  missing line is what `waiting` looks for.
- It never sets `modified`, which means "last edited by hand".

Add --dry-run to `add` to see what would be made without writing anything.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import email
import email.policy
import email.utils
import html
import io
import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

VAULT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((VAULT / "bin" / "vault.json").read_text(encoding="utf-8"))
ATTACH = VAULT / "Attachments"
START, END = "<!-- ingest:start -->", "<!-- ingest:end -->"
DASHES = str.maketrans({"\u2013": "-", "\u2014": "-"})
SKIP_DIRS = {".git", ".obsidian", ".trash", ".claude", "bin", "node_modules", "__pycache__"}
NOTION_ID = re.compile(r"\s+[0-9a-f]{32}$")
URL = re.compile(r"^https?://\S+$")
TODAY = dt.date.today().isoformat()
DOC_EXT = {".md", ".markdown", ".txt", ".html", ".htm", ".docx", ".eml", ".csv", ".pdf", ".json"}


# ------------------------------------------------------------ the vault


def kind_folder(mine: bool) -> str:
    """Clippings/ for other people's writing; the vault's first authored kind for yours."""
    kinds = list(CONFIG["kinds"])
    if not mine:
        if "Clippings" not in kinds:
            sys.exit("This vault has no Clippings/ kind. Add it (see CLAUDE.md, adding a kind) or use --mine.")
        return "Clippings"
    for k in ("Notes", "Knowledge"):
        if k in kinds:
            return k
    authored = [k for k in kinds if k not in ("Clippings", "Daily")]
    if not authored:
        sys.exit("This vault has no folder for your own notes.")
    return authored[0]


def template_keys(folder: str) -> list[tuple[str, str]]:
    """(key, raw default) for every top-level property in the folder's template, in order."""
    name = CONFIG["kinds"][folder]["template"]
    text = (VAULT / "Templates" / name).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return []
    block = text[4:text.index("\n---", 3)]
    out: list[tuple[str, str]] = []
    for line in block.split("\n"):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            out.append((m.group(1), m.group(2)))
        elif out and line.strip():
            out[-1] = (out[-1][0], out[-1][1] + "\n" + line)
    return out


def note_names() -> set[str]:
    """Every note name in the vault, lower case. Obsidian links by name, so names are global."""
    names = set()
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".md"):
                names.add(unicodedata.normalize("NFC", fn[:-3]).lower())
    return names


def safe_name(title: str) -> str:
    title = unicodedata.normalize("NFC", title).translate(DASHES)
    title = re.sub(r'[\\/:*?"<>|#^\[\]]', " ", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    return title[:100].rstrip(" .") or "Untitled"


def unique_note(title: str, taken: set[str]) -> str:
    base = safe_name(title)
    name, n = base, 2
    while name.lower() in taken:
        name, n = "%s (%d)" % (base, n), n + 1
    taken.add(name.lower())
    return name


def attach(src: Path | None, data: bytes | None, filename: str, dry: bool) -> str:
    """Copy a file into Attachments/ under a free name; return that name for ![[...]]."""
    stem, ext = os.path.splitext(safe_name(filename))
    name, n = stem + ext, 2
    while (ATTACH / name).exists():
        name, n = "%s (%d)%s" % (stem, n, ext), n + 1
    if not dry:
        ATTACH.mkdir(exist_ok=True)
        if src is not None:
            shutil.copy2(src, ATTACH / name)
        else:
            (ATTACH / name).write_bytes(data or b"")
    return name


def yaml_value(value) -> str:
    if isinstance(value, list):
        return " []" if not value else "".join("\n  - " + json.dumps(v, ensure_ascii=False) for v in value)
    if value in ("", None):
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
        return " " + str(value)
    return " " + json.dumps(str(value), ensure_ascii=False)


def frontmatter(folder: str, fields: dict, carry: list[str]) -> str:
    lines = ["---"]
    keys = template_keys(folder)
    have = {k for k, _ in keys}
    for key, raw in keys:
        if key in fields and fields[key] not in ("", None, []):
            lines.append(key + ":" + yaml_value(fields[key]))
        else:
            default = raw.replace("{{date}}", TODAY).replace("{{title}}", "")
            lines.append(key + ":" + ((" " if default and not default.startswith("\n") else "") + default))
    for key in ("url", "author", "published"):
        if key not in have and fields.get(key):
            lines.append(key + ":" + yaml_value(fields[key]))
    lines.append("ingested: " + TODAY)
    lines.extend(carry)
    lines.append("---")
    return "\n".join(lines)


def write_note(folder: str, title: str, body: str, fields: dict, origin: str,
               taken: set[str], dry: bool, carry: list[str] | None = None) -> Path:
    name = unique_note(title, taken)
    path = VAULT / folder / (name + ".md")
    body = body.translate(DASHES).strip()
    text = "%s\n%s\n*Imported from %s on %s.*\n\n%s\n%s\n\n## Notes\n\n- \n" % (
        frontmatter(folder, fields, carry or []), START, origin.translate(DASHES), TODAY, body, END)
    if not dry:
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("ADDED  %s/%s.md  (from %s)" % (folder, name, origin))
    return path


# ------------------------------------------------------------ HTML to Markdown


class Markdown(HTMLParser):
    """Small HTML to Markdown converter: enough for articles, not for web apps."""

    DROP = {"script", "style", "noscript", "svg", "nav", "footer", "form", "aside", "iframe",
            "button", "template", "head"}
    BLOCK = {"p", "div", "section", "article", "main", "header", "figure", "figcaption",
             "table", "dl", "dt", "dd", "hr", "body"}

    def __init__(self, base: str = "", only: str | None = None):
        super().__init__(convert_charrefs=True)
        self.base, self.only = base, only
        self.out: list[str] = []
        self.drop = 0
        self.inside = 0 if only else 1
        self.lists: list[list] = []
        self.pre = 0
        self.href: list[str | None] = []
        self.quote_at: list[int] = []
        self.meta: dict[str, str] = {}
        self.title = ""
        self.in_title = False
        self.cells = 0  # cells in the current table row
        self.head = False  # the current row is a header row
        self.ruled = False  # the current table has its header rule

    def emit(self, text: str) -> None:
        if self.inside and not self.drop:
            self.out.append(text)

    def block(self) -> None:
        self.emit("\n\n")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"])
            return
        if tag == "title":
            self.in_title = True
        if self.only and tag == self.only:
            self.inside += 1
        if tag in self.DROP:
            self.drop += 1
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.block()
            self.emit("#" * int(tag[1]) + " ")
        elif tag in ("ul", "ol"):
            if not self.lists:
                self.block()
            self.lists.append([tag, 0])
        elif tag == "li":
            depth = max(len(self.lists) - 1, 0)
            if self.lists and self.lists[-1][0] == "ol":
                self.lists[-1][1] += 1
                mark = "%d. " % self.lists[-1][1]
            else:
                mark = "- "
            self.emit("\n" + "    " * depth + mark)
        elif tag == "br":
            self.emit("  \n")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag == "code" and not self.pre:
            self.emit("`")
        elif tag == "pre":
            self.pre += 1
            self.emit("\n\n```\n")
        elif tag == "blockquote":
            self.block()
            self.quote_at.append(len(self.out))
        elif tag == "a":
            href = a.get("href")
            self.href.append(urllib.parse.urljoin(self.base, href) if href and not href.startswith("#") else None)
            if self.href[-1]:
                self.emit("[")
        elif tag == "img":
            src = a.get("src") or a.get("data-src")
            if src and not src.startswith("data:"):
                self.emit("![%s](%s)" % ((a.get("alt") or "").replace("]", ""), urllib.parse.urljoin(self.base, src)))
        elif tag == "table":
            self.block()
            self.ruled = False
        elif tag == "tr":
            self.cells, self.head = 0, False
            self.emit("\n|")
        elif tag in ("td", "th"):
            self.cells += 1
            self.head = self.head or tag == "th"
            self.emit(" ")
        elif tag in self.BLOCK:
            self.block()

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in self.DROP:
            self.drop = max(self.drop - 1, 0)
            return
        if re.fullmatch(r"h[1-6]", tag) or tag in self.BLOCK:
            self.block()
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            if not self.lists:
                self.block()
        elif tag in ("td", "th"):
            self.emit(" |")
        elif tag == "tr":
            if not self.ruled and self.cells:
                self.emit("\n|" + " --- |" * self.cells)
                self.ruled = True
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag == "code" and not self.pre:
            self.emit("`")
        elif tag == "pre":
            self.pre = max(self.pre - 1, 0)
            self.emit("\n```\n\n")
        elif tag == "blockquote" and self.quote_at:
            at = self.quote_at.pop()
            inner = "".join(self.out[at:]).strip()
            del self.out[at:]
            self.emit("\n\n" + "\n".join("> " + ln if ln.strip() else ">" for ln in inner.split("\n")) + "\n\n")
        elif tag == "a" and self.href:
            href = self.href.pop()
            if href:
                self.emit("](%s)" % href)
        if self.only and tag == self.only:
            self.inside = max(self.inside - 1, 0)

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.pre:
            self.emit(data)
        else:
            self.emit(re.sub(r"\s+", " ", data))

    def markdown(self) -> str:
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+(?=[^\s-])", "\n", text)
        text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
        text = re.sub(r"(?m)^(\s*(?:-|\d+\.)) {2,}", r"\1 ", text)
        return re.sub(r"\n{3,}", "\n\n", text).strip()


def html_to_note(raw: str, base: str = "") -> tuple[str, str, dict]:
    """(title, markdown body, fields) from an HTML page."""
    lower = raw.lower()
    only = "article" if "<article" in lower else ("main" if "<main" in lower else None)
    parser = Markdown(base, only)
    parser.feed(raw)
    body = parser.markdown()
    if only and len(body) < 200:  # the article tag held a teaser, not the article
        parser = Markdown(base, None)
        parser.feed(raw)
        body = parser.markdown()
    m = parser.meta
    title = html.unescape(m.get("og:title") or parser.title or "").strip()
    author = m.get("author") or m.get("article:author") or m.get("twitter:creator") or ""
    published = (m.get("article:published_time") or m.get("datepublished") or m.get("date") or "")[:10]
    fields = {"author": ["[[%s]]" % safe_name(author)] if author and not author.startswith("http") else [],
              "published": published if re.fullmatch(r"\d{4}-\d{2}-\d{2}", published) else ""}
    return title, body, fields


# ------------------------------------------------------------ one reader per kind of file


def read_markdown(path: Path, dry: bool, used: set[Path]) -> tuple[str, list[str]]:
    """Body of a Markdown or text file, its old frontmatter kept, local images attached."""
    text = path.read_text(encoding="utf-8", errors="replace")
    carry: list[str] = []
    if text.startswith("---\n") and "\n---" in text[3:]:
        end = text.index("\n---", 3)
        own = {"categories", "created", "ingested", "filed", "modified", "url", "author", "published"}
        block_key = None
        for line in text[4:end].split("\n"):
            m = re.match(r"^([A-Za-z_][\w-]*):", line)
            if m:
                block_key = m.group(1)
            if block_key and block_key not in own:
                carry.append(line.translate(DASHES))
        text = text[end + 4:].lstrip("\n")

    def local_image(m: re.Match) -> str:
        target = urllib.parse.unquote(m.group(2).split(" ")[0])
        src = (path.parent / target).resolve()
        if re.match(r"^[a-z]+:", target) or not src.is_file():
            return m.group(0)
        used.add(src)
        return "![[%s]]" % attach(src, None, src.name, dry)

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", local_image, text)
    return text, carry


def read_docx(path: Path) -> str:
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))

    def para(p) -> str:
        parts = []
        for node in p.iter():
            if node.tag == w + "t":
                parts.append(node.text or "")
            elif node.tag == w + "tab":
                parts.append("\t")
            elif node.tag in (w + "br", w + "cr"):
                parts.append("\n")
        text = "".join(parts).strip()
        style = p.find("%spPr/%spStyle" % (w, w))
        style = (style.get(w + "val") if style is not None else "") or ""
        m = re.match(r"(?i)heading\s*(\d)", style)
        if text and m:
            return "#" * min(int(m.group(1)), 6) + " " + text
        if text and style.lower() == "title":
            return "# " + text
        if text and p.find("%spPr/%snumPr" % (w, w)) is not None:
            return "- " + text
        return text

    out = []
    body = root.find(w + "body")
    for child in list(body) if body is not None else []:
        if child.tag == w + "p":
            out.append(para(child))
        elif child.tag == w + "tbl":
            rows = [[" ".join(para(p) for p in cell.iter(w + "p")).strip().replace("|", "\\|")
                     for cell in row.iter(w + "tc")] for row in child.iter(w + "tr")]
            if rows:
                out.append(md_table(rows))
    return "\n\n".join(x for x in out if x)


def read_pdf(path: Path) -> str:
    try:
        import pypdf  # optional: python3 -m pip install --user pypdf
    except ImportError:
        return ("> [!note] Text not extracted\n> The PDF is attached above. To have its text "
                "pulled out too, run `python3 -m pip install --user pypdf` and ingest it again.")
    try:
        reader = pypdf.PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:  # a damaged or encrypted PDF should not stop a folder import
        return "> [!warning] Could not read the PDF's text (%s). It is attached above." % exc
    text = "\n\n".join(p for p in pages if p)
    return text or "> [!note] This PDF has no text layer (it may be a scan). It is attached above."


def md_table(rows: list[list[str]], limit: int = 1000) -> str:
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:limit + 1]]
    if len(rows) > limit + 1:
        lines.append("\n*%d more rows not shown; the full file is attached.*" % (len(rows) - limit - 1))
    return "\n".join(lines)


def read_csv(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows = [[c.replace("|", "\\|").replace("\n", " ") for c in r] for r in csv.reader(io.StringIO(text)) if r]
    return md_table(rows) if rows else "(empty file)"


def read_email(path: Path) -> tuple[str, str, dict]:
    msg = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
    part = msg.get_body(preferencelist=("plain", "html"))
    body = part.get_content() if part else ""
    if part is not None and part.get_content_type() == "text/html":
        body = html_to_note(body)[1]
    sender = email.utils.parseaddr(msg.get("from", ""))[0] or msg.get("from", "")
    try:
        sent = email.utils.parsedate_to_datetime(msg["date"]).date().isoformat() if msg["date"] else ""
    except (TypeError, ValueError):
        sent = ""
    fields = {"author": ["[[%s]]" % safe_name(sender)] if sender else [], "published": sent}
    return msg.get("subject", "") or path.stem, body, fields


def fetch(url: str) -> tuple[str, bytes]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh) vault-ingest/1.0", "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.headers.get("Content-Type", ""), res.read()


# ------------------------------------------------------------ the commands


def add_url(url: str, folder: str, taken: set[str], dry: bool) -> None:
    fields = {"url": url}
    try:
        ctype, data = fetch(url)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        host = urllib.parse.urlparse(url).netloc
        body = ("> [!warning] Not fetched yet\n> The page could not be read (%s). The librarian "
                "will try to find what it is.\n\n<%s>" % (exc, url))
        write_note(folder, host or url, body, fields, url, taken, dry)
        return
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        name = os.path.basename(urllib.parse.urlparse(url).path) or "download.pdf"
        stored = attach(None, data, name, dry)
        tmp = ATTACH / stored
        body = "![[%s]]\n\n%s" % (stored, read_pdf(tmp) if not dry else "")
        write_note(folder, os.path.splitext(name)[0], body, fields, url, taken, dry)
        return
    charset = re.search(r"charset=([\w-]+)", ctype)
    raw = data.decode(charset.group(1) if charset else "utf-8", errors="replace")
    title, body, more = html_to_note(raw, url)
    fields.update(more)
    write_note(folder, title or urllib.parse.urlparse(url).netloc, body, fields, url, taken, dry)


def add_file(path: Path, folder: str, mine: bool, taken: set[str], dry: bool, used: set[Path]) -> None:
    ext = path.suffix.lower()
    title = NOTION_ID.sub("", path.stem)
    origin = "`%s`" % path.name
    fields: dict = {}
    carry: list[str] = []
    if mine:
        st = path.stat()
        fields["created"] = dt.date.fromtimestamp(getattr(st, "st_birthtime", st.st_mtime)).isoformat()
    if ext in (".md", ".markdown", ".txt"):
        body, carry = read_markdown(path, dry, used)
        first = re.match(r"#\s+(.+)", body)
        if first and title.lower().startswith("untitled"):
            title = first.group(1)
    elif ext in (".html", ".htm"):
        t, body, more = html_to_note(path.read_text(encoding="utf-8", errors="replace"))
        title = t or title
        fields.update(more)
    elif ext == ".docx":
        body = read_docx(path)
    elif ext == ".eml":
        title, body, more = read_email(path)
        fields.update(more)
    elif ext == ".csv":
        body = read_csv(path)
        body = "![[%s]]\n\n%s" % (attach(path, None, path.name, dry), body)
    elif ext == ".json":
        body = "```json\n%s\n```" % path.read_text(encoding="utf-8", errors="replace").strip()
    elif ext == ".pdf":
        body = "![[%s]]\n\n%s" % (attach(path, None, path.name, dry), read_pdf(path))
    else:
        body = "![[%s]]" % attach(path, None, path.name, dry)
    if mine:
        fields["created"] = fields.get("created") or TODAY
    else:
        fields.setdefault("created", TODAY)
    write_note(folder, title, body, fields, origin, taken, dry, carry)


def add_folder(root: Path, folder: str, mine: bool, taken: set[str], dry: bool, used: set[Path]) -> None:
    docs, rest = [], []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
        for fn in sorted(files):
            if fn.startswith("."):
                continue
            p = Path(base) / fn
            (docs if p.suffix.lower() in DOC_EXT else rest).append(p)
    for p in docs:  # documents first, so the images they link are attached with them
        add_file(p, folder, mine, taken, dry, used)
    for p in rest:
        if p.resolve() not in used:
            add_file(p, folder, mine, taken, dry, used)


def cmd_add(args) -> None:
    folder = kind_folder(args.mine)
    taken = note_names()
    used: set[Path] = set()
    items = list(args.items)
    if args.links:
        for line in Path(args.links).read_text(encoding="utf-8").splitlines():
            if URL.match(line.strip()):
                items.append(line.strip())
    if not items:
        sys.exit("Nothing to add. Give a file, a folder, a URL, or --links FILE.")
    for item in items:
        if URL.match(item):
            add_url(item, folder, taken, args.dry_run)
            continue
        p = Path(item).expanduser()
        if p.is_dir():
            add_folder(p, folder, args.mine, taken, args.dry_run, used)
        elif p.is_file():
            add_file(p, folder, args.mine, taken, args.dry_run, used)
        else:
            print("SKIPPED  %s  (no such file, folder or URL)" % item)
    if args.dry_run:
        print("(dry run: nothing was written)")
    else:
        print("Next: file them with `python3 bin/librarian.py`, or ask your AI to follow bin/librarian.md.")


def waiting_notes(filed_today: bool = False) -> list[Path]:
    """Notes with `ingested:` and no `filed:` (or, with filed_today, filed today)."""
    out = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and d != "Templates")
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = Path(root) / fn
            text = p.read_text(encoding="utf-8", errors="replace")
            head = text[:text.find("\n---", 3)] if text.startswith("---\n") else ""
            filed = re.search(r"^filed:\s*(\S*)", head, re.M)
            if re.search(r"^ingested:", head, re.M) and (
                    not filed or (filed_today and filed.group(1) == TODAY)):
                out.append(p)
    return out


def cmd_waiting(_args) -> None:
    notes = waiting_notes()
    if not notes:
        print("Nothing waiting to be filed.")
    for p in notes:
        print("WAITING  %s" % p.relative_to(VAULT))


def rename(old: str, new: str) -> Path:
    """Rename an imported note that is waiting or was filed today. Exits with the reason if not."""
    def stem(s: str) -> str:
        s = unicodedata.normalize("NFC", s.strip())
        return s[:-3] if s.endswith(".md") else s

    old, new = stem(old), stem(new)
    match = [p for p in waiting_notes(filed_today=True) if unicodedata.normalize("NFC", p.stem) == old]
    if not match:
        sys.exit("No note named %r waiting to be filed (or filed today). Only those can be renamed here." % old)
    if not new or any(c in new for c in "/\\:") or new.startswith("."):
        sys.exit("Not a plain note name: %r" % new)
    if new != new.translate(DASHES):
        sys.exit("The new name has an en or em dash. Use a hyphen, comma or parentheses.")
    if new.lower() in note_names() and new.lower() != old.lower():
        sys.exit("A note named %r already exists. Pick another name." % new)
    src = match[0]
    dest = src.with_name(new + ".md")
    src.rename(dest)
    print("RENAMED  %s  ->  %s" % (src.relative_to(VAULT), dest.relative_to(VAULT)))
    return dest


def cmd_rename(args) -> None:
    rename(args.old, args.new)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="bring in files, folders or URLs")
    a.add_argument("items", nargs="*")
    a.add_argument("--mine", action="store_true", help="you wrote these: file them with your own notes")
    a.add_argument("--links", help="a text file with one URL per line")
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=cmd_add)
    w = sub.add_parser("waiting", help="list notes not yet filed")
    w.set_defaults(func=cmd_waiting)
    r = sub.add_parser("rename", help="rename a waiting note")
    r.add_argument("old")
    r.add_argument("new")
    r.set_defaults(func=cmd_rename)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
