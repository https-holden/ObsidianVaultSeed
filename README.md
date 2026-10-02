# Obsidian Vault Seed

A Claude Code skill that gives a project an Obsidian vault. You type `/vault-seed`, answer a
few questions, and get a vault that you can browse in Obsidian and that Claude Code sessions
can maintain without making a mess of it.

It is the common ground of four vaults that were built by hand and ended up alike: a product
roadmap, a lexicon that feeds prompts, a work second brain and a personal one. The seed is
what they share, with the reasons written down.

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
| Lives in | `roadmap/` in the repo | Usually the repo root | `lexicon/` (or any name) in the repo |
| Notes | `Ideas/` (raw capture) and `Builds/` (one per session, the prompt inside) | A folder per kind you choose: Knowledge, Playbooks, People, Projects, Meetings, Daily, Clippings, or your own | One note per entry, in a folder per type |
| Organised by | `kind` (NOW, SPEC, POLISH, DREAM), `status`, `area` | `categories` links to topic pages (the kepano method) | `type`, `key`, `status` |
| The gate | An idea is `Open`, `Done` or `Culled`; a build is `Planned` to `Shipped` | `draft`, `verified`, `stale` | `empty`, `draft`, `done`. Only `done` ships |
| Its check | `bin/reindex.py --check` | `bin/lint.py` | `bin/vault.py check` |
| Extra | A Stop hook that will not let a session end with a build it worked but did not write up | `Decisions.md`, optional `Now.md` working memory, a bundled `kepano-method` skill for audits | `canon.json` plus a scaffolder that writes a stub for every key your code expects |

A project can have more than one. They are seeded as separate vaults in separate folders.

Every vault also gets: a `CLAUDE.md` contract, a `Home.md` hub, one template and one Base per
kind, tracked `.obsidian/` config, a `.gitignore` for Obsidian's per-machine state, and a CSS
snippet.

## Without Claude

The scaffolder is one standard-library Python script and works on its own:

```bash
python3 skills/vault-seed/scripts/seed.py --archetype roadmap --dest roadmap --name "Acme roadmap" --stop-hook
```

```bash
python3 skills/vault-seed/scripts/seed.py --archetype brain --dest . --name "Acme Brain" --kinds Knowledge,Playbooks,People,Daily --working-memory
```

```bash
python3 skills/vault-seed/scripts/seed.py --archetype content --dest lexicon --name "The lexicon" --kinds term,card
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
skills/vault-seed/
  SKILL.md              what Claude follows when you type /vault-seed
  scripts/seed.py       the scaffolder
  references/           the interview, the conventions, the plugins
  assets/
    roadmap/            the planning vault
    brain/              the second brain (plus a kepano-method project skill)
    content/            the content vault
    plugins/            the four home-made plugins
    optional/           pieces a flag adds (Now.md)
  evals/                test prompts for the skill
install.sh              links the skill into ~/.claude/skills
.claude-plugin/         manifests for installing as a Claude Code plugin
```

To change what a seeded vault contains, edit the files under `assets/`. They are the vault,
with `@@TOKENS@@` where a name goes.

## Credits

The method is Steph Ango's ([How I use Obsidian](https://stephango.com/vault)). The general
Bases (`Related`, `Backlinks`, `Attachments`, `Everything`, `Templates`) come from his
[vault template](https://github.com/kepano/kepano-obsidian), and the syntax skills every vault
leans on are his [obsidian-skills](https://github.com/kepano/obsidian-skills), both MIT.
