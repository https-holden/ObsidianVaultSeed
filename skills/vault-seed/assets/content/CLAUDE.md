# @@VAULT_NAME@@

This directory is an Obsidian vault holding @@OWNER@@'s own definitions of the vocabulary
@@PROJECT@@ uses. It is content, not planning: code reads it. Read `Home.md` for the shape and
the writing workflow. Seeded @@DATE@@ from the ObsidianVaultSeed content archetype.

Plain Markdown on core Obsidian, no community plugins. `cat`, `grep` and `git diff` are how a
session reads it.

## The rules

- **One note per entry.** Frontmatter is the table, body is the prose. The properties code
  depends on are `type`, `key`, `status` and `short`. Every other property is @@OWNER@@'s and
  may come and go.
- **Types in use:** @@TYPE_LIST@@, each with its folder, listed in `canon.json`.
- **The keys are the code's spellings**, so an entry can be found from the product without
  translation. Canonical entries are authored in `canon.json` (`{"type", "key", "name"}`);
  adding one there and running `python3 @@VAULT_PREFIX@@bin/vault.py scaffold` writes a stub
  for what is missing and never touches a note that exists. A note needs no canon entry; a
  unique `key` is enough.
- **`status` is the gate.** `empty`, `draft`, `done`. Only `done` ships: the `short` property,
  or `## Distilled` when `short` is blank. `bin/vault.py` (`prompt_text`) is the one rule; any
  reader in the product must follow it.
- **The writing is @@OWNER@@'s.** A session may distill a Talk through into a Distilled
  section and propose a `short`, clearly as a draft to be rewritten. A session never writes a
  definition from its own knowledge and never flips a note to `done`.
- **`aliases` carries the key** wherever the key does not already read as the name, so
  `[[the-key]]` resolves in Obsidian.
- **No em or en dashes**, anywhere in a note. The check fails on one.
- **`Sources/` holds raw material, not entries.** A transcript or clipping lives there with
  `type: source`; the loader skips the folder, so it is never validated and never ships.
  Entries link into it by heading from their Sources section.
- **Body sections are free text under `## Headings`.** Talk through, Distilled and Sources
  are a convention, not a schema.

## Obsidian syntax

The reference is the `kepano/obsidian-skills` plugin. **Load the skills before writing here:**
`obsidian:obsidian-markdown` before creating or editing any note, `obsidian:obsidian-bases`
before touching `Entries.base`. Wikilinks only, no tags (`type` and `status` are the axes),
callouts fine.

**Linking convention.** Every entry links the entries it mentions. Inline links live in Talk
through and Sources only, first mention per note, written as `[[Note|as it was said]]` so the
original wording stands. `short` and Distilled carry NO links, ever: they are what ships.

## Checking it

```
python3 @@VAULT_PREFIX@@bin/vault.py check             # exits 1 on any problem
python3 @@VAULT_PREFIX@@bin/vault.py scaffold --check  # lists missing stubs, writes nothing
```

`check` verifies: every canonical key has a note, every note has a known type and status, no
key repeats, no banned dash, and a `done` note actually has text to ship. Wire it into the
project's test run once code depends on the vault.

## What reads it

Nothing yet. When code does, record here which surface reads which type, and remember that
flipping a note to `done` then becomes a live product change. If the product is deployed from
an image, the image has to include this directory.
