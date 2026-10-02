#!/usr/bin/env python3
"""Stop-hook gate: did this session write its build back into the vault?

The vault's CLAUDE.md asks a session that works a build to do four things before
it ends, and says of the fourth (discoveries become Ideas notes) that it "is
the one that gets skipped." An instruction an agent has to remember at the end
of a long session, usually after context has been compacted, is the weakest
possible enforcement. This script converts it into something checkable.

It is wired as a Stop hook in .claude/settings.json. Claude Code hands a Stop
hook a JSON object on stdin carrying `transcript_path` and `stop_hook_active`,
and reads exit code 2 as "do not stop, here is why" with stderr fed back to
the model. Every other exit code lets the session end.

The transcript is how "did this session work a build?" gets answered without
guessing: if the session read or wrote Builds/<name>.md, that path is
in the transcript. Only builds the session actually touched are checked, so a
session that never went near the vault is never blocked.

    python3 bin/session_check.py            read hook JSON on stdin
    python3 bin/session_check.py --self-test

Deliberately quiet by design: no findings means no output and exit 0.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reindex import VAULT, load, note_name  # noqa: E402

REL = os.path.relpath(VAULT)

BUILDS_DIR = os.path.join(VAULT, "Builds")

# A build in one of these states is finished as far as this check is
# concerned. "Planned" or "In progress" after a session that worked it is
# the thing worth catching.
CLOSED_STATUSES = {"Shipped", "Abandoned"}

# Referenced in the transcript as a path, a wikilink, or a bare filename.
# The transcript is JSONL with escaped strings, so match the note name
# rather than trying to parse it.
def builds_mentioned(transcript_text, build_names):
    hit = []
    for name in build_names:
        if name in transcript_text:
            hit.append(name)
    return hit


def section_body(body, heading):
    """Text under `## <heading>`, up to the next `## `. '' when absent."""
    match = re.search(
        r"^##\s+" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def check_build(name, note):
    """Return a list of problem strings for one build note."""
    problems = []
    status = note["fm"].get("status", "")
    body = note["body"]

    if status not in CLOSED_STATUSES:
        problems.append(
            f'status is "{status}", not Shipped or Abandoned'
        )
    if not section_body(body, "Outcome"):
        problems.append("no `## Outcome` section, or it is empty")
    if not section_body(body, "Commits"):
        problems.append("no `## Commits` section, or it is empty")
    return problems


def reindex_drift():
    """True when the generated tables are stale. False if it cannot tell."""
    try:
        done = subprocess.run(
            [sys.executable, os.path.join(VAULT, "bin", "reindex.py"), "--check"],
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode != 0


def report(worked):
    """Build the blocking message, or '' when everything is written back."""
    lines = []
    for name, problems in worked:
        if problems:
            lines.append(f"  {name}:")
            lines.extend(f"    - {p}" for p in problems)

    drift = reindex_drift()
    if not lines and not drift:
        return ""

    out = [
        "This session worked a build in the planning vault and has not finished "
        "writing it back. %s/CLAUDE.md, 'Working a build':" % REL,
        "",
    ]
    if lines:
        out.append("Incomplete build notes:")
        out.extend(lines)
        out.append("")
        out.append(
            "Each needs: `## Outcome` (one line per scoped item), `## Commits` "
            "(hashes, and whether they were pushed), anything deliberately not "
            "done and why, and DISCOVERIES written as their own files in "
            "Ideas/ and added to the build's `ideas:` list. Then set "
            "the build's status and flip every idea it closed to Done with a "
            "`## Resolved in` section."
        )
    if drift:
        out.append(
            "The vault's generated tables are stale. Run "
            "`python3 %s/bin/reindex.py` and commit what it changes." % REL
        )
    out.append("")
    out.append(
        "If this session did not actually work a build, say so and stop again; "
        "this check reads the transcript and cannot tell reading from working."
    )
    return "\n".join(out)


def main(argv):
    if "--self-test" in argv:
        return self_test()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # A hook that cannot read its input must not block a session.
        return 0

    # Set on the stop that this hook itself caused. Blocking again would
    # loop the session forever.
    if payload.get("stop_hook_active"):
        return 0

    path = payload.get("transcript_path") or ""
    if not path or not os.path.exists(path):
        return 0
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            transcript = handle.read()
    except OSError:
        return 0

    builds = load("Builds")
    worked = [
        (name, check_build(name, builds[name]))
        for name in builds_mentioned(transcript, builds)
    ]
    if not worked:
        return 0

    message = report(worked)
    if not message:
        return 0
    print(message, file=sys.stderr)
    return 2


def self_test():
    """Check the parts that are easy to get wrong, against the real vault."""
    failures = []

    # An empty vault is a valid vault: a freshly seeded one has no builds.
    builds = load("Builds")

    # section_body finds a present section and rejects an absent one.
    sample = "## Outcome\n\nIt shipped.\n\n## Commits\n\n- abc123\n"
    if section_body(sample, "Outcome") != "It shipped.":
        failures.append("section_body did not read `## Outcome`")
    if section_body(sample, "Discoveries") != "":
        failures.append("section_body invented a missing section")
    if section_body("## Outcome\n\n\n## Commits\n", "Outcome") != "":
        failures.append("section_body treated an empty section as present")

    # check_build against synthetic notes, NOT against whichever real
    # builds happen to be unfinished today: a self-test whose fixtures are
    # live data breaks the afternoon the fixture ships, which is the worst
    # kind of false alarm.
    written_back = dict(
        fm={"status": "Shipped"},
        body="## Outcome\n\nIt shipped.\n\n## Commits\n\n- abc123, not pushed.\n",
    )
    if check_build("fixture", written_back):
        failures.append("a fully written-back build was flagged")

    for label, note in (
        ("still Planned", dict(written_back, fm={"status": "Planned"})),
        ("no Outcome", dict(written_back, body="## Commits\n\n- abc123\n")),
        ("no Commits", dict(written_back, body="## Outcome\n\nIt shipped.\n")),
        ("empty Outcome", dict(written_back, body="## Outcome\n\n## Commits\n\n- a\n")),
    ):
        if not check_build("fixture", note):
            failures.append(f"a build with {label} was not flagged")

    # Every real build still parses, which is what would break if the
    # frontmatter format drifted.
    for name, note in builds.items():
        if not note["fm"].get("status"):
            failures.append(f"{name} has no status in frontmatter")

    # Mention detection is substring-based; make sure it does not fire on
    # a session that mentioned nothing.
    if builds_mentioned("nothing to see here", builds):
        failures.append("builds_mentioned matched an unrelated transcript")
    names = list(builds) or ["B-00 Fixture"]
    if names[0] not in builds_mentioned(f"read Builds/{names[0]}.md", names):
        failures.append("builds_mentioned missed a real path reference")

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    if failures:
        return 1
    print("session_check self-test: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
