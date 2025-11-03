#!/usr/bin/env python3
import os, re, sys, argparse
from pathlib import Path
from typing import NamedTuple

HOME = str(Path.home())
RABBIT_DIR = f"{HOME}/Documents/Rabbit/RabbitRemoteControl"
FAV_INI   = f"{RABBIT_DIR}/etc/Favorite.ini"
SHARE_DIR = f"{RABBIT_DIR}/share"

class Entry(NamedTuple):
    name: str
    protocol: str
    host: str
    port: str
    user: str
    key_path: str
    group: str | None

parser = argparse.ArgumentParser(description="Convert MobaXterm bookmarks to Rabbit Remote Control favorites (SSH + Telnet), without prefixing names. Stores original group as metadata.")
parser.add_argument("-f","--file", dest="src_file", default="./moba_bookmarks.txt",
                    help="Path to MobaXterm bookmarks export (default: ./moba_bookmarks.txt)")
parser.add_argument("-n","--dry-run", action="store_true", help="Preview without writing files")
args = parser.parse_args()

SRC_FILE = args.src_file
DRY_RUN  = args.dry_run

for needed in [FAV_INI, SHARE_DIR]:
    if not os.path.exists(needed):
        print(f"Error: expected Rabbit path not found: {needed}", file=sys.stderr)
        print("Open Rabbit once, create a dummy connection, then close it.")
        sys.exit(1)

if not os.path.isfile(SRC_FILE):
    print(f"Error: input file not found: {SRC_FILE}", file=sys.stderr)
    sys.exit(1)

def parse_line(name: str, rhs: str, group: str | None) -> Entry:
    parts = rhs.split('%')
    proto_code = parts[0] if parts else "#109#0"

    if proto_code.startswith("#109"):
        protocol = "SSH";    port_default = "22"
    elif proto_code.startswith("#98"):
        protocol = "TELNET"; port_default = "23"
    else:
        protocol = "SSH";    port_default = "22"

    host = parts[1] if len(parts) > 1 and parts[1] else ""
    port = parts[2] if len(parts) > 2 and parts[2] else port_default
    user = parts[3] if len(parts) > 3 and parts[3] else ""

    key_path = ""
    for p in parts:
        if ".ssh" in p or "\\.ssh" in p:
            key_path = p
            break
    if key_path:
        key_path = key_path.replace("_ProfileDir_\\", "").replace("\\", "/")
        if not key_path.startswith("/"):
            key_path = f"{HOME}/{key_path}"

    return Entry(name=name.strip(), protocol=protocol, host=host.strip(),
                 port=port.strip(), user=user.strip(), key_path=key_path.strip(),
                 group=(group.strip() if group else None))

def read_rootcount(fav_text: str) -> int:
    m = re.search(r"^RootCount=(\d+)\s*$", fav_text, flags=re.M)
    return int(m.group(1)) if m else 0

def set_rootcount(fav_text: str, new_count: int) -> str:
    if re.search(r"^RootCount=\d+\s*$", fav_text, flags=re.M):
        return re.sub(r"^RootCount=\d+\s*$", f"RootCount={new_count}", fav_text, flags=re.M)
    else:
        if "[General]" in fav_text:
            return fav_text.replace("[General]", f"[General]\nRootCount={new_count}")
        return f"[General]\nRootCount={new_count}\n" + fav_text

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', "_", name).strip("_")

def make_rrc_common(entry_name: str, group: str | None) -> list[str]:
    lines = []
    lines.append("[General]")
    lines.append(f"Name={entry_name}")
    if group:
        lines.append(f"Group={group}")  # stored as metadata; Rabbit may ignore, but useful
    lines.append("")
    lines.append("[Manage]")
    lines.append("FileVersion=1")
    lines.append("")
    return lines

def make_rrc_terminal_block(keybindings: str) -> list[str]:
    t = []
    t.append("[Terminal]")
    t.append("BackgroupImage=")
    t.append("ColorScheme=GreenOnBlack")
    t.append("Commands=@Invalid()")
    t.append("Directional=true")
    t.append('Font="DejaVu Sans Mono,12,-1,2,400,0,0,0,0,0,0,0,0,0,0,1"')
    t.append("HistorySize=1000")
    t.append(f"KeyBindings={keybindings}")
    t.append("SizeHint=false")
    t.append("TextCodec=UTF-8")
    t.append("Transparency=0")
    t.append("cursorShape=0")
    t.append("disableBracketedPasteMode=false")
    t.append("flowControl=false")
    t.append("flowControlWarning=false")
    t.append("motionAfterPasting=false")
    t.append("scrollBarPosition=2")
    t.append("")
    return t

