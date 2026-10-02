# @@VAULT_NAME@@

This directory is an Obsidian vault and it is the source of truth for planning @@PROJECT@@.
Seeded @@DATE@@ from the ObsidianVaultSeed planning archetype.

Open it in Obsidian with "Open folder as vault". It is also just Markdown, so `cat`, `grep`
and `git diff` work on it, and that is how a Claude Code session should read it.

**No community plugins.** Everything here runs on core Obsidian plus two Python scripts. Bases
is core, does what Dataview did, and does not make the vault unreadable to anyone without the
same plugin set.

## Obsidian syntax, and where it is documented

The syntax reference is the `kepano/obsidian-skills` plugin (`/plugin marketplace add
kepano/obsidian-skills`, then `/plugin install obsidian@obsidian-skills`). **Load the skill
before the work:** `obsidian:obsidian-markdown` before creating or editing a note,
`obsidian:obsidian-bases` before touching a `.base` file, `obsidian:obsidian-cli` only when
something has to happen inside the running app.

- **Wikilinks, never Markdown links, for anything inside the vault.** `app.json` sets
  `useMarkdownLinks: false` and `newLinkFormat: shortest`, so Obsidian tracks renames and the
  script's `[[...]]` matching keeps working. Markdown links are for URLs only.
- **No tags.** `type`, `kind`, `status` and `area` are the axes; a tag would be a second copy of
  one of them that the script cannot validate.
- **Callouts are allowed, sparingly.** `> [!note] Superseded` is the shape for a dated
  correction that must be seen. In `cat` a callout is a blockquote, so nothing is lost.
- **A `.base` view's `sort:` key is valid** even though the skill does not list it. Keep it.
- **Add a frontmatter field, add it to the base view's `order:` list too**, or it will not show
  as a column.

## The two note types

`Ideas/` is raw capture. One note per idea, annoyance, bug or dream. An idea is never worked
from directly. Frontmatter:

| Field | Values |
|---|---|
| `type` | `idea` |
| `status` | `Open`, `Done`, `Culled` |
| `kind` | `NOW`, `SPEC`, `POLISH`, `DREAM` |
| `area` | free text, kept consistent: (fill in: the areas ideas are filed under) |
| `created` | ISO date |

`kind` is the triage axis and it carries real meaning:

- **NOW**: broken or missing in a way a user meets.
- **SPEC**: wanted, but a real decision has to be made before anyone can build it. Write the
  decision down in the note when it is made, then retype it.
- **POLISH**: correct already, just not good yet.
- **DREAM**: someday, unscoped, keep it visible.

`Builds/` is units of work handed to a Claude Code session. One note per session. The prompt
that starts the session lives in the note body under `## Prompt`, and the note names the ideas
it covers. Frontmatter:

| Field | Values |
|---|---|
| `type` | `build` |
| `status` | `Planned`, `In progress`, `In review`, `Shipped`, `Abandoned` |
| `kind` | `Implementation`, `Fix`, `Investigation`, `Docs` |
| `order` | integer, run order across the whole vault |
| `repo_area` | which part of the repo it touches |
| `model` | which model the build is scoped for |
| `roadmap` | the milestone it serves, free text |
| `ideas` | list of wikilinks to Ideas notes, each quoted |

Name a build with a short prefix and a number so it can be said aloud and found by grep
(`@@PREFIX@@-07 Title`). New notes start from `_templates/`.

## The one rule that keeps it consistent

**The relation is authored in exactly one place: the `ideas:` list in a build's frontmatter.**
Every other place the relation appears is generated from it.

An idea note therefore has no `builds:` field. Its `## Builds` section is written by the
script, between `<!-- reindex:builds -->` markers. Same for a build's `## Ideas in scope`
section and every table in `Home.md`, `Builds.md` and `Ideas.md`. Never hand-edit anything
between `reindex:` markers; it is overwritten on the next run.

