---
name: vault-seed
description: Interview the user about the current project, then scaffold an Obsidian vault for it from the ObsidianVaultSeed repo (a planning vault of ideas and builds, a kepano-method second brain, or a content vault that code reads), with the kepano obsidian skills, Bases, templates, a drift-check script and a CLAUDE.md contract wired in. Use this whenever the user wants to start, seed, scaffold, init or set up an Obsidian vault, a roadmap or planning vault, a second brain, a knowledge base in Markdown, or a lexicon for a project, or says "vault-seed", "seed a vault" or "give this project a vault", even if they do not say Obsidian. Not for editing notes in a vault that already exists (use the obsidian:* skills and that vault's own CLAUDE.md).
---

# Vault seed

Stand up an Obsidian vault that a person can browse and a Claude Code session can maintain,
shaped by a short interview. The shapes were distilled from four working vaults (a product
roadmap, a lexicon that feeds prompts, a work second brain and a personal one); what they have
in common is in `references/conventions.md`, and it is the reason each piece exists.

The work has five steps. Do them in order, and keep the interview short: the user called this
to get a vault, not a questionnaire.

## 1. Refresh the seed and look around

Run `python3 <this skill's dir>/scripts/seed.py --self-update`. It pulls the seed repo the
skill was installed from and never fails; if it cannot reach the repo it says so and the
bundled assets are used as they are.

Then read before asking, because most of the interview can be answered from the project:

- Is this a git repo? What does its `CLAUDE.md` or `README` say the project is?
- Is there already a vault (`find . -name .obsidian -maxdepth 3`) or a planning doc the vault
  would replace? If a vault exists, this is not a seeding job: say so and stop, or seed a
  second vault beside it only if the user wants one.
- Is there a `.claude/settings.json` with hooks already?
- Are the `obsidian:*` skills in your skill list? If not, the vault will still work, but tell
  the user the two commands that install them (`/plugin marketplace add kepano/obsidian-skills`
  then `/plugin install obsidian@obsidian-skills`), because every vault's `CLAUDE.md` tells
  sessions to load them.
- Does the project's `CLAUDE.md` set privacy or account rules (work vs personal, what may be
  committed)? They bind the vault too.

## 2. Interview

Read `references/interview.md` for the questions, their options and how each answer maps to a
flag. Ask with `AskUserQuestion` when it is available, in one round of at most four questions
and a second only if an answer opened something. Skip any question the project already
answered, and say what you inferred so the user can correct it.

The one decision everything hangs on is the archetype:

| Archetype | It is for | Shape |
|---|---|---|
| `roadmap` | Planning a code project with Claude Code sessions | `Ideas/` (raw capture) and `Builds/` (one note per session, prompt inside), generated tables, a Stop hook that enforces the write-back |
| `brain` | A second brain: knowledge, procedures, people, days | kepano method: a folder per kind, `categories` links for topics, a template and a Base per kind, a lint whose schema is the templates |
| `content` | Authored definitions or copy that code reads | one note per entry, a `status` gate where only `done` ships, canonical keys, a scaffolder and a validator |

A project can want two (a product repo with a `roadmap/` and a `lexicon/`). Seed them as
separate vaults in separate directories: their readers and vocabularies differ, and a Base
with no folder filter would list one vault's notes in the other.

## 3. Confirm the plan in a few lines

Before writing, show: archetype, where the vault goes, its name, the kinds or types, plugins,
whether the Stop hook is wired. Run the scaffolder with `--dry-run` first, every time: it is
free, and it shows what would be created, what already exists and would be kept, and whether
`.claude/settings.json` (which sits outside the vault) would change. One confirmation, then go.

## 4. Scaffold

```
python3 <skill dir>/scripts/seed.py --archetype <a> --dest <dir> --name "<name>" [flags]
```

`seed.py --help` lists the flags. It never overwrites (an existing file is kept and reported),
writes structure and never content, and prints the check command for the vault it made.

## 5. Tailor, verify, hand over

The scaffold is generic on purpose. What makes it this project's vault is the next ten minutes:

- Load `obsidian:obsidian-markdown` before hand-editing notes and `obsidian:obsidian-bases`
  before touching a `.base`. They carry syntax that is easy to get subtly wrong.
- **Fill the placeholders.** Every gap the seed leaves is written `(fill in: ...)`.
  `grep -rn "fill in:" <vault>` lists them; replace each with what the interview said, or
  leave it standing and tell the user when only they can answer it. For a brain that means
  the map and kinds rows of any kind the seed did not know; for a roadmap, the areas; for
  content, the families and what will read the vault.
- **A kept file is a merge to do.** If the seed reported `CLAUDE.md` or a `README` as kept
  (a brain seeded at a repo root that already had one), fold the vault contract from
  `assets/<archetype>/CLAUDE.md` into the existing file by hand; do not replace it.
- **`Decisions.md`** (brain): record the interview's answers as the first entry, dated.
- **The project's root `CLAUDE.md`**: when the vault is a subdirectory, add a short section
  pointing at the vault's `CLAUDE.md` and `Home.md`, naming the check command, and (roadmap)
  stating the session write-back. `references/conventions.md` has the wording to adapt. If
  the project has no root `CLAUDE.md`, create one holding just that section: a build's
  prompt tells its session to read it.
- **Do not author content.** No example ideas, no sample knowledge notes, no definitions. An
  invented note is indistinguishable from a real one a month later. The one exception is
  material the user hands you in this session (an existing TODO file, a planning doc): offer
  to migrate it, one note per item, in their words. For a roadmap, type each idea by what
  stands between it and being built: broken or missing in a way a user meets is `NOW`, a
  decision has to be made first is `SPEC`, works but is not good yet is `POLISH`, someday is
  `DREAM`; say the typing is a first pass. Leave the source file where it is and tell the
  user it can go once they have checked the migration.
- Run the vault's check and show its output. For a roadmap also run
  `bin/session_check.py --self-test`.
- If the `obsidian` CLI is installed and the app is running, offer to open the vault;
  otherwise tell the user to "Open folder as vault" at the path. A vault that ships plugins
  needs Restricted mode turned off once, by hand.
- Do not commit unless the user asks or the project's rules say sessions commit. Report what
  was made, what was kept, and the two or three things only the user can decide next.

## Reference files

- `references/interview.md`: the questions, defaults and the flag each answer sets. Read at step 2.
- `references/conventions.md`: the rules every seeded vault follows and why, plus root
  `CLAUDE.md` wording. Read at step 5, and whenever the user asks why the vault is shaped this way.
- `references/plugins.md`: the four bundled home-made plugins and the rule for writing more.
  Read only if plugins come up.
