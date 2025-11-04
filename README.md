# mobaxterm-sessions

Convert a MobaXterm bookmarks export into:
- Remmina profiles (.remmina)
- PuTTY saved sessions
- Rabbit Remote Control favorites (.rrc + Favorite.ini entries)

## Requirements
- Python 3.7+
- A MobaXterm bookmarks export file (e.g., `moba_bookmarks.txt`)
- For Remmina: Linux desktop with Remmina (profiles go under `~/.local/share/remmina` or the Flatpak dir)
- For PuTTY: either native PuTTY or Flatpak PuTTY (sessions directory will be created if missing)
- For Rabbit: Rabbit Remote Control installed and run at least once to create its config paths

## Preparing your input (choose one)

Option A — Start from the sanitized template (recommended for testing):
- Copy the provided template and edit placeholders (hosts, usernames, optional SSH key path):

```sh
cp moba_bookmarks.txt.example moba_bookmarks.txt
# edit moba_bookmarks.txt
```

- Keep the overall structure:
  - Group headers like `[Bookmarks_1]`
  - A group line like `SubRep=Example Servers`
  - Optional `ImgNum=` lines (these are ignored)
  - One or more entries like `Example-SSH-Host=...` (the right side is the MobaXterm-encoded fields)
- Lines starting with `#` are comments and ignored by the converters.

Option B — Use your MobaXterm export as-is:
- Export your bookmarks from MobaXterm to the text/INI-like format that contains sections named `[Bookmarks_*]` with entries `VisibleName=encoded_fields`.
- The converters look for:
  - Section headers: `[Bookmarks_*]`
  - Group name: `SubRep=...`
  - Entries: `Name=...` where the right-hand side starts with `#109` (SSH) or `#98` (Telnet), then `%host%port%user%...`
  - `ImgNum=` and blank/comment lines are ignored.
- You can pass the full export file directly with `--file`. Only matching lines will be processed.

---

## moba2remmina

Convert MobaXterm bookmarks export to Remmina profiles.

### Usage

Basic run (uses `./moba_bookmarks.txt` by default):

```sh
python3 moba2remmina.py
```

Specify a bookmarks file explicitly:

```sh
python3 moba2remmina.py --file moba_bookmarks.txt
```

Short flag:

```sh
python3 moba2remmina.py -f /path/to/moba_bookmarks.txt
```

Dry-run (no files created; shows the target paths):

```sh
python3 moba2remmina.py --file moba_bookmarks.txt --dry-run
```

### Output
- Profiles are created in:
  - Flatpak: `~/.var/app/org.remmina.Remmina/data/remmina/*.remmina`
  - Native:  `~/.local/share/remmina/*.remmina`

### Notes
- SSH entries attempt to detect a private key path if present in the export. `_ProfileDir_\\.ssh\...` maps to `~/.ssh/...`.
- Unknown protocols default to SSH.
- Remmina filenames are sanitized to `[A-Za-z0-9._-]`.

---

## moba2putty

Convert MobaXterm bookmarks to PuTTY saved sessions. Flatpak path is preferred by default; you can override.

### Usage

Basic run (reads `./moba_bookmarks.txt`):

```sh
python3 moba2putty.py
```

Explicit file and dry-run preview:

```sh
python3 moba2putty.py --file moba_bookmarks.txt --dry-run
```

Control the target sessions directory:

- Force native path (`~/.config/putty/sessions`, or legacy `~/.putty/sessions` if present):

```sh
python3 moba2putty.py --native -f moba_bookmarks.txt
```

- Force Flatpak path (`~/.var/app/uk.org.greenend.chiark.sgtatham.putty/config/putty/sessions`):

```sh
python3 moba2putty.py --flatpak -f moba_bookmarks.txt
```

- Custom directory:

```sh
python3 moba2putty.py --target /path/to/sessions -f moba_bookmarks.txt
```

### Output
- Session files are created under the chosen PuTTY sessions directory. Names are URL-encoded to be filesystem-safe.

### Notes
- SSH key paths like `_ProfileDir_\\.ssh\id_ed25519` are mapped to `~/.ssh/id_ed25519`.
- Original group (if any) is written as `_ImportedGroup` metadata in the session.
- Protocols supported: SSH and Telnet; others are skipped.

---

## moba2rabbit

Convert the same MobaXterm bookmarks export into Rabbit Remote Control favorites (.rrc) and append them to Rabbit's Favorite.ini. SSH and Telnet are supported; original groups are preserved as metadata.

### Requirements
- Rabbit Remote Control installed locally, with configuration created at least once
  - Expected paths (created by Rabbit on first run):
    - `$HOME/Documents/Rabbit/RabbitRemoteControl/etc/Favorite.ini`
    - `$HOME/Documents/Rabbit/RabbitRemoteControl/share`

If these paths don't exist, open Rabbit, create a dummy connection, then close it.

### Usage

Basic run (reads `./moba_bookmarks.txt` by default):

```sh
python3 moba2rabbit.py
```

Specify a bookmarks file explicitly:

```sh
python3 moba2rabbit.py --file moba_bookmarks.txt
```

Short flag:

```sh
python3 moba2rabbit.py -f /path/to/moba_bookmarks.txt
```

Dry-run (no files created; prints intended actions):

```sh
python3 moba2rabbit.py --file moba_bookmarks.txt --dry-run
```

### Output
- Creates `.rrc` files under: `$HOME/Documents/Rabbit/RabbitRemoteControl/share/`
- Appends entries to: `$HOME/Documents/Rabbit/RabbitRemoteControl/etc/Favorite.ini`
  - Adds `File_{idx}`, `Name_{idx}`, and a minimal `Descripte_{idx}` (includes the original group if present)
  - Updates `RootCount` accordingly

When run with `--dry-run`, the script prints the target `.rrc` paths and Favorite entries instead of writing them.

### Input guidance
- Use the same input file described above. You can:
  - Start from the sanitized template:
    ```sh
    cp moba_bookmarks.txt.example moba_bookmarks.txt
    # edit placeholders (hosts, usernames, optional key path)
    python3 moba2rabbit.py --file moba_bookmarks.txt --dry-run
    ```
  - Or pass your full MobaXterm export; only lines under `[Bookmarks_*]`, `SubRep=...`, and `Name=...=...` are processed. `ImgNum=` and comment lines are ignored.

### Notes
- SSH key paths like `_ProfileDir_\\.ssh\id_ed25519` are mapped to `~/.ssh/id_ed25519`.
- Visible names are not prefixed with the group; group is stored as metadata and echoed in the description.
- Unknown protocols are skipped (reported on stderr) rather than imported.

---

## Quick start (dry-run with the template)

```sh
cp moba_bookmarks.txt.example moba_bookmarks.txt
python3 moba2remmina.py --file moba_bookmarks.txt --dry-run
python3 moba2putty.py   --file moba_bookmarks.txt --dry-run
python3 moba2rabbit.py  --file moba_bookmarks.txt --dry-run
```

## Troubleshooting
- `Error: input file not found` → Ensure the `--file` path is correct and readable.
- Remmina: Profiles must be under `~/.local/share/remmina/` (or Remmina Flatpak data dir) to be detected.
- PuTTY: If using Flatpak, sessions live under `~/.var/app/uk.org.greenend.chiark.sgtatham.putty/config/putty/sessions`.
- Rabbit: If its paths don’t exist yet, run Rabbit once and create a dummy connection so it creates `Favorite.ini` and the `share` directory.
