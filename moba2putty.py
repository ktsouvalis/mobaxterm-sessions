#!/usr/bin/env python3
import os, sys, argparse
from pathlib import Path
from urllib.parse import quote
from typing import NamedTuple

HOME = str(Path.home())

PUTTY_FLATPAK_APPID = "uk.org.greenend.chiark.sgtatham.putty"
PUTTY_FLATPAK_SESS = Path(HOME) / f".var/app/{PUTTY_FLATPAK_APPID}/config/putty/sessions"
PUTTY_NATIVE_SESS = Path(os.getenv("XDG_CONFIG_HOME", f"{HOME}/.config")) / "putty" / "sessions"
PUTTY_LEGACY_SESS = Path(HOME) / ".putty" / "sessions"

class Entry(NamedTuple):
    name: str
    protocol: str   # SSH | TELNET
    host: str
    port: str
    user: str
    key_path: str
    group: str | None

def detect_target(args) -> Path:
    # 1) explicit wins
    if args.target:
        return Path(args.target).expanduser()

    # 2) honor --native / --flatpak
    if args.native:
        if PUTTY_NATIVE_SESS.exists():
            return PUTTY_NATIVE_SESS
        elif PUTTY_LEGACY_SESS.exists():
            return PUTTY_LEGACY_SESS
        else:
            return PUTTY_NATIVE_SESS  # will be created
    if args.flatpak:
        return PUTTY_FLATPAK_SESS

    # 3) DEFAULT: Flatpak first (create if missing), else native, else legacy
    return PUTTY_FLATPAK_SESS if True else PUTTY_NATIVE_SESS  # (always prefer Flatpak)

def parse_line(name: str, rhs: str, group: str | None) -> Entry:
    parts = rhs.split('%')
    proto_code = parts[0] if parts else "#109#0"
    if proto_code.startswith("#109"):
        protocol, port_default = "SSH", "22"
    elif proto_code.startswith("#98"):
        protocol, port_default = "TELNET", "23"
    else:
        protocol, port_default = "SSH", "22"

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

    return Entry(
        name=name.strip(),
        protocol=protocol,
        host=host.strip(),
        port=port.strip(),
        user=user.strip(),
        key_path=key_path.strip(),
        group=(group.strip() if group else None),
    )

def putty_encode(name: str) -> str:
    # encode special chars for session filename
    return quote(name, safe="").replace("/", "%2F")

def write_session(entry: Entry, target_dir: Path):
    settings = {
        "HostName": entry.host,
        "PortNumber": entry.port or ("22" if entry.protocol == "SSH" else "23"),
        "Protocol": entry.protocol.lower(),
        "UserName": entry.user,
        "TerminalType": "xterm",
        # readable on open:
        # "Colour0": "255,255,255",   # default FG = white
        # "Colour2": "0,0,0",         # default BG = black
    }
    if entry.protocol == "SSH" and entry.key_path:
        settings["PublicKeyFile"] = entry.key_path
    if entry.group:
        settings["_ImportedGroup"] = entry.group  # harmless metadata

    path = target_dir / putty_encode(entry.name)
    content = "\n".join(f"{k}={v}" for k,v in settings.items()) + "\n"
    return path, content

def main():
    ap = argparse.ArgumentParser(
        description="Convert MobaXterm bookmarks to PuTTY saved sessions (Flatpak by default)."
    )
    ap.add_argument("-f","--file", dest="src_file", default="./moba_bookmarks.txt",
                    help="Path to MobaXterm bookmarks export")
    ap.add_argument("-n","--dry-run", action="store_true", help="Preview without writing files")
    ap.add_argument("--target", help="Override target sessions directory")
    ap.add_argument("--native", action="store_true", help="Force native path (~/.config/putty/sessions)")
    ap.add_argument("--flatpak", action="store_true", help="Force Flatpak path (~/.var/app/.../config/putty/sessions)")
    args = ap.parse_args()

    src = Path(args.src_file)
    if not src.is_file():
        print(f"Error: input file not found: {src}", file=sys.stderr); sys.exit(1)

    target_dir = detect_target(args)
    if not args.dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    current_group = None

    with src.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[Bookmarks_"):
                current_group = None; continue
            if line.startswith("SubRep="):
                current_group = line.split("=",1)[1].strip(); continue
            if line.startswith("ImgNum="):
                continue
            if "=" not in line:
                continue

            name, rhs = line.split("=", 1)
            e = parse_line(name, rhs, current_group)

            if e.protocol not in ("SSH", "TELNET"):
                skipped += 1
                continue

            path, content = write_session(e, target_dir)
            if args.dry_run:
                print(f"[dry-run] Would write {path}")
                print(content.strip(), "\n")
            else:
                with path.open("w", encoding="utf-8") as out:
                    out.write(content)
            created += 1

    print(f"Created: {created} sessions, Skipped: {skipped}")
    print(f"Target directory: {target_dir}")
    if args.dry_run:
        print("Dry-run only: no files written.")

if __name__ == "__main__":
    main()
