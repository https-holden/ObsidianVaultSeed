# The interview

Seven questions at most, usually four. Each maps to a `seed.py` flag. Infer what the project
already answers and state the inference instead of asking.

## 1. What is the vault for? (sets `--archetype`)

- **Planning the build** (Recommended when the project is a code repo with no roadmap): ideas,
  bugs and the queue of Claude Code sessions. `roadmap`.
- **A second brain**: what is known, how things are done, who is who, what happened each day.
  `brain`.
- **Content the product reads**: definitions, copy or vocabulary authored by a person and
  loaded by code. `content`.
- **More than one**: seed each as its own vault in its own directory.

Tell-tales: a pile of TODOs, a `RUNWAY.md` or an issues list means `roadmap`. "I keep
re-explaining how X works" means `brain`. Strings or definitions hardcoded in prompts or
templates that the owner wants to write themselves means `content`.

## 2. Where does it live? (sets `--dest`)

- **A directory in this repo** (Recommended for `roadmap` and `content`): named for the
  project and the vault together, `acme-roadmap/` or `acme-lexicon/`, or a name the user
  gives. Tracked in git beside the code it serves.
- **The repo root is the vault** (usual for `brain`): the whole repository is the vault.
- **A standalone folder elsewhere**: give the path.

**The folder's name is the vault's name in Obsidian.** The vault switcher and the window title
show the last segment of the path and nothing else; `--name` does not reach them. A vault in a
folder called `roadmap/` is "roadmap" there, indistinguishable from every other project's. So
never offer a bare `roadmap/`, `lexicon/`, `vault/` or `notes/`: the default is the vault's
name as a slug (`--name "Acme roadmap"` gives `acme-roadmap/`, which is what `seed.py` uses
when `--dest` is left out), and `seed.py` refuses a generic folder unless `--generic-dir-ok`
is passed. Lower case with hyphens, because the path goes into a hook and shell commands. When
the repo root is the vault, the repo's own folder name is what Obsidian shows; say so if it is
something like `notes`.

## 3. What is it called, and whose is it? (sets `--name`, `--project`, `--owner`)

Offer a default from the repo name ("Acme roadmap", "Acme Brain", "Acme lexicon"), and always
with the project in it: the folder is named from it (question 2). `--owner`
is the person whose writing the vault holds; it appears in the authorship rules of `brain` and
`content`. Always pass it: the script's fallback is the first word of `git config user.name`,
which is often a handle. For a `roadmap`, also settle `--prefix`, the two or three letters
build names start with (`LD-07 Faster search`); default to the project's initials.

## 4. What kinds of notes? (sets `--kinds`)

- `roadmap`: fixed (Ideas and Builds). Ask instead for the three to six **areas** ideas will
  be filed under. An area is a part of the product a person would name ("Search", "Import",
  "Accounts"), free text in each idea's `area` field, and it is how `Ideas.md` is grouped.
  There is no flag: write them into the vault's `CLAUDE.md` afterwards. With no answer,
  propose them from the repo's top-level structure or from the material being migrated, and
  say they are a first guess.
- `brain`: pick from the kinds the seed knows, or name new ones (a new name gets a generic
  template to fill in). Known: `Knowledge` (claims), `Playbooks` (procedures), `People`,
  `Projects`, `Meetings`, `References`, `Notes`, `Clippings`, `Daily`. Default:
  `Knowledge,Playbooks,People`. Fewer is better: a kind is cheap to add the day a note has no
  home, and an unused one is clutter. The first kind listed is where new notes land.
- `content`: the entry types, singular and lower case (`term`, `card`, `step`). Default `term`.

## 5. Who or what reads it, besides the owner? (shapes the contract, no flag)

- **Only me and Claude sessions**: nothing extra.
- **Code or a pipeline**: for `content` this is the point; ask which surface reads which
  type and record it under "What reads it". For `brain`, note which properties are a schema.
- **Other people later**: record in `Decisions.md` which folders are shareable and which are
  private, and that customer or personal names stay out of the shareable ones. Do not build an
  export until someone needs it.

## 6. Automation (sets `--stop-hook`, `--working-memory`, the `Daily` kind)

- `roadmap`: **wire the Stop hook?** (Recommended) It blocks a session from ending with a
  build it worked but did not write back. Skip it only if sessions will not work from builds.
- `brain`: **a working-memory page?** `--working-memory` adds `Now.md` (dated bullets under
  Goals, Active, Waiting on, Recently done). Worth it when the vault follows live work.
  **Daily notes?** Add the `Daily` kind.

## 7. Look and plugins (sets `--accent`, `--plugins`)

Ask only if the user seems to care, otherwise default to none.

- An accent colour (`--accent "#rrggbb"`) so the vault is told apart from the user's others.
- Home-made plugins (`--plugins`), see `plugins.md`. Default: none for `roadmap` and `content`
  (the rule there is core Obsidian only); for a `brain` used daily, `home-button` and
  `manual-modified` are the two that earn their place first.

## Mapping, in one place

| Answer | Flag |
|---|---|
| purpose | `--archetype roadmap\|brain\|content` |
| location | `--dest <project>-<vault>` (omit it and the slug of `--name` is used) |
| names | `--name "<vault>" --project "<product>" --owner "<person>" --prefix LD` |
| kinds or types | `--kinds A,B,C` |
| Stop hook | `--stop-hook` |
| working memory | `--working-memory` |
| accent | `--accent "#rrggbb"` |
| plugins | `--plugins home-button,manual-modified` |
