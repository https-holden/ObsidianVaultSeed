# Home-made plugins

Four small plugins are bundled in `assets/plugins/`. Each is plain `main.js` plus
`manifest.json` (and sometimes `styles.css`): no bundler, no build step, readable in one
sitting. `seed.py --plugins a,b` copies them into `.obsidian/plugins/` and lists them in
`community-plugins.json`. The user turns Restricted mode off once to load them.

| Plugin | What it does | Worth it when |
|---|---|---|
| `home-button` | A house icon in the ribbon and an "Open Home" command that open the `Home` note, reusing its tab. | The vault has a hub that is opened many times a day. |
| `manual-modified` | Keeps a `modified` date that only changes when a person types in the note. Renames, templates and scripts do not count. Excluded folders in its `data.json`. | Sessions and scripts write to the vault, and "what did I last touch by hand" matters. |
| `resting-view` | Notes open at rest: no cursor, blocks at the top render, a click edits in place. | Hubs and briefs that are read more than written. |
| `sticky-bullets` | A scrolled-off parent bullet stays pinned at the top of the editor. | Long nested lists and checklists. |

## Writing another

- Plain JS, `require("obsidian")`, one `module.exports = class extends Plugin`.
- The repo copy is the source of truth and the vault copy is an install. Two hand-edited
  copies drift.
- Document every plugin in the vault's `Readme.md`: what it does and what depends on it.
- Reload after an edit with the `obsidian` CLI (load `obsidian:obsidian-cli`), or by toggling
  the plugin in settings.
- A plugin that patches Obsidian's private API says so in its header, so it is the first
  thing disabled when an update breaks something.
