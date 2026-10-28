# Eiyu*Senki Gold Balance Editor

Python script and web GUI done by Claude.

Unpack the game's data files, edit units / skills / income / items / enemy battles in a simple web page, and pack them back so the game loads them.

Tested against Steam v1.03c1 of *Eiyu\*Senki Gold* (Eiyuu\*Senki GOLD: A New Conquest). This is an unofficial fan tool. Always keep backups of the original files.

## What's in the kit

| File | What it does |
|---|---|
| `rpack.py` | Command-line tool that unpacks a game `.dat` into plain text files and packs them back. |
| `define_editor.html` | Offline editor you open in a browser. Nothing is uploaded anywhere. |

## What you need

- **Python 3** (3.10 or newer recommended; any current version from python.org is fine). On Windows, tick **"Add python.exe to PATH"** in the installer. If `python` opens the Microsoft Store, use `py` instead.
- A modern browser (Chrome/Edge 90+, Firefox 88+, Safari 16.4+).
- The two game files: `Define.dat` and `BattleSet.dat` in `\AUGGame`.

## Quick walkthrough

### 0. Back up the originals
Copy the original `Define.dat` and `BattleSet.dat` to a safe folder the game never touches. If anything goes wrong, put them back.

### 1. Set up a work folder
Make a folder, e.g. `D:\Mods\EiyuSenki`, and put in it `rpack.py` plus copies of `Define.dat` and `BattleSet.dat`. Open PowerShell in that folder.

### 2. Unpack
```
python rpack.py extract Define.dat define_txt
python rpack.py extract BattleSet.dat battleset_txt --hints define_txt\team.txt
```
Expected output: `extracted 63 files` for the first and `extracted 19 files` for the second. If the second says 0, you are using an old `rpack.py`.

`--hints` must come last. It points at `team.txt`, which lists the names of the BattleSet files. The pack itself doesn't store file names.

### 3. Edit
1. Open `define_editor.html` in your browser.
2. Drag in files:
   - from `define_txt`: `unit.txt`, `tech.txt`, `city.txt`, `item.txt`, `itemmix.txt`, `battlestate.txt`
   - optional, for English names: `spot.txt`, `country.txt`, `techkind.txt`, `skill.txt`
   - from `battleset_txt`: all the `battleset_*.txt` files
3. Use the tabs and type new values. Edited boxes turn yellow, invalid ones red.
4. **Review changes** shows every edit as old → new.

### 4. Save edits back to the folders
- Define files: **Download unit.txt** (etc.) or **Download all edited**, saved into `define_txt` and replace the old file(s).
- Battle files: **Download edited battle files (.zip)** on the Battles tab, unzipped into `battleset_txt` and replace the old file(s).

### 5. Repack
```
python rpack.py repack Define.dat define_txt Define_new.dat
python rpack.py repack BattleSet.dat battleset_txt BattleSet_new.dat --hints define_txt\team.txt
```
It prints `modified <file>` for every file you changed. If none are listed, your downloads didn't reach the right folder.

### 6. Install
Close the game. Rename the originals in the game folder (e.g. `Define.dat.bak`), copy in the new files and rename them to exactly `Define.dat` and `BattleSet.dat`. Start the game and test.

## What the editor can edit

| Tab | Editable | Not editable |
|---|---|---|
| Units (101) | Element, Troops, ATK, DEF, SPD, skill list, map skills | names, faction, LCK/heal (in `unitmodel.txt`), traits |
| Skills (428) | Level, Brave cost, WT (charge), DLY (delay), Mult (damage/heal multiplier), Hits, Crit, Fixed damage | names, descriptions, ranges, AI weights, extra effects |
| Cities (151) | Funds (income), Walls | owner, names |
| Items (225) | Price, effect slots (buff ids), summary and description text | names, images (copies inherit from their original) |
| Crafting (73) | Recipe cost | ingredients and results |
| Buffs/States (348) | Value (`add=`), description text | effect type, conditions |
| Battles (2,672 enemy units in 420 battles + 118 teams) | Troops, ATK, DEF, SPD, LCK, Element, skills, equipment, trait | formations, drops, turn limits, models, names |

