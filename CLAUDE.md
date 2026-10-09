# ObsidianVaultSeed

This repo makes Obsidian second brains. Two kinds of session open here:

- **Someone setting up their own vault** (often a beginner sent this link by a friend). Follow
  `AGENTS.md`: one step at a time, plain words, never ask for a password or token. Their vault
  goes in its own folder (by default `~/Documents/Obsidian/<name>-brain`), never inside this
  repo, and `setup/mac.sh --name <Name> --preset personal|work` makes it without prompts.
  Once it exists, that vault's own `CLAUDE.md` is the contract, not this file.
- **Changing the seed itself.** The rules below.

## Changing the seed

- `skills/vault-seed/assets/` is what a seeded vault contains, with `@@TOKENS@@` filled by
  `skills/vault-seed/scripts/seed.py`. `assets/optional/` holds the pieces a flag adds and the
  `sections/` spliced into a vault's `CLAUDE.md` and `Readme.md`.
- Everything a vault runs is Python standard library and must work on Python 3.9 (what Apple's
  Command Line Tools ship). `pypdf` is the one optional extra, and only for PDF text.
- `starter-vault/` is generated: never edit it by hand. After changing assets or `seed.py`,
  run `python3 tools/build_starter.py`.
- Run `python3 tools/check.py` before committing (also with `/usr/bin/python3` when touching
  scripts). It needs no network and no AI.
- Nothing personal or employer-specific goes in this repo: no real names, clients, companies,
  hostnames or account ids in assets, guides or examples. "Sam" and "Acme" are the examples.
- No en or em dashes in any file (the check scans the docs).
- The headless librarian's permission rules: file writes of every kind are matched by
  `Edit(...)` rules (there is no `Write(...)` rule), and `--restricted` is added only when the
  installed `claude` supports it.
