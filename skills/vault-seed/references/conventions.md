# What every seeded vault has in common, and why

Distilled from four vaults that were built separately and converged. When tailoring a vault,
or when the user asks why something is the way it is, this is the answer.

## The rules

1. **The vault has its own `CLAUDE.md`.** It is the maintenance contract: the schema, the one
   rule that keeps it consistent, what a session owes the vault. A vault with no contract
   drifts in a week, because every session improvises.
2. **Frontmatter is the table, the body is the prose.** One thing per file. Properties are a
   schema, written down in the contract.
3. **Every kind has a template and a Base.** The template makes the properties exist from the
   first note. The Base is the live table. Bases is core Obsidian: no Dataview, no plugin set
   another machine might lack.
4. **A deterministic check, in Python's standard library.** `reindex.py --check`, `lint.py`,
   `vault.py check`. A session cannot be trusted to remember a style guide at the end of a
   long task; a script can be run. The schema it enforces is read from the templates or the
   contract's vocabulary, never duplicated.
5. **A relation or a derived view is authored in one place.** Everything else that shows it
   is generated between `<!-- name -->` markers and never hand-edited. Generated files are
   never hand-merged: take either side and rerun the script.
6. **A `status` gate.** `Open/Done/Culled`, `draft/verified/stale`, `empty/draft/done`. A
   model writes drafts; only the owner promotes. What is unchecked must be visibly unchecked.
7. **Plain text first.** Anything a person sees in Obsidian a session must be able to see with
   `cat` and `grep`. That is why generated Markdown tables sit beside the Bases.
8. **Load the obsidian skills before the work.** `obsidian:obsidian-markdown` for notes,
   `obsidian:obsidian-bases` for `.base` files, `obsidian:obsidian-cli` for the running app,
   `obsidian:json-canvas`, `obsidian:defuddle` for clippings.
9. **Wikilinks inside the vault, Markdown links for URLs.** `alwaysUpdateLinks` is on, so a
   rename in the app fixes links. A rename outside the app must fix them in the same commit.
10. **No em or en dashes. ISO dates, never relative.** Checked by the script.
11. **Corrections are appended and dated**, never edited over the original.
12. **Tracked config, untracked state.** `.obsidian/` config, snippets and home-made plugins
    are in git so the vault looks the same on every machine; `workspace.json`, caches and the
    trash are not.
13. **Automation never bumps `modified`** and never writes into a person's own text. Imported
    text lives between markers; handwriting goes outside them.
14. **The seed writes structure, a person writes content.** Nothing invented.

## Where the vaults differ, on purpose

| | roadmap | brain | content |
|---|---|---|---|
| Axis for "what is it" | `type` property | the folder | `type` property |
| Axis for "what is it about" | `area` | `categories` links | `keywords` |
| Tags | none | only `categories`, `daily` | none |
| Templates folder | `_templates/` | `Templates/` | `_templates/` |
| Check | `bin/reindex.py --check` | `bin/lint.py` | `bin/vault.py check` |
| Community plugins | none | home-made only, optional | none |

## Root `CLAUDE.md` wording, when the vault is a subdirectory

Adapt, do not paste blind, and use the vault's real folder name. For a roadmap:

> ## Working from the roadmap vault
>
> Planning lives in `acme-roadmap/`, an Obsidian vault tracked in this repo. `Ideas/` is raw
> capture, one file per idea. `Builds/` is units of work handed to a Claude Code session, one
> file per session, the prompt in the note body. Start at `acme-roadmap/Home.md`;
> `acme-roadmap/CLAUDE.md` is the contract and should be read before editing anything there.
>
> When a session starts from a build it says so, and the build's scope is the scope. When it
> ends it writes back: `## Outcome`, `## Commits`, what was not done, and every discovery as
> its own file in `acme-roadmap/Ideas/`. Then `python3 acme-roadmap/bin/reindex.py`, and commit.

For a content vault:

> ## The lexicon vault
>
> `acme-lexicon/` holds <owner>'s own definitions, one note per entry.
> `acme-lexicon/CLAUDE.md` is its contract. Only a `done` entry ships. The writing is
> <owner>'s: a session may draft from their talk-through, never author a definition or flip
> a note to `done`.

## Several sessions, one working tree

If the user runs sessions side by side in one checkout: never switch branches, stage only the
paths this session touched, and let the last session to finish run the vault's script and
commit the generated files.
