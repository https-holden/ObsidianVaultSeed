#!/usr/bin/env python3
"""Regenerate every derived section in this planning vault.

The vault has exactly one authored source for the idea/build relation: the
`ideas:` list in a build note's frontmatter. Everything else that shows that
relation is derived from it by this script, so the two directions can never
disagree. Run it after editing any note, and commit the result.

    python3 bin/reindex.py          regenerate, print a summary
    python3 bin/reindex.py --check  fail if anything is out of date

Run it by whatever path reaches it; the vault is found from this file's own
location, never from the working directory.

--check writes nothing and exits 1 on drift, which is what CI would call.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.relpath(os.path.abspath(__file__))

# The vocabularies. Changing one here is a schema change: say so in the
# vault's CLAUDE.md in the same commit.

STATUSES_IDEA = ["Open", "Done", "Culled"]
STATUSES_BUILD = ["Planned", "In progress", "In review", "Shipped", "Abandoned"]
KINDS_IDEA = ["NOW", "SPEC", "POLISH", "DREAM"]

KIND_BLURB = {
    "NOW": "broken or missing in a way a user meets",
    "SPEC": "wanted, but a real decision has to be made first",
    "POLISH": "correct already, just not good yet",
    "DREAM": "someday, unscoped, keep it visible",
}


# ---------------------------------------------------------------- parsing


def parse(path):
    """Return (frontmatter dict, body string). Values are str or list[str]."""
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---\n", 3)
    raw, body = text[4:end], text[end + 5 :]
    fm, key = {}, None
    for line in raw.split("\n"):
        if not line.strip():
            continue
        if line.startswith("  - "):
            if key:
                fm.setdefault(key, []).append(line[4:].strip().strip('"'))
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip().strip('"')
        fm[key] = val if val else []
    return fm, body


def note_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def load(kind):
    out = {}
    d = os.path.join(VAULT, kind)
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(d, fn)
        fm, body = parse(p)
        out[note_name(p)] = dict(path=p, fm=fm, body=body)
    return out


LINK = re.compile(r"\[\[([^\]|]+)")


def linked(fm):
    return [LINK.match(x).group(1).strip() for x in fm.get("ideas", []) if LINK.match(x)]


# ---------------------------------------------------------------- writing


def norm(block):
    """Compare blocks ignoring cosmetic whitespace.

    Obsidian rewrites Markdown tables on save, padding every cell to the
    column width. That is a better-looking file and it is not a content
    change, so without this the script and the editor would overwrite each
    other forever and --check would report drift on any file you had merely
    opened. Obsidian's formatting wins; we only rewrite on real change.
    """
    out = []
    for line in block.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("|"):
            cells = [re.sub(r"\s+", " ", c).strip() for c in line.split("|")]
            cells = ["-" if c and set(c) == {"-"} else c for c in cells]
            out.append("|".join(cells))
        else:
            out.append(re.sub(r"\s+", " ", line))
    return "\n".join(out)


def splice(path, marker, lines):
    """Replace the content between <!-- reindex:MARKER --> and its closer."""
    text = open(path, encoding="utf-8").read()
    open_m, close_m = "<!-- reindex:%s -->" % marker, "<!-- /reindex:%s -->" % marker
    if open_m not in text:
        return False, text
    a = text.index(open_m) + len(open_m)
    b = text.index(close_m)
    # Blank lines on both sides are load-bearing: without them Obsidian reads
    # the following table or heading as part of the HTML comment block and
    # renders it as raw pipe characters.
    block = "\n\n" + "\n".join(lines) + "\n\n" if lines else "\n\n"
    if norm(text[a:b]) == norm(block):
        return False, text
    new = text[:a] + block + text[b:]
    return True, new


def link(name):
    return "[[%s]]" % name


# ---------------------------------------------------------------- tables


def table(rows, headers):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c == [] else str(c) for c in r) + " |")
    return out


def build_sort(item):
    name, b = item
    try:
        return (0, int(b["fm"].get("order", 999)), name)
    except (TypeError, ValueError):
        return (1, 999, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    ideas, builds = load("Ideas"), load("Builds")
    problems, changed = [], []

    for n, i in ideas.items():
        s, k = i["fm"].get("status"), i["fm"].get("kind")
        if s not in STATUSES_IDEA:
            problems.append("Ideas/%s: status %r is not one of %s" % (n, s, STATUSES_IDEA))
        if k not in KINDS_IDEA:
            problems.append("Ideas/%s: kind %r is not one of %s" % (n, k, KINDS_IDEA))
    for n, b in builds.items():
        if b["fm"].get("status") not in STATUSES_BUILD:
            problems.append("Builds/%s: status %r is not one of %s"
                            % (n, b["fm"].get("status"), STATUSES_BUILD))

    # relation: build -> ideas is authored, idea -> builds is derived
    reverse = defaultdict(list)
    for n, b in sorted(builds.items(), key=build_sort):
        for target in linked(b["fm"]):
            if target not in ideas:
                problems.append("Builds/%s: ideas: links to missing note %r" % (n, target))
                continue
            reverse[target].append(n)

    def write(path, marker, lines):
        dirty, new = splice(path, marker, lines)
        if dirty:
            changed.append(os.path.relpath(path, VAULT))
            if not args.check:
                open(path, "w", encoding="utf-8").write(new)

    for n, b in builds.items():
        names = linked(b["fm"])
        lines = ["## Ideas in scope", ""] + ["- %s" % link(x) for x in names] if names else []
        write(b["path"], "ideas", lines)

    for n, i in ideas.items():
        names = reverse.get(n, [])
        lines = ["## Builds", ""] + ["- %s" % link(x) for x in names] if names else []
        write(i["path"], "builds", lines)

    # ---- Home.md
    scoped = set(reverse)
    open_ideas = {n: i for n, i in ideas.items() if i["fm"].get("status") == "Open"}

    planned = [(n, b) for n, b in sorted(builds.items(), key=build_sort)
               if b["fm"].get("status") in ("Planned", "In progress", "In review")]
    rows = [(link(n), b["fm"].get("status", ""), b["fm"].get("kind", ""), b["fm"].get("repo_area", ""),
             b["fm"].get("model", ""), len(linked(b["fm"]))) for n, b in planned]
    write(os.path.join(VAULT, "Home.md"), "queue",
          table(rows, ["Build", "Status", "Kind", "Area", "Model", "Ideas"]) if rows
          else ["Nothing queued."])

    by_kind = []
    for k in KINDS_IDEA:
        got = sorted(n for n, i in open_ideas.items() if i["fm"].get("kind") == k)
        by_kind.append("### %s" % k)
        by_kind.append("")
        by_kind.append("*%s*" % KIND_BLURB[k])
        by_kind.append("")
        if got:
            by_kind += table([(link(n), open_ideas[n]["fm"].get("area", ""),
                               ", ".join(link(x) for x in reverse[n]) if n in scoped else "unscoped")
                              for n in got], ["Idea", "Area", "Scoped into"])
        else:
            by_kind.append("None open.")
        by_kind.append("")
    write(os.path.join(VAULT, "Home.md"), "open", by_kind)

    counts = Counter(i["fm"].get("status") for i in ideas.values())
    bcounts = Counter(b["fm"].get("status") for b in builds.values())
    unscoped = sorted(n for n in open_ideas if n not in scoped)
    # A list, not a table: a two-column table with no headers renders an empty
    # header row, and there is nothing to put in it.
    write(os.path.join(VAULT, "Home.md"), "counts", [
        "- **Ideas** %d open, %d done, %d culled"
        % (counts["Open"], counts["Done"], counts["Culled"]),
        "- **Builds** %d planned, %d shipped" % (bcounts["Planned"], bcounts["Shipped"]),
        "- **Open and unscoped** %d of %d" % (len(unscoped), len(open_ideas)),
    ])

    # ---- Builds.md ledger
    rows = [(link(n), b["fm"].get("status", ""), b["fm"].get("kind", ""), b["fm"].get("repo_area", ""),
             b["fm"].get("roadmap", ""), len(linked(b["fm"])))
            for n, b in sorted(builds.items(), key=build_sort)]
    write(os.path.join(VAULT, "Builds.md"), "ledger",
          table(rows, ["Build", "Status", "Kind", "Area", "Roadmap", "Ideas"]) if rows
          else ["No builds yet."])

    # ---- Ideas.md, everything, grouped by area
    lines = []
    for area in sorted({i["fm"].get("area", "") for i in ideas.values()}):
        got = sorted(n for n, i in ideas.items() if i["fm"].get("area") == area)
        lines += ["### %s" % (area or "Unfiled"), ""]
        lines += table([(link(n), ideas[n]["fm"].get("status", ""), ideas[n]["fm"].get("kind", ""),
                         ", ".join(link(x) for x in reverse[n]) if n in reverse else "")
                        for n in got], ["Idea", "Status", "Kind", "Builds"])
        lines += [""]
    write(os.path.join(VAULT, "Ideas.md"), "all", lines or ["No ideas yet."])

    for p in problems:
        print("PROBLEM  %s" % p, file=sys.stderr)
    if args.check:
        for c in sorted(set(changed)):
            print("STALE    %s" % c, file=sys.stderr)
        if changed or problems:
            print("\n%d stale, %d problems. Run: python3 %s"
                  % (len(set(changed)), len(problems), SELF), file=sys.stderr)
            return 1
        print("reindex: up to date (%d ideas, %d builds)" % (len(ideas), len(builds)))
        return 0

    print("reindex: %d ideas, %d builds, %d files rewritten"
          % (len(ideas), len(builds), len(set(changed))))
    print("         %d open ideas, %d of them unscoped" % (len(open_ideas), len(unscoped)))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
