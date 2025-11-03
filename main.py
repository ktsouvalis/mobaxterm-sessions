#!/usr/bin/env python3
import os
import re
import sys
import argparse
from pathlib import Path
from typing import NamedTuple

# paths
HOME = str(Path.home())

class Entry(NamedTuple):
    name: str
    protocol: str
    host: str
    port: str
    user: str
    key_path: str

# Allow overriding the source file via --file / -f (defaults to ./moba_bookmarks.txt)
parser = argparse.ArgumentParser(description="Convert MobaXterm bookmarks to Remmina profiles.")
parser.add_argument(
    "--file", "-f",
    dest="src_file",
    default="./moba_bookmarks.txt",
    help="Path to MobaXterm bookmarks export (default: ./moba_bookmarks.txt)",
)
parser.add_argument(
    "--dry-run", "-n",
    action="store_true",
    help="Preview actions without creating any files",
)
args = parser.parse_args()

SRC_FILE = args.src_file
DEST_DIR = f"{HOME}/.local/share/remmina"
DRY_RUN = args.dry_run

# Validate input file exists for a clearer error message
if not os.path.isfile(SRC_FILE):
    print(f"Error: input file not found: {SRC_FILE}", file=sys.stderr)
    sys.exit(1)

# Only create destination directory when not in dry-run mode
if not DRY_RUN:
    os.makedirs(DEST_DIR, exist_ok=True)

current_group = None

# This regex splits the right-hand side of each entry by '%'
# Example right side:
# "#109#0%10.57.1.10%22%root%%-1%-1%%%%%0%0%0%%%-1%..."
# We mainly care about:
#   index 0 -> "#109#0"   (type code)
#   index 1 -> host/IP
#   index 2 -> port
#   index 3 -> username
#   index 8 -> maybe key path (ex: "_ProfileDir_\.ssh\id_ed25519")
#
# We'll try to be defensive if fields are missing.

def parse_line(name: str, rhs: str) -> Entry:
    parts = rhs.split('%')

    # protocol guess from parts[0]
    proto_code = parts[0] if parts else "#109#0"  # default to SSH-ish
    if proto_code.startswith("#109"):
        protocol = "SSH"
        port_default = "22"
    elif proto_code.startswith("#98"):
        # Those look like telnet-ish (port 23 in your dump)
        protocol = "TELNET"
        port_default = "23"
    else:
        protocol = "SSH"
        port_default = "22"

    host = parts[1] if len(parts) > 1 and parts[1] else ""
    port = parts[2] if len(parts) > 2 and parts[2] else port_default
    user = parts[3] if len(parts) > 3 and parts[3] else ""

    # key path detection:
    key_path = ""
    # search all parts for something containing ".ssh"
    for p in parts:
        if ".ssh" in p or "\\.ssh" in p:
            key_path = p
            break

    # normalize key path if found
    if key_path:
        key_path = key_path.replace("_ProfileDir_\\", "")
        key_path = key_path.replace("\\", "/")
        if not key_path.startswith("/"):
            key_path = f"{HOME}/{key_path}"

    return Entry(
        name=name.strip(),
        protocol=protocol,
        host=host.strip(),
        port=port.strip(),
        user=user.strip(),
        key_path=key_path.strip(),
    )

with open(SRC_FILE, "r", encoding="utf-8") as f:
    for raw_line in f:
        line = raw_line.rstrip("\n")

        # Skip blank and comment lines
        if not line or line.lstrip().startswith("#"):
            continue

        # Detect group blocks like:
        # [Bookmarks_1]
        # SubRep=Servers
        if line.startswith("[Bookmarks_"):
            current_group = None
            continue

        if line.startswith("SubRep="):
            current_group = line.split("=",1)[1].strip()
            continue

        # skip ImgNum, blank, etc
        if line.startswith("ImgNum="):
            continue

        # Match "name=rest"
        if "=" in line:
            name, rhs = line.split("=", 1)

            data = parse_line(name, rhs)

            # Build .remmina file content
            # Remmina wants lowercase keys except "name"
            remmina_lines = []
            remmina_lines.append("[remmina]")

            # protocol:
            # SSH or TELNET
            if data.protocol == "SSH":
                remmina_lines.append("protocol=SSH")
            elif data.protocol == "TELNET":
                remmina_lines.append("protocol=TELNET")
            else:
                remmina_lines.append("protocol=SSH")

            # visible name
            disp_name = data.name
            if current_group:
                disp_name = f"{current_group}/{disp_name}"

            remmina_lines.append(f"name={disp_name}")
            remmina_lines.append(f"group={current_group if current_group else ''}")

            # server, username, port
            remmina_lines.append(f"server={data.host}")
            if data.user:
                remmina_lines.append(f"username={data.user}")
            if data.port:
                remmina_lines.append(f"port={data.port}")

            if data.protocol == "SSH":
                # auth mode
                if data.key_path:
                    remmina_lines.append("ssh_auth=1")
                    remmina_lines.append(f"ssh_privatekey={data.key_path}")
                else:
                    remmina_lines.append("ssh_auth=0")

            # minimal extras so Remmina is happy
            remmina_lines.append("disablepasswordstorage=0")
            remmina_lines.append("notes=")

            # write file
            # sanitize filename
            safe_filename = re.sub(r'[^A-Za-z0-9._-]+', "_", data.name)
            outfile = os.path.join(DEST_DIR, safe_filename + ".remmina")

            if DRY_RUN:
                print(f"[dry-run] Would write {outfile}")
            else:
                with open(outfile, "w", encoding="utf-8") as out:
                    out.write("\n".join(remmina_lines) + "\n")
                print(f"Wrote {outfile}")
