#!/usr/bin/env bash
# =============================================================================
#  install.sh -- One-command setup for the Veeder-Root capture/upload service.
#
#  Run from the cloned repo directory with sudo:
#      sudo ./install.sh
#  (or, if it won't execute:  sudo bash install.sh )
#
#  It will:
#    1. Install system packages (python3, venv, pip).
#    2. Create config.py from the template on first run.
#    3. Create a local Python venv and install pyserial + paramiko.
#    4. Add the invoking user to the 'dialout' group (serial port access).
#    5. Install an hourly systemd timer that runs capture + upload.
# =============================================================================
set -euo pipefail

# --- Must be root ------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run with sudo:  sudo ./install.sh" >&2
    exit 1
fi

# --- Figure out who and where -----------------------------------------------
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"

echo "Install dir : $INSTALL_DIR"
echo "Service user: $RUN_USER"
echo

# --- 1. System packages ------------------------------------------------------
echo "==> Installing system packages..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip

# --- 2. First-run config -----------------------------------------------------
if [ ! -f "$INSTALL_DIR/config.py" ]; then
    echo "==> Creating config.py from template (edit it after install)..."
    cp "$INSTALL_DIR/config.example.py" "$INSTALL_DIR/config.py"
    chown "$RUN_USER":"$RUN_USER" "$INSTALL_DIR/config.py"
else
    echo "==> config.py already exists, leaving it as-is."
fi

# --- 3. Python venv + deps ---------------------------------------------------
echo "==> Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

chmod +x "$INSTALL_DIR/run.sh" "$INSTALL_DIR/install.sh" || true
chown -R "$RUN_USER":"$RUN_USER" "$INSTALL_DIR/.venv"

# --- 4. Serial port access ---------------------------------------------------
echo "==> Adding $RUN_USER to 'dialout' group for serial access..."
usermod -aG dialout "$RUN_USER" || true

# --- 5. systemd service + timer (generated here, no extra files needed) ------
echo "==> Installing systemd service and hourly timer..."

cat > /etc/systemd/system/veeder-capture.service <<UNIT
[Unit]
Description=Veeder-Root tank capture and SFTP upload
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/env bash $INSTALL_DIR/run.sh
UNIT

cat > /etc/systemd/system/veeder-capture.timer <<'UNIT'
[Unit]
Description=Run Veeder-Root capture+upload hourly

[Timer]
OnCalendar=hourly
Persistent=true
OnBootSec=2min

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now veeder-capture.timer

echo
echo "============================================================"
echo " Done."
echo
echo " IMPORTANT: set the store name, serial port, and SFTP"
echo "            password before relying on it:"
echo "     nano $INSTALL_DIR/config.py"
echo
echo " Useful commands:"
echo "   Run once now:      sudo systemctl start veeder-capture.service"
echo "   View last run:     journalctl -u veeder-capture.service -n 50 --no-pager"
echo "   Timer schedule:    systemctl list-timers veeder-capture.timer"
echo
echo " NOTE: the dialout group change takes effect after the user"
echo "       logs out/in or the Pi reboots."
echo "============================================================"
