# Obsidian Vault Seed

> **New to all this?** Read [START-HERE.md](START-HERE.md), or point your AI (Claude,
> ChatGPT, anything) at this repo and say "help me set this up". The AI's instructions are in
> [AGENTS.md](AGENTS.md). No GitHub account, Obsidian experience or terminal skills needed.

A second brain you can set up in half an hour: an Obsidian vault with a place for each kind of
note, rules an AI follows to keep it tidy, tools that bring in web pages, PDFs, documents,
emails and old notes and file them for you, and a morning and evening habit that keeps it
current. It works with Claude (best, because it can open your files) or any chat AI.

| You want | Go to |
|---|---|
| To set one up, step by step | [START-HERE.md](START-HERE.md) |
| A vault to open right now, no terminal | [`starter-vault/`](starter-vault) (download the ZIP, copy that folder) |
| To learn Obsidian | [guides/obsidian-basics.md](guides/obsidian-basics.md) |
| To bring your stuff in | [guides/bringing-things-in.md](guides/bringing-things-in.md) |
| The daily habit | [guides/daily-loop.md](guides/daily-loop.md) |
| ChatGPT prompts | [guides/prompts-for-any-ai.md](guides/prompts-for-any-ai.md) |
| A backup | [guides/backup-with-github.md](guides/backup-with-github.md) |
| To share one with a team | [guides/sharing-a-vault.md](guides/sharing-a-vault.md) |

The rest of this page is for Claude Code users and for changing the seed itself.

## The Claude Code skill

A Claude Code skill that gives a project an Obsidian vault. You type `/vault-seed`, answer a
few questions, and get a vault that you can browse in Obsidian and that Claude Code sessions
can maintain without making a mess of it.

It is the common ground of four vaults that were built by hand and ended up alike: a product
roadmap, a lexicon that feeds prompts, a work second brain and a personal one. The seed is
what they share, with the reasons written down. The two second brains are also available as
presets, `--preset personal` and `--preset work`, which is what the setup scripts use.

## Install

