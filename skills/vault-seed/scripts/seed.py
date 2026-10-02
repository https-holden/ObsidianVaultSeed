#!/usr/bin/env python3
"""Scaffold an Obsidian vault from the seed assets. Standard library only.

    seed.py --archetype brain   --dest . --name "Acme Brain" --kinds Knowledge,Playbooks,People,Daily
    seed.py --archetype roadmap --dest roadmap --name "Acme roadmap" --project Acme --stop-hook
    seed.py --archetype content --dest lexicon --name "The lexicon" --kinds term,card --owner Holden
    seed.py --self-update        pull the seed repo this skill was installed from

Three rules it keeps, all learned in the vaults this was distilled from:

- It never overwrites. A file that already exists is left alone and reported
  as "kept", so the script is safe to rerun and safe to point at a vault that
  is already half built.
- It writes structure, never content. No note a person would have authored
  comes out of this script.
- --dry-run prints exactly what a real run would write and touches nothing.
"""
from __future__ import annotations

import argparse
import colorsys
import datetime
import json
import os
import shutil
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")
TEXT_EXT = {".md", ".base", ".json", ".css", ".py", ".js", ".txt", ".canvas", ""}
KNOWN_PLUGINS = ["home-button", "manual-modified", "resting-view", "sticky-bullets"]

# ------------------------------------------------------------ brain kinds
#
# One entry per kind of note the brain archetype knows how to shape. A kind is
# a folder (what a note IS), a template (its schema) and a Base (its table).
# A name that is not here still works: it gets the generic shape.

DRAFTS = ["draft", "verified", "stale"]

KINDS = {
    "Knowledge": dict(
        singular="Knowledge note", template="Knowledge",
        holds="One claim per note, third person. The title is the claim. Default landing folder.",
        nots="Procedures, wishes, raw logs.",
        title="a claim you could say in a sentence, one idea per note",
        props=[("categories", "[]"), ("created", "{{date}}"), ("status", "draft"), ("source", "")],
        status=DRAFTS, views=[("Recent", None, 15), ("Drafts", "draft", None), ("Stale", "stale", None)],
        home="Recent", body="\n"),
    "Playbooks": dict(
        singular="Playbook", template="Playbook",
        holds="Procedures actually run: when to use, inputs, steps, outputs, the last run.",
        nots="Theory, one-off logs.",
        title="an imperative (\"Rotate the signing key\")",
        props=[("categories", "[]"), ("created", "{{date}}"), ("status", "draft"), ("source", "")],
        status=DRAFTS, views=[("Drafts", "draft", None)], home="All playbooks",
        body="## When to use\n\n## Inputs\n\n## Steps\n\n1. \n\n## Outputs\n\n## Gotchas\n\n## Last run\n\n"),
    "People": dict(
        singular="Person", template="Person",
        holds="One note per person: who they are, their role, one line.",
        nots="Private details, anything they would not want written down.",
        title="the person's name, never a role (qualify in parentheses when two share one)",
        props=[("categories", "[]"), ("created", "{{date}}"), ("org", "[]"), ("role", ""), ("source", "")],
        body="\n"),
    "Projects": dict(
        singular="Project", template="Project",
        holds="One hub note per project: what it is for, its state, links to everything about it.",
        nots="The project's own notes (they link here through `project` or `categories`).",
        title="the project's name",
        props=[("categories", "[]"), ("created", "{{date}}"), ("status", "active"), ("start", ""), ("end", "")],
        status=["active", "paused", "done"], views=[("Active", "active", None)], home="Active",
        body="\n"),
    "Meetings": dict(
        singular="Meeting", template="Meeting",
        holds="One note per meeting or call, written on the day.",
        nots="Facts that outlive the meeting (copy them out to a claim note and link back).",
        title="`YYYY-MM-DD Title`",
        props=[("categories", "[]"), ("created", "{{date}}"), ("date", "{{date}}"), ("people", "[]"), ("topics", "[]")],
        body="## Notes\n\n## Decisions\n\n## Follow-ups\n\n"),
    "References": dict(
        singular="Reference", template="Reference",
        holds="Things that exist outside your head: books, tools, places, organisations.",
        nots="Dated, authored writing.",
        title="the thing's own title, exactly",
        props=[("categories", "[]"), ("created", "{{date}}"), ("author", "[]"), ("url", ""), ("rating", "")],
        body="\n"),
    "Notes": dict(
        singular="Note", template="Note",
        holds="Anything authored that is not another kind: essays, evergreen ideas, working notes.",
        nots="Things other people wrote (those are clippings).",
        title="for an idea, the idea as a claim; otherwise a plain name",
        props=[("categories", "[]"), ("created", "{{date}}"), ("topics", "[]")],
        body="\n"),
    "Clippings": dict(
        singular="Clipping", template="Clipping",
        holds="Things other people wrote, as clean Markdown (`obsidian:defuddle` or the Web Clipper).",
        nots="Anything authored here. The folder is the divider between your writing and ingested text.",
        title="the page's own title",
        props=[("categories", "[]"), ("author", "[]"), ("url", ""), ("created", "{{date}}"), ("published", "")],
        body="\n"),
    "Daily": dict(
        singular="Daily note", template="Daily Note",
        holds="`YYYY-MM-DD`, the raw log of one day. Never rewritten after the day.",
        nots="Knowledge (copy it out to its own note and link back).",
        title="`YYYY-MM-DD`",
        props=[("tags", "\n  - daily")], views=[("Recent days", None, 14)], home="Recent days",
        sort="file.name", body="## Notes\n\n## Learned\n\n"),
}