def make_rrc_user_block(user: str, key_path: str | None, is_ssh: bool) -> list[str]:
    u = []
    u.append("[User]")
    u.append("Authentication\\PublicKey\\File\\CA=")
    u.append("Authentication\\PublicKey\\File\\CRL=")
    if is_ssh:
        u.append(f"Authentication\\PublicKey\\File\\PrivateKey={key_path or ''}")
        u.append("Authentication\\PublicKey\\File\\PublicKey=")
        u.append("Authentication\\PublicKey\\File\\SavePassphrase=false")
        u.append("Authentication\\PublicKey\\File\\UseSystemFile=true")
        types = "2, 3"
        used  = "3" if key_path else "2"
    else:
        u.append("Authentication\\PublicKey\\File\\PrivateKey=")
        u.append("Authentication\\PublicKey\\File\\PublicKey=")
        u.append("Authentication\\PublicKey\\File\\SavePassphrase=false")
        u.append("Authentication\\PublicKey\\File\\UseSystemFile=true")
        types = "2"; used = "2"
    u.append("Authentication\\SavePassword=false")
    u.append(f"Authentication\\Type={types}")
    u.append(f"Authentication\\Type\\Used={used}")
    u.append(f"Name={user}")
    u.append("")
    return u

def make_rrc_ssh(entry: Entry) -> str:
    lines = make_rrc_common(entry.name, entry.group)
    lines.append("[Net]")
    lines.append(f"Host={entry.host}")
    lines.append(f"Port={entry.port or '22'}")
    lines.append("")
    lines.append("[Plugin]")
    lines.append("ID=1:SSH:SSH")
    lines.append("Name=SSH")
    lines.append("Protocol=SSH")
    lines.append("")
    lines.extend(make_rrc_terminal_block("default"))
    lines.extend(make_rrc_user_block(entry.user, entry.key_path, is_ssh=True))
    return "\n".join(lines)

def make_rrc_telnet(entry: Entry) -> str:
    lines = make_rrc_common(entry.name, entry.group)
    lines.append("[Net]")
    lines.append(f"Host={entry.host}")
    lines.append(f"Port={entry.port or '23'}")
    lines.append("")
    lines.append("[Plugin]")
    lines.append("ID=1:Telnet:Telnet")
    lines.append("Name=Telnet")
    lines.append("Protocol=Telnet")
    lines.append("")
    lines.extend(make_rrc_terminal_block("vt420pc"))
    lines.extend(make_rrc_user_block(entry.user, None, is_ssh=False))
    return "\n".join(lines)

def append_favorite(fav_text: str, idx: int, rrc_path: str, disp_name: str, group: str | None) -> str:
    insertion = []
    insertion.append(f"File_{idx}={rrc_path}")
    insertion.append(f"Name_{idx}={disp_name}")
    # Put a lightweight description that includes the group (searchable in Rabbit)
    if group:
        # keep it simple; no huge block like the stock SSH description
        insertion.append(f'Descripte_{idx}="Group: {group}"')
    insertion.append("")
    return fav_text.rstrip() + "\n" + "\n".join(insertion) + "\n"

with open(FAV_INI, "r", encoding="utf-8", errors="ignore") as f:
    fav_text = f.read()

rootcount = read_rootcount(fav_text)
next_idx  = rootcount

if not DRY_RUN:
    os.makedirs(SHARE_DIR, exist_ok=True)

created = 0
skipped = 0

with open(SRC_FILE, "r", encoding="utf-8") as f:
    current_group = None  # <<< FIX: no stray underscore
    for raw_line in f:
        line = raw_line.rstrip("\n")
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("[Bookmarks_"):
            current_group = None
            continue
        if line.startswith("SubRep="):
            current_group = line.split("=",1)[1].strip()
            continue
        if line.startswith("ImgNum="):
            continue
        if "=" in line:
            name, rhs = line.split("=", 1)
            e = parse_line(name, rhs, current_group)

            # Use ONLY the raw bookmark name (no group prefix in visible name)
            disp_name = e.name

            if e.protocol == "SSH":
                rrc_filename = f"SSH_SSH_{next_idx}_{sanitize_filename(disp_name)}.rrc"
                content = make_rrc_ssh(e)
            elif e.protocol == "TELNET":
                rrc_filename = f"Telnet_Telnet_{next_idx}_{sanitize_filename(disp_name)}.rrc"
                content = make_rrc_telnet(e)
            else:
                skipped += 1
                print(f"Skipping unknown protocol entry: {disp_name} ({e.protocol})", file=sys.stderr)
                continue

            rrc_path = os.path.join(SHARE_DIR, rrc_filename)

            if DRY_RUN:
                print(f"[dry-run] Would write {rrc_path}")
                print(f"[dry-run] Would add Favorite: Name_{next_idx}={disp_name} (Group: {e.group or '-'})")
            else:
                with open(rrc_path, "w", encoding="utf-8") as out:
                    out.write(content)
                fav_text = append_favorite(fav_text, next_idx, rrc_path, disp_name, e.group)

            next_idx += 1
            created += 1

new_rootcount = next_idx
if not DRY_RUN:
    fav_text = set_rootcount(fav_text, new_rootcount)
    with open(FAV_INI, "w", encoding="utf-8") as f:
        f.write(fav_text)

print(f"Done. Created: {created}, Skipped: {skipped}. New RootCount: {new_rootcount}.")
if DRY_RUN:
    print("Dry-run only: no files written.")