It can't add or delete entries or rename ids.

Tools on every tab: search, filters, sortable columns, **Bulk edit** (×, + or = on a column across the filtered rows), per-row **reset**, **Review changes**. Unsaved edits are remembered in your browser.

## Rules that avoid crashes

- **Decimals need a decimal point.** Multipliers are floats: `5.0`, not `5`. The editor adds `.0` automatically; if you edit the text files by hand, do it yourself. Writing `10` where `10.0` was expected caused an "Internal Error" crash.
- **Ids must exist.** Skills, equipment and effect lists are comma-separated ids. Use the English names shown under the box to check them; unknown ids show in red.
- **Description text is only display.** Changing a number doesn't update the text that describes it, so edit both.
- **Small steps.** Change a few things, test, then continue. A bad value usually only shows up when the game uses it.
- Values are saved in Shift-JIS (cp932). Characters Shift-JIS can't represent stop the repack with an error.

## How the game uses these files (useful for deciding what to edit)

- **Named characters**, including named enemy leaders such as Pandora, are in `unit.txt`. Enemies in battles can say `ベース="<unit id>"` to inherit a named unit's stats and then override only some fields.
- **Generic enemies** (soldiers, bandits) are defined inline per battle in the BattleSet files, with their own troops and stats. Their appearance, element, LCK and heal come from a model in `unitmodel.txt` (372 models).
- A battle header with `兵力="相対"` scales enemy troops relative to something about your army. In one test the factor was about ×4.8 on every unit. Test troop edits in such battles.
- **Items** point at buffs by id; the actual numbers live in `battlestate.txt`. Editing a buff changes everything that uses it.
- `battlestate.txt` also contains income modifiers (kind `都市収入`).

## Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| "Internal Error" box on start or when using something | Restore the `.bak` files. Check the last edits: a whole number where a decimal was expected, or a mistyped skill/item id. |
| `extracted 0 files` for `BattleSet.dat` | Old `rpack.py`, or `--hints` missing or not last, or `team.txt` isn't the one from your `Define.dat` extract. |
| `python` not recognised | Reinstall Python with "Add python.exe to PATH" ticked, or use `py`. |
| Changes don't appear in game | Wrong folder, wrong file name, or Steam restored the originals ("Verify integrity of game files" overwrites mods). |
| Repack error about a character | A character isn't in Shift-JIS. Replace it. |
| After a game update | Unpack the new original `.dat` files and redo your edits. Don't reuse old edited packs on a new version. |

## Verification status

- `rpack.py` repacks an unmodified `Define.dat` and `BattleSet.dat` byte-for-byte identical to the originals, and edited packs extract back to exactly the edited text.
- In game, a `Define.dat` edit to a skill's multiplier (`倍率`) was confirmed to load and take effect.
- In game, a `BattleSet.dat` edit to Bandit King's troops (700 → 7000 in the "Bandit Raid" battle) was confirmed: the unit appeared with 33,742 troops, the same ≈×4.8 relative scaling (`兵力="相対"`) as before the edit applied to the new value.
- Other fields use the same mechanism but were not each tested. Anything the game parses normally should take effect; values above the game's own limits, or wrong skill/item ids, can crash it. The game's limits are unknown, so raise numbers in steps.

## File format notes (for the curious)

`RepiPack` archive: header `RepiPack`, version 5, name, entry count, then 32-byte table entries (MD5 of the lowercase Shift-JIS file name, offset, stored size, real size) encrypted with a running-key dword cipher. Entry data has its first 1024 bytes XOR-ed with a keystream built from a chained MD5 of the reversed file name, and is LZSS-compressed (4096-byte ring, start 0xFEE) when stored size differs from real size. Full details are in the docstring of `rpack.py`.

