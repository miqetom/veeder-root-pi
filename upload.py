#!/usr/bin/env python3
"""
upload.py -- Send the local tank CSV to the SFTP server.
Per-store settings live in config.py.
"""

from pathlib import Path
import sys

import paramiko

import config


def upload():
    local_file = Path(config.CSV_PATH)

    if not local_file.exists():
        sys.exit(f"Local file not found: {local_file}")

    try:
        with paramiko.Transport((config.SFTP_HOST, config.SFTP_PORT)) as transport:
            transport.connect(username=config.SFTP_USER, password=config.SFTP_PASSWORD)
            with paramiko.SFTPClient.from_transport(transport) as sftp:
                sftp.put(str(local_file), config.REMOTE_FILE)
                print(f"OK: {local_file} -> {config.SFTP_HOST}:{config.REMOTE_FILE}")
    except Exception as exc:
        sys.exit(f"Upload failed: {exc}")


if __name__ == "__main__":
    upload()