The markers are hidden in Live Preview by `.obsidian/snippets/vault.css`, which is tracked in
git so the vault looks the same on any machine. It is scoped away from code blocks on purpose:
an unscoped rule would delete comment lines out of the prompts in build notes.

Read the relation as **"appears in"**, not "closed by". A build lists an idea it merely
discovered as well as one it fixes. The idea's own `## Resolved in` section records where it
actually closed, in prose, because "which commit and why" does not fit in a link.

## Two views of the same data, and why both exist

`Build queue.base` and `Idea backlog.base` read the notes' frontmatter live. They are the right
way for a person to browse. The generated Markdown tables are the same information as plain
text, because a `.base` renders only inside Obsidian: without them `grep`, `git diff` and a
session reading with `cat` would see nothing. Neither is authored, so they cannot disagree
about anything except how recently the script ran.

## After any edit, run the script

```
python3 @@VAULT_PREFIX@@bin/reindex.py          # regenerate, then commit the result
python3 @@VAULT_PREFIX@@bin/reindex.py --check  # writes nothing, exits 1 on drift
```

It also validates: unknown `status` or `kind` values, and `ideas:` links that point at a note
that does not exist. Both print as `PROBLEM`. A dangling link is how a build silently loses an
item, so fix it on the spot.

## Working a build

A session that starts from this vault says so, naming the build. That framing is authoritative
about scope: the items listed in the build note are the work, and anything not listed is out
of scope even if it looks related and easy.

When a session ends, update the build note as part of the same work. Four things, and the
fourth is the one that gets skipped:

1. `## Outcome`, one line per scoped item, saying what actually shipped.
2. `## Commits`, hashes and whether they were pushed.
3. Anything deliberately not done, and why.
4. **Discoveries become new notes in `Ideas/`**, one file each, written to make sense to
   someone who was not in the session. Then add them to the build's `ideas:` list. A discovery
   that only exists in a session transcript is lost.

Set the build's `status` to `Shipped` and flip every idea it closed to `Done` with a
`## Resolved in` section naming the commit. Then run the script.

Discoveries are expected, not a sign of a bad session. `Ideas/` is the correct destination for
"I noticed X is fragile" and the correct alternative to fixing X mid-session and blowing the
scope. The code is not the source of truth for sequencing: a session does not reorder or
expand its own scope based on what it finds.

## The Stop hook, and why it exists

`bin/session_check.py` runs as a Stop hook (wired in the repo's `.claude/settings.json` when
the vault was seeded with it). It answers one question: did this session work a build and then
leave without writing it back?

It reads the session transcript for build-note names, so a session that never went near the
vault is never blocked. For each build it did touch, it requires a `status` of `Shipped` or
`Abandoned`, a non-empty `## Outcome`, and a non-empty `## Commits`. It also runs
`reindex.py --check`. Anything missing exits 2, which Claude Code reads as "do not stop".

It exists because the write-back is the one instruction that has to be remembered at the END
of a long session, usually after context has been compacted. It deliberately never checks
whether discoveries were written (a judgement no script can make), and it fails OPEN wherever
it is unsure. One known wart: it cannot tell reading a build note from working it. If it fires
on a build this session only read, say "did not work it" and stop again.

`python3 @@VAULT_PREFIX@@bin/session_check.py --self-test` checks it. Run that after touching it.

## Concurrent sessions

`Home.md`, `Ideas.md` and `Builds.md` are 100% generated and are the only files two sessions
collide on. Never hand-merge them: take either side and rerun the script. When several
sessions are live, the last one to finish runs the script and commits the tables.

## Corrections

When a later session finds that an earlier build's outcome note was wrong, **append a dated
correction rather than editing the original text.** The wrong claim and the date it was
believed are both evidence.

## House rules

- No em dashes or en dashes, anywhere, including in these notes.
- Convert relative dates to absolute ones when writing a note.
- One idea per file. If a note holds two questions that could be decided independently, it is
  two notes.