PROP_TYPES = {
    "aliases": "aliases", "cssclasses": "multitext", "tags": "tags", "categories": "multitext",
    "created": "date", "modified": "date", "status": "text", "source": "text", "org": "multitext",
    "role": "text", "start": "date", "end": "date", "date": "date", "people": "multitext",
    "topics": "multitext", "author": "multitext", "url": "text", "rating": "number",
    "published": "date", "type": "text", "key": "text", "short": "text", "keywords": "multitext",
    "kind": "text", "area": "text", "order": "number", "ideas": "multitext",
}


def kind_spec(name):
    if name in KINDS:
        return KINDS[name]
    singular = name[:-1] if name.endswith("s") and len(name) > 3 else name
    return dict(
        singular=singular, template=singular,
        holds="(say what a %s note holds)" % singular.lower(), nots="(say what does not belong)",
        title="(say how these are named)",
        props=[("categories", "[]"), ("created", "{{date}}")], body="\n")


def kind_template(spec):
    lines = ["---"]
    for key, val in spec["props"]:
        lines.append("%s:%s%s" % (key, "" if val.startswith("\n") else " ", val) if val else "%s: " % key)
    lines.append("---")
    return "\n".join(lines) + "\n" + spec.get("body", "\n")


def kind_base(folder, spec):
    cols = [k for k, _ in spec["props"] if k != "tags"]
    sort = spec.get("sort", "created")

    def view(name, status=None, limit=None):
        out = ["  - type: table", "    name: %s" % name]
        if status:
            out += ["    filters:", "      and:", '        - status == "%s"' % status]
        out += ["    order:", "      - file.name"] + ["      - %s" % c for c in cols]
        out += ["    sort:", "      - property: %s" % sort, "        direction: DESC"]
        if limit:
            out.append("    limit: %d" % limit)
        return out

    lines = ["filters:", "  and:", '    - file.inFolder("%s")' % folder,
             "properties:", "  file.name:", "    displayName: %s" % spec["singular"], "views:"]
    lines += view("All %s" % folder.lower())
    for name, status, limit in spec.get("views", []):
        lines += view(name, status, limit)
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------ plumbing


class Seeder:
    def __init__(self, dry):
        self.dry, self.made, self.kept = dry, [], []

    def write(self, path, data, binary=False):
        if os.path.exists(path):
            self.kept.append(path)
            return False
        self.made.append(path)
        if self.dry:
            return True
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as fh:
            fh.write(data)
        if path.endswith(".py"):
            os.chmod(path, 0o755)
        return True

    def copy_tree(self, src, dest, tokens):
        for root, dirs, files in os.walk(src):
            dirs.sort()
            for fn in sorted(files):
                if fn == ".DS_Store":
                    continue
                rel = os.path.relpath(os.path.join(root, fn), src)
                parts = ["." + p[4:] if p.startswith("dot-") else p for p in rel.split(os.sep)]
                if parts[-1] == "gitignore":
                    parts[-1] = ".gitignore"
                target = os.path.join(dest, *[sub(p, tokens) for p in parts])
                ext = os.path.splitext(fn)[1]
                if ext in TEXT_EXT:
                    with open(os.path.join(root, fn), encoding="utf-8") as fh:
                        self.write(target, sub(fh.read(), tokens))
                else:
                    with open(os.path.join(root, fn), "rb") as fh:
                        self.write(target, fh.read(), binary=True)


