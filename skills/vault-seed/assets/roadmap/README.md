# @@VAULT_NAME@@

An Obsidian vault holding the plan for @@PROJECT@@ and the prompts that build it. Open it with
"Open folder as vault" pointed at this directory, and start at [[Home]].

It is plain Markdown with wikilinks, so it works from a terminal too, and it is tracked in git
beside the code it plans, so `git diff` shows how the plan moved.

Tables are generated. After editing any note:

```
python3 @@VAULT_PREFIX@@bin/reindex.py
```

`CLAUDE.md` in this directory is the maintenance contract: the note schema, the single-source
rule for the idea/build relation, and what a session owes the vault when it finishes.
