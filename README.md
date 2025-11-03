# moba-to-remmina

Convert MobaXterm bookmarks export to Remmina profiles.

## Requirements
- Python 3.7+
- A MobaXterm bookmarks export file (e.g., `moba_bookmarks.txt`)
- Linux desktop with Remmina (files will be written to `~/.local/share/remmina`)

## Usage

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

Output profiles are created in:

- `~/.local/share/remmina/*.remmina`

## Preparing your input (choose one)

Option A — Start from the example template (recommended for testing):
- Copy the provided sanitized template and then edit placeholders (hosts, usernames, optional SSH key path):

```sh
cp moba_bookmarks.txt.example moba_bookmarks.txt
# edit moba_bookmarks.txt
python3 moba2remmina.py --file moba_bookmarks.txt --dry-run
```

- Keep the overall structure:
  - Group headers like `[Bookmarks_1]`
  - A group name line like `SubRep=Example Servers`
  - Optional `ImgNum=` lines (these are ignored)
  - One or more entries like `Example-SSH-Host=...` (the right side is the encoded fields from MobaXterm)
- Comment lines starting with `#` are ignored, so you can annotate your file.

Option B — Use your MobaXterm export as-is:
- Export your bookmarks from MobaXterm to a text/INI-like format that contains sections named `[Bookmarks_*]` with entries in the form `VisibleName=encoded_fields`.
- The converter looks for the following lines and ignores the rest:
  - Section headers: `[Bookmarks_*]`
  - Group name: `SubRep=...`
  - Entries: `Name=...` where the right-hand side contains the MobaXterm-encoded connection string (e.g., starts with `#109` for SSH or `#98` for Telnet, then `%host%port%user%...`).
  - `ImgNum=` and blank/comment lines are safely ignored.
- You can pass the full export file directly with `--file`. Only matching lines will be processed.

## Notes
- SSH entries attempt to detect a private key path if present in the MobaXterm export. `_ProfileDir_\\.ssh\...` is mapped to `~/.ssh/...`.
- Unknown protocols default to SSH.
- Filenames are sanitized to `[A-Za-z0-9._-]` only.
- Lines beginning with `#` are treated as comments and ignored by the converter.

## Troubleshooting
- If you see `Error: input file not found`, ensure the path to the export file is correct and readable.
- Remmina won’t pick up files unless they’re under `~/.local/share/remmina/`.


## moba2rabbit

Convert the same MobaXterm bookmarks export into Rabbit Remote Control favorites (.rrc) and append them to Rabbit's Favorite.ini. SSH and Telnet are supported; original groups are preserved as metadata.

### Requirements
- Python 3.7+
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

### Troubleshooting
- `Error: expected Rabbit path not found: ...` → Launch Rabbit once and create a dummy connection so it creates its directories and Favorite.ini.
- `Error: input file not found: ...` → Check your `--file` path.
