#!/usr/bin/env python3
"""Loader, validator and scaffolder for this content vault. Standard library only.

    python3 bin/vault.py check              validate every entry; exit 1 on a problem
    python3 bin/vault.py scaffold           write a stub for each canon entry with no note
    python3 bin/vault.py scaffold --check   list what scaffold would write

Import it for the one rule product code must follow:

    from vault import load, prompt_text
    text = prompt_text(load()["some-key"])     # '' unless the entry is done
"""
from __future__ import annotations

import json
import os
import re
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUSES = ["empty", "draft", "done"]
SKIP_DIRS = {"_templates", "_attachments", "Sources", "bin", ".obsidian", ".git", ".trash"}
SKIP_TYPES = {"index", "source"}
DASHES = ("–", "—")


def canon():
    with open(os.path.join(VAULT, "canon.json"), encoding="utf-8") as fh:
        return json.load(fh)


def parse(path):
    """Return (frontmatter dict, body). Values are str or list[str]. Naive YAML, enough here."""
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n") or "\n---" not in text[3:]:
        return {}, text
    end = text.index("\n---", 3)
    fm, key = {}, None
    for line in text[4:end].split("\n"):
        if line.startswith("  - ") and key:
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(line[4:].strip().strip('"'))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            fm[key] = [] if val == "[]" else val.strip('"')
    return fm, text[end + 4:].lstrip("\n")


def section(body, heading):
    m = re.search(r"^##\s+" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def notes():
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if root == VAULT:
            continue  # root files are hubs and contracts, not entries
        for fn in sorted(files):
            if fn.endswith(".md"):
                path = os.path.join(root, fn)
                fm, body = parse(path)
                if fm.get("type") not in SKIP_TYPES:
                    yield path, fm, body


def load():
    """Every entry keyed by `key`."""
    return {fm.get("key"): dict(path=p, fm=fm, body=b) for p, fm, b in notes() if fm.get("key")}


def prompt_text(entry):
    """The only text that ships: a done entry's short, or its Distilled section."""
    if not entry or entry["fm"].get("status") != "done":
        return ""
    return entry["fm"].get("short") or section(entry["body"], "Distilled")


def missing():
    have = load()
    return [e for e in canon().get("entries", []) if e["key"] not in have]


def check():
    types, seen, problems = canon()["types"], {}, []
    for path, fm, body in notes():
        rel = os.path.relpath(path, VAULT)
        if fm.get("type") not in types:
            problems.append("%s: type %r is not one of %s" % (rel, fm.get("type"), sorted(types)))
        if fm.get("status") not in STATUSES:
            problems.append("%s: status %r is not one of %s" % (rel, fm.get("status"), STATUSES))
        key = fm.get("key")
        if not key:
            problems.append("%s: no key" % rel)
        elif key in seen:
            problems.append("%s: key %r repeats %s" % (rel, key, seen[key]))
        else:
            seen[key] = rel
        if any(d in open(path, encoding="utf-8").read() or d in rel for d in DASHES):
            problems.append("%s: contains an en or em dash" % rel)
        if fm.get("status") == "done" and not prompt_text(dict(fm=fm, body=body)):
            problems.append("%s: done, but has no short and no Distilled text to ship" % rel)
    for entry in missing():
        problems.append("canon: %s %r has no note (run scaffold)" % (entry["type"], entry["key"]))
    for p in problems:
        print("PROBLEM  %s" % p, file=sys.stderr)
    print("vault: %d entries, %d problems" % (len(seen), len(problems)))
    return 1 if problems else 0


def scaffold(check_only):
    types = canon()["types"]
    template = open(os.path.join(VAULT, "_templates", "entry.md"), encoding="utf-8").read()
    todo = missing()
    for entry in todo:
        name = entry.get("name") or entry["key"]
        path = os.path.join(VAULT, types[entry["type"]]["folder"], name + ".md")
        print("%s %s" % ("MISSING" if check_only else "wrote  ", os.path.relpath(path, VAULT)))
        if check_only or os.path.exists(path):
            continue
        text = re.sub(r"^type: .*$", "type: %s" % entry["type"], template, count=1, flags=re.M)
        text = re.sub(r"^key: *$", "key: %s" % entry["key"], text, count=1, flags=re.M)
        text = re.sub(r"^name: *$", "name: %s" % name, text, count=1, flags=re.M)
        if name != entry["key"]:
            text = text.replace("aliases: []", "aliases:\n  - %s" % entry["key"], 1)
        text = text.replace("\n# \n", "\n# %s\n" % name, 1)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(text)
    if not todo:
        print("vault: nothing to scaffold")
    return 1 if (check_only and todo) else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        sys.exit(check())
    if cmd == "scaffold":
        sys.exit(scaffold("--check" in sys.argv))
    print(__doc__)
    sys.exit(2)
