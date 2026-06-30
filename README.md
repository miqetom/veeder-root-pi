# veeder-root-pi

Raspberry Pi tooling to poll a **Veeder-Root TLS-350** ATG over serial, write
tank inventory to a CSV, and SFTP it to the central server. Designed so a fresh
Pi can be set up with **one command**.

## What's in here

| File | Purpose |
|------|---------|
| `config.example.py` | Template of all settings. `install.sh` copies it to `config.py`. |
| `config.py` | **Your real per-store settings** — created on first install, git-ignored so credentials never reach GitHub. |
| `capture.py` | Reads the TLS-350 over serial and writes the tank CSV. |
| `upload.py` | Uploads the CSV to the SFTP server (`paramiko`). |
| `run.sh` | Runs capture, waits, then uploads. |
| `install.sh` | Installs dependencies + an hourly systemd timer. |
| `requirements.txt` | Python deps (`pyserial`, `paramiko`). |
| `systemd/` | Service + timer templates. |

## Install on a new Raspberry Pi

Connect the Pi to the Veeder-Root via the USB-serial adapter, then run:

```bash
git clone https://github.com/YOURUSER/veeder-root-pi.git
cd veeder-root-pi
sudo ./install.sh
```

That installs `pyserial` + `paramiko` into a local virtual environment, grants
the user serial-port access, and enables an **hourly** systemd timer.

No GitHub login is needed on the Pi as long as the repo is public. Credentials
are **not** stored in the repo — you enter them in `config.py` after install.

## Configure the store

`install.sh` creates `config.py` from the template. Edit it for this location,
then reboot (or run once manually):

```bash
nano config.py
```

Set at minimum:

- `STORE_NAME` — used to build the remote path `/fuel/<STORE_NAME>/<STORE_NAME>TABLE.csv`
- `SERIAL_PORT` — confirm with `ls /dev/ttyUSB*`
- `SFTP_PASSWORD` — the template ships with a placeholder; put the real password here

## Run / check it

```bash
# Trigger a capture+upload right now
sudo systemctl start veeder-capture.service

# See the result of the last run
journalctl -u veeder-capture.service -n 50 --no-pager

# Confirm the hourly schedule
systemctl list-timers veeder-capture.timer
```

## Notes

- The hourly timer uses `Persistent=true`, so if the Pi is powered off it will
  catch up the next time it boots.
- `config.py` is git-ignored, so credentials stay on the Pi and never get
  pushed. The repo only contains `config.example.py` with a placeholder
  password — safe to keep public.
- The `dialout` group change applies after the next login/reboot.