def sub(text, tokens):
    for key, val in tokens.items():
        text = text.replace("@@%s@@" % key, val)
    return text


def git_root(path):
    probe = path
    while not os.path.isdir(probe):
        probe = os.path.dirname(probe) or "."
    try:
        out = subprocess.run(["git", "-C", probe, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def self_update():
    root = git_root(SKILL_DIR)
    if not root:
        print("seed: not installed from a git checkout; using the bundled assets as they are")
        return 0
    try:
        out = subprocess.run(["git", "-C", root, "pull", "--ff-only", "--quiet"],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print("seed: could not reach the seed repo (%s); using what is on disk" % exc)
        return 0
    if out.returncode:
        print("seed: pull failed, using what is on disk:\n%s" % out.stderr.strip())
    else:
        head = subprocess.run(["git", "-C", root, "log", "-1", "--format=%h %s"],
                              capture_output=True, text=True).stdout.strip()
        print("seed: up to date at %s (%s)" % (head, root))
    return 0


def merge_settings(seeder, repo_root, stop_cmd=None, allow=()):
    """Add a Stop hook and/or permission rules to .claude/settings.json without disturbing the rest."""
    path = os.path.join(repo_root, ".claude", "settings.json")
    data = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except ValueError:
            print("seed: %s is not valid JSON; leaving it alone. Add this by hand:" % path)
            print("      Stop hook: %s" % stop_cmd)
            return
    before = json.dumps(data, sort_keys=True)
    if stop_cmd:
        stops = data.setdefault("hooks", {}).setdefault("Stop", [])
        if "session_check.py" not in json.dumps(stops):
            stops.append({"hooks": [{"type": "command", "command": stop_cmd, "timeout": 30,
                                     "statusMessage": "Checking the vault write-back"}]})
    if allow:
        rules = data.setdefault("permissions", {}).setdefault("allow", [])
        for rule in allow:
            if rule not in rules:
                rules.append(rule)
    if json.dumps(data, sort_keys=True) == before:
        return
    print("seed: %s .claude/settings.json" % ("would update" if seeder.dry else "updated"))
    if not seeder.dry:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")


def accent_css(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    return ("\n/* The vault's accent, so it is told apart from every other vault at a glance. */\n"
            "body {\n  --accent-h: %d;\n  --accent-s: %d%%;\n  --accent-l: %d%%;\n}\n"
            % (round(hue * 360), round(sat * 100), round(light * 100)))


# ------------------------------------------------------------ archetypes


def brain_tokens(kinds, working_memory):
    map_rows, kind_rows, home, schema, types = [], [], [], {}, {}
    for folder in kinds:
        spec = kind_spec(folder)
        map_rows.append("| `%s/` | %s | %s |" % (folder, spec["holds"], spec["nots"]))
        keys = ", ".join("`%s`" % k for k, _ in spec["props"])
        kind_rows.append("| %s | %s Template | %s.base | %s | %s |"
                         % (folder, spec["template"], folder, keys, spec["title"]))
        view = spec.get("home", "All %s" % folder.lower())
        home.append("## %s\n\n![[%s.base#%s]]\n" % (folder, folder, view))
        schema[folder] = {"template": "%s Template.md" % spec["template"]}
        if spec.get("status"):
            schema[folder]["status"] = spec["status"]
        for key, _ in spec["props"]:
            types[key] = PROP_TYPES.get(key, "text")
    drafts = [k for k in kinds if kind_spec(k).get("status") == DRAFTS]
    if drafts:
        home.append("## Needs attention\n\nDrafts are unchecked. Stale notes were contradicted "
                    "by something newer and need a rewrite or a delete.\n")
        for k in drafts:
            home.append("![[%s.base#Drafts]]\n" % k)
    memory = ("Three memory tiers. `Daily/` (when present) is the raw log and is never rewritten "
              "after the day. `Now.md` is working memory: Goals, Active, Waiting on, Recently done, "
              "Open questions, every bullet ending with the date it last moved; a bullet that "
              "settles into a fact becomes a note and the bullet links it. The kind folders are "
              "long-term." if working_memory else
              "There is no working-memory page yet. If the same in-flight items keep being "
              "re-explained to sessions, add a `Now.md` (dated bullets under Goals, Active, "
              "Waiting on, Recently done, Open questions) and record the decision.")
    return dict(
        MAP_ROWS="\n".join(map_rows), KIND_ROWS="\n".join(kind_rows),
        HOME_SECTIONS="\n".join(home), MEMORY_RULE=memory,
        DEFAULT_FOLDER=kinds[0], KIND_LIST=" ".join("%s/" % k for k in kinds),
        NOW_ROW=("| `Now.md` | Working memory: what is in flight, every bullet dated. | Facts "
                 "(they become notes), history. |\n" if working_memory else ""),
    ), schema, types


def seed_brain(seeder, dest, tokens, kinds, working_memory):
    extra, schema, types = brain_tokens(kinds, working_memory)
    tokens = dict(tokens, **extra)
    seeder.copy_tree(os.path.join(ASSETS, "brain"), dest, tokens)
    for folder in kinds:
        spec = kind_spec(folder)
        seeder.write(os.path.join(dest, folder, ".gitkeep"), "")
        seeder.write(os.path.join(dest, "Templates", "%s Template.md" % spec["template"]),
                     kind_template(spec))
        seeder.write(os.path.join(dest, "Templates", "Bases", "%s.base" % folder),
                     kind_base(folder, spec))
    for folder in ("Categories", "Attachments"):
        seeder.write(os.path.join(dest, folder, ".gitkeep"), "")
    seeder.write(os.path.join(dest, "bin", "vault.json"), json.dumps(
        {"kinds": schema, "draft_max_days": 14, "now_max_days": 14,
         "dash_exempt": [".obsidian/", ".git/", ".claude/", "bin/"]}, indent=2) + "\n")
    types.update({k: PROP_TYPES[k] for k in ("aliases", "cssclasses", "tags", "modified")})
    seeder.write(os.path.join(dest, ".obsidian", "types.json"),
                 json.dumps({"types": types}, indent=2) + "\n")
    if "Daily" in kinds:
        seeder.write(os.path.join(dest, ".obsidian", "daily-notes.json"), json.dumps(
            {"folder": "Daily", "format": "YYYY-MM-DD",
             "template": "Templates/Daily Note Template"}, indent=2) + "\n")
    if working_memory:
        with open(os.path.join(ASSETS, "optional", "Now.md"), encoding="utf-8") as fh:
            seeder.write(os.path.join(dest, "Now.md"), sub(fh.read(), tokens))
    return tokens


def seed_content(seeder, dest, tokens, kinds):
    types = kinds or ["term"]
    folders = {t: t.capitalize() + ("" if t.endswith("s") else "s") for t in types}
    tokens = dict(tokens, TYPE_LIST=", ".join("`%s`" % t for t in types), FIRST_TYPE=types[0],
                  FAMILY_ROWS="\n".join("| %s | (what these are) | (how the key is spelled) |"
                                        % folders[t] for t in types))
    seeder.copy_tree(os.path.join(ASSETS, "content"), dest, tokens)
    for folder in list(folders.values()) + ["Sources"]:
        seeder.write(os.path.join(dest, folder, ".gitkeep"), "")
    seeder.write(os.path.join(dest, "canon.json"), json.dumps(
        {"types": {t: {"folder": folders[t]} for t in types}, "entries": []}, indent=2) + "\n")
    return tokens


def add_plugins(seeder, dest, plugins, tokens):
    for pid in plugins:
        src = os.path.join(ASSETS, "plugins", pid)
        if not os.path.isdir(src):
            print("seed: no bundled plugin %r (have: %s)" % (pid, ", ".join(KNOWN_PLUGINS)))
            continue
        seeder.copy_tree(src, os.path.join(dest, ".obsidian", "plugins", pid), tokens)
    path = os.path.join(dest, ".obsidian", "community-plugins.json")
    have = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            have = json.load(fh)
    want = have + [p for p in plugins if p not in have]
    if want != have and not seeder.dry:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(want, fh, indent=2)
            fh.write("\n")
    # A vault that ships its own plugins has to track them.
    ignore = os.path.join(dest, ".gitignore")
    if os.path.exists(ignore) and not seeder.dry:
        with open(ignore, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        kept = [ln for ln in lines if ln.strip() != ".obsidian/plugins/"]
        if kept != lines:
            with open(ignore, "w", encoding="utf-8") as fh:
                fh.write("\n".join(kept))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archetype", choices=["brain", "roadmap", "content"])
    ap.add_argument("--dest", help="vault directory (created if missing)")
    ap.add_argument("--name", help="the vault's display name")
    ap.add_argument("--project", help="the product or project the vault serves (default: the repo folder name)")
    ap.add_argument("--owner", help="whose writing the vault holds (default: git user.name's first word)")
    ap.add_argument("--kinds", default="", help="brain: kind folders; content: entry types. Comma separated.")
    ap.add_argument("--plugins", default="", help="bundled home-made plugins to install: " + ", ".join(KNOWN_PLUGINS))
    ap.add_argument("--accent", help="accent colour as #rrggbb")
    ap.add_argument("--working-memory", action="store_true", help="brain: add Now.md")
    ap.add_argument("--stop-hook", action="store_true", help="roadmap: wire the write-back Stop hook")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-update", action="store_true")
    args = ap.parse_args()

    if args.self_update:
        return self_update()
    if not (args.archetype and args.dest and args.name):
        ap.error("--archetype, --dest and --name are required")

    dest = os.path.abspath(args.dest)
    repo_root = git_root(dest) or dest
    vault_path = os.path.relpath(dest, repo_root)
    prefix = "" if vault_path == "." else vault_path.replace(os.sep, "/") + "/"
    owner = args.owner
    if not owner:
        try:
            owner = subprocess.run(["git", "config", "user.name"], capture_output=True,
                                   text=True).stdout.split()[0]
        except (OSError, IndexError):
            owner = "the author"
    tokens = dict(
        VAULT_NAME=args.name, PROJECT=args.project or os.path.basename(repo_root),
        VAULT_PATH="the repo root" if not prefix else "`%s`" % prefix, VAULT_PREFIX=prefix,
        DATE=datetime.date.today().isoformat(), OWNER=owner, HOME_NOTE="Home",
    )
    kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
    plugins = [p.strip() for p in args.plugins.split(",") if p.strip()]
    seeder = Seeder(args.dry_run)

    if args.archetype == "brain":
        kinds = kinds or ["Knowledge", "Playbooks", "People"]
        seed_brain(seeder, dest, tokens, kinds, args.working_memory)
        merge_settings(seeder, repo_root, allow=["Bash(python3 %sbin/lint.py:*)" % prefix])
        check = "python3 %sbin/lint.py" % prefix
    elif args.archetype == "roadmap":
        seeder.copy_tree(os.path.join(ASSETS, "roadmap"), dest, tokens)
        for folder in ("Ideas", "Builds"):
            seeder.write(os.path.join(dest, folder, ".gitkeep"), "")
        if args.stop_hook:
            merge_settings(seeder, repo_root, stop_cmd=(
                'f="${CLAUDE_PROJECT_DIR:-.}/%sbin/session_check.py"; '
                '[ -f "$f" ] || exit 0; exec python3 "$f"' % prefix))
        check = "python3 %sbin/reindex.py --check" % prefix
    else:
        seed_content(seeder, dest, tokens, kinds)
        check = "python3 %sbin/vault.py check" % prefix

    if plugins:
        add_plugins(seeder, dest, plugins, tokens)
    if args.accent:
        css = os.path.join(dest, ".obsidian", "snippets", "vault.css")
        if not seeder.dry and os.path.exists(css):
            with open(css, "a", encoding="utf-8") as fh:
                fh.write(accent_css(args.accent))

    verb = "would create" if args.dry_run else "created"
    for path in seeder.made:
        print("  + %s" % os.path.relpath(path, repo_root))
    for path in seeder.kept:
        print("  = %s (exists, kept)" % os.path.relpath(path, repo_root))
    print("seed: %s %d files, kept %d, vault at %s" % (verb, len(seeder.made), len(seeder.kept), dest))
    if not args.dry_run:
        print("seed: check it with: %s" % check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
