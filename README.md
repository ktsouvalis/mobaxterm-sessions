# moba-to-remmina

Convert MobaXterm bookmarks export to Remmina profiles.

## Requirements
- Python 3.7+
- A MobaXterm bookmarks export file (e.g., `moba_bookmarks.txt`)
- Linux desktop with Remmina (files will be written to `~/.local/share/remmina`)

## Usage

Basic run (uses `./moba_bookmarks.txt` by default):

```sh
python3 main.py
```

Specify a bookmarks file explicitly:

```sh
python3 main.py --file moba_bookmarks.txt
```

Short flag:

```sh
python3 main.py -f /path/to/moba_bookmarks.txt
```

Dry-run (no files created; shows the target paths):

```sh
python3 main.py --file moba_bookmarks.txt --dry-run
```

Output profiles are created in:

- `~/.local/share/remmina/*.remmina`

## Preparing your input (choose one)

Option A — Start from the example template (recommended for testing):
- Copy the provided sanitized template and then edit placeholders (hosts, usernames, optional SSH key path):

```sh
cp moba_bookmarks.txt.example moba_bookmarks.txt
# edit moba_bookmarks.txt
python3 main.py --file moba_bookmarks.txt --dry-run
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
