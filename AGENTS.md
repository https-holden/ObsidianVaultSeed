# For the AI helping someone set this up

You are probably here because a person pointed you at this repository and said something like
"help me get this set up". This file tells you how. It works for Claude (desktop app, Code tab,
or Claude Code), ChatGPT, Codex, Gemini or any other assistant.

## Who you are helping

Assume a beginner until they show otherwise: they may never have used Obsidian, a terminal,
git or GitHub, and may not know what a wiki link is. So:

- **One step at a time.** Say exactly what to click or paste, then wait for them to say it
  worked (or to paste what they see) before the next step. Never hand over ten steps at once.
- **Plain words.** "A folder of notes" before "a vault"; "the box of properties at the top of
  a note" before "frontmatter". Introduce a term once, when it is needed.
- **Every command in its own copyable block**, and say where to run it (Terminal on a Mac,
  PowerShell on Windows, and from which folder).
- **Never ask for a password, token or code**, and never ask them to paste one into the chat.
  Sign-ins happen in their browser. They do not need a GitHub account for any of this.
- **Celebrate small wins**, and if something fails, read the error with them before guessing.

## First, find out two things

1. **Their computer**: Mac or Windows. (Linux works like the Mac path.)
2. **What you can do**: if you can run commands on their machine (Claude Code, the Claude
   desktop app's Code tab, Codex), you do the commands and they watch. If you are a chat in a
   browser (ChatGPT, claude.ai, Gemini), they run the commands and you guide.

Then ask, briefly, what the second brain is for: their life (journal, ideas, reading, people,
projects) or their job (how things work, procedures, colleagues, meetings). That picks the
preset: `personal` or `work`. Ask their first name for the vault's name.

## The setup, in order

### 1. Get Obsidian

Download from https://obsidian.md/download and install it like any app. No account needed.

### 2. Get this repository onto their computer

**Mac.** In Terminal (Cmd+Space, type Terminal, Enter), first the developer tools, which bring
git and Python:

```bash
xcode-select -p >/dev/null 2>&1 && echo "already installed" || xcode-select --install
```

A window appears: they click **Install**, not "Get Xcode". Full Xcode is a huge app they do
not need. It takes 5 to 15 minutes. Then:

```bash
git clone https://github.com/https-holden/ObsidianVaultSeed.git ~/ObsidianVaultSeed && bash ~/ObsidianVaultSeed/setup/mac.sh
```

**Windows.** In PowerShell:

```powershell
winget install --id Git.Git -e; winget install --id Python.Python.3.12 -e
```

Close and reopen PowerShell, then:

```powershell
git clone https://github.com/https-holden/ObsidianVaultSeed.git $HOME\ObsidianVaultSeed; powershell -ExecutionPolicy Bypass -File $HOME\ObsidianVaultSeed\setup\windows.ps1
```

**No terminal at all** (if they really do not want one): on the GitHub page, the green
**Code** button, **Download ZIP**, unzip it, and copy the `starter-vault` folder into
`Documents`. Rename the folder to their name (say `sam-brain`). That is a ready vault. The
scripts inside it need Python later, but Obsidian works right away.

The setup script asks their name and personal or work, and makes the vault at
`~/Documents/Obsidian/<name>-brain`. If you are running it for them, pass the answers so it
does not wait for typing:

```bash
bash ~/ObsidianVaultSeed/setup/mac.sh --name Sam --preset personal
```

### 3. Open the vault in Obsidian

Obsidian, **Open folder as vault**, choose that folder, trust it. Open **Home**. Then give them
the ten-minute tour from [guides/obsidian-basics.md](guides/obsidian-basics.md): links with
`[[`, backlinks, properties, categories instead of folders, templates, the tables. Have them
make one note and one link while you explain, so it sticks.

### 4. Fill in Me.md together

`Me.md` in the vault says who they are, what the vault is for, what they will bring in and
what is private. Interview them, a few questions at a time, and write it (or give them the
text to paste). Every AI that helps them later reads it first.

### 5. Bring in the first things

Ask what they already have: articles, PDFs, an old journal, notes in another app, voice memos.
Pick two or three and bring them in with them, following
[guides/bringing-things-in.md](guides/bringing-things-in.md). Then file them: with Claude,
`python3 bin/librarian.py` or "file my clippings"; with a chat AI, the `--paste` and `--apply`
round trip. Open the filed notes in Obsidian together and show them the topic pages filling
themselves in.

### 6. Show them the daily loop

[guides/daily-loop.md](guides/daily-loop.md): "start my day" in the morning, jot under
`## Notes` in the daily note, "end of day" in the evening. That habit is what makes it a
second brain. With a chat AI, the prompts are in
[guides/prompts-for-any-ai.md](guides/prompts-for-any-ai.md).

### 7. Optional, later

- A backup: [guides/backup-with-github.md](guides/backup-with-github.md). Only now does a
  GitHub account matter, and only if they choose GitHub.
- Kepano's Obsidian skills for Claude Code, which teach Claude the exact note and table syntax:
  in a Claude Code session, `/plugin marketplace add kepano/obsidian-skills`, then
  `/plugin install obsidian@obsidian-skills`.
- Sharing with a team: [guides/sharing-a-vault.md](guides/sharing-a-vault.md).

## Once the vault exists

Work from the vault's own `CLAUDE.md` (inside their vault folder, not this repo's). It is the
contract: where each kind of note goes, the properties, the rules, the check to run
(`python3 bin/lint.py`). Follow it exactly, even if you are not Claude. Never invent notes or
facts for them: the vault holds their material, not yours.

## What is in this repository

| Path | What it is |
|---|---|
| `START-HERE.md` | The same journey, written for the person instead of for you |
| `setup/` | `mac.sh` and `windows.ps1`: install what is missing and make the vault |
| `starter-vault/` | A ready-made personal vault for people who skip the terminal |
| `guides/` | Obsidian basics, bringing things in, the daily loop, backup, sharing, chat prompts |
| `skills/vault-seed/` | A Claude Code skill (`/vault-seed`) that interviews and builds any kind of vault, including planning and content vaults for code projects. `scripts/seed.py` is the builder the setup scripts call |