You need [Claude Code](https://claude.com/claude-code), `git` and Python 3. Obsidian is where
you read the vault; any recent version with Bases (1.9 or later).

```bash
git clone https://github.com/https-holden/ObsidianVaultSeed ~/.claude/ObsidianVaultSeed
```

```bash
~/.claude/ObsidianVaultSeed/install.sh
```

That links the skill into `~/.claude/skills/`. To update later, `git pull` in the clone (the
skill also pulls for itself each time it runs).

Or, as a Claude Code plugin, inside a session:

```
/plugin marketplace add https-holden/ObsidianVaultSeed
/plugin install vault-seed@obsidian-vault-seed
```

**Also install kepano's Obsidian skills.** Every seeded vault tells Claude to load them
before touching a note or a `.base` file, because they carry the syntax:

```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

## Use

Open Claude Code in the project and type:

```
/vault-seed
```

or just say what you want: "give this project a roadmap vault", "seed a second brain here".

The skill then:

1. **Looks at the project** so it does not ask what it can read.
2. **Asks up to seven short questions**: what the vault is for, where it lives, what it is
   called, what kinds of notes it holds, who else reads it, what should be automated, and
   whether you want a colour or plugins.
3. **Shows the plan** and, if the folder is not empty, the exact file list.
4. **Scaffolds** from this repo. It never overwrites an existing file.
5. **Tailors and verifies**: fills in the vault's `CLAUDE.md` from your answers, points the
   project's own `CLAUDE.md` at it, runs the vault's check, and tells you how to open it.

It writes structure, never content. You will not find invented example notes in your vault.

## The three vaults it can make

| | `roadmap` | `brain` | `content` |
|---|---|---|---|
| For | Planning a code project that Claude Code sessions build | A second brain: what is known, how things are done, who is who | Definitions or copy you write and your code reads |
| Lives in | `<project>-roadmap/` in the repo | Usually the repo root | `<project>-lexicon/` (or any name) in the repo |
| Notes | `Ideas/` (raw capture) and `Builds/` (one per session, the prompt inside) | A folder per kind you choose: Knowledge, Playbooks, People, Projects, Meetings, Daily, Clippings, or your own | One note per entry, in a folder per type |
| Organised by | `kind` (NOW, SPEC, POLISH, DREAM), `status`, `area` | `categories` links to topic pages (the kepano method) | `type`, `key`, `status` |
| The gate | An idea is `Open`, `Done` or `Culled`; a build is `Planned` to `Shipped` | `draft`, `verified`, `stale` | `empty`, `draft`, `done`. Only `done` ships |
| Its check | `bin/reindex.py --check` | `bin/lint.py` | `bin/vault.py check` |
| Extra | A Stop hook that will not let a session end with a build it worked but did not write up | `Decisions.md`, optional `Now.md` working memory and `Me.md`, a bundled `kepano-method` skill for audits; with `Clippings`, the ingest tools and librarian; with `Now.md` and `Daily`, the `start-of-day` and `end-of-day` skills | `canon.json` plus a scaffolder that writes a stub for every key your code expects |

A project can have more than one. They are seeded as separate vaults in separate folders.

Every vault also gets: a `CLAUDE.md` contract, a `Home.md` hub, one template and one Base per
kind, tracked `.obsidian/` config, a `.gitignore` for Obsidian's per-machine state, and a CSS
snippet.

## Without Claude

The scaffolder is one standard-library Python script and works on its own:

```bash
python3 skills/vault-seed/scripts/seed.py --archetype roadmap --dest acme-roadmap --name "Acme roadmap" --stop-hook
```

```bash
python3 skills/vault-seed/scripts/seed.py --archetype brain --dest . --name "Acme Brain" --kinds Knowledge,Playbooks,People,Daily --working-memory
```

```bash
python3 skills/vault-seed/scripts/seed.py --archetype content --dest acme-lexicon --name "Acme lexicon" --kinds term,card
```

```bash
python3 skills/vault-seed/scripts/seed.py --preset personal --dest ~/Documents/Obsidian/sam-brain --name "Sam's Brain" --owner Sam
```

Add `--dry-run` to see the file list first. `--help` lists every flag.

## The rules every seeded vault follows

The short version. The reasons are in
[`skills/vault-seed/references/conventions.md`](skills/vault-seed/references/conventions.md).

- The vault has its own `CLAUDE.md`, and it is the contract.
- Frontmatter is the table, the body is the prose. One thing per file.
- Every kind has a template and a Base. Bases is core Obsidian; no Dataview.
- A deterministic check script, whose schema is read from the templates.
- Anything derived is generated between markers and never hand-edited.
- A `status` gate: a model writes drafts, only the owner promotes.
- Whatever shows in Obsidian is also readable with `cat` and `grep`.
- Wikilinks inside the vault. No em or en dashes. ISO dates.
- Corrections are appended and dated, never edited over.
- Config is tracked, per-machine state is not.

## Optional home-made plugins

Four small plain-JavaScript Obsidian plugins are bundled (no build step): `home-button`,
`manual-modified`, `resting-view`, `sticky-bullets`. Ask for them in the interview or pass
`--plugins`. See
[`skills/vault-seed/references/plugins.md`](skills/vault-seed/references/plugins.md).

## What is in this repo

```
START-HERE.md           for a person setting up their first vault
AGENTS.md               for the AI helping them (Claude, ChatGPT, Codex, anything)
setup/                  mac.sh and windows.ps1: install git, Python, Obsidian; make the vault
starter-vault/          the personal preset, ready to open (rebuilt by tools/build_starter.py)
guides/                 Obsidian basics, bringing things in, the daily loop, backup, sharing,
                        chat prompts, and a Web Clipper template
tools/                  check.py (the test suite) and build_starter.py
skills/vault-seed/
  SKILL.md              what Claude follows when you type /vault-seed
  scripts/seed.py       the scaffolder
  references/           the interview, the conventions, the plugins
  assets/
    roadmap/            the planning vault
    brain/              the second brain (plus a kepano-method project skill)
    content/            the content vault
    plugins/            the four home-made plugins
    optional/           pieces a flag adds: Now.md, Me.md, the ingest tools and
                        librarian, the daily-loop skills, and the CLAUDE.md sections for them
  evals/                test prompts for the skill
install.sh              links the skill into ~/.claude/skills
.claude-plugin/         manifests for installing as a Claude Code plugin
```

To change what a seeded vault contains, edit the files under `assets/`. They are the vault,
with `@@TOKENS@@` where a name goes. Then run `python3 tools/build_starter.py` to refresh
`starter-vault/`, and `python3 tools/check.py`, which seeds every kind of vault, runs their
checks and puts sample files through the ingest and librarian scripts.

## Credits

The method is Steph Ango's ([How I use Obsidian](https://stephango.com/vault)). The general
Bases (`Related`, `Backlinks`, `Attachments`, `Everything`, `Templates`) come from his
[vault template](https://github.com/kepano/kepano-obsidian), and the syntax skills every vault
leans on are his [obsidian-skills](https://github.com/kepano/obsidian-skills), both MIT.
