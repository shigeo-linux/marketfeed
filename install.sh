#!/bin/bash
set -e

APP_NAME="marketfeed"
INSTALL_DIR="/opt/${APP_NAME}"
DESKTOP_DIR="/usr/share/applications"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installing ${APP_NAME} ==="

sudo apt-get update -qq
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-requests python3-venv

echo "Copying application files..."
sudo mkdir -p "${INSTALL_DIR}"
sudo cp -r "$(dirname "$0")"/* "${INSTALL_DIR}/"
sudo chmod +x "${INSTALL_DIR}/marketfeed.py"
sudo chmod +x "${INSTALL_DIR}/runner.py"

echo "Creating virtual environment..."
sudo python3 -m venv --system-site-packages "${INSTALL_DIR}/venv"
sudo "${INSTALL_DIR}/venv/bin/pip" install --quiet feedparser yfinance

echo "Installing icon..."
sudo mkdir -p /usr/share/icons/hicolor/scalable/apps
sudo cp "${INSTALL_DIR}/marketfeed.svg" /usr/share/icons/hicolor/scalable/apps/marketfeed.svg
sudo gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true

echo "Installing desktop entry..."
sudo cp "${INSTALL_DIR}/marketfeed.desktop" "${DESKTOP_DIR}/"
sudo update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true

echo "Creating launcher..."
sudo tee /usr/local/bin/marketfeed > /dev/null << 'EOF'
#!/bin/bash
exec /opt/marketfeed/venv/bin/python3 /opt/marketfeed/marketfeed.py "$@"
EOF
sudo chmod +x /usr/local/bin/marketfeed

echo "Creating config directory..."
mkdir -p "$HOME/.config/${APP_NAME}"

echo "Installing systemd user timer..."
mkdir -p "${SYSTEMD_USER_DIR}"
cp "${INSTALL_DIR}/marketfeed.service" "${SYSTEMD_USER_DIR}/marketfeed.service"
cp "${INSTALL_DIR}/marketfeed.timer"   "${SYSTEMD_USER_DIR}/marketfeed.timer"
sudo loginctl enable-linger "$(whoami)"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
if systemctl --user daemon-reload 2>/dev/null; then
    systemctl --user enable marketfeed.timer
    systemctl --user start marketfeed.timer
else
    echo "Note: Timer files installed. Run 'systemctl --user enable --now marketfeed.timer' after logging in."
fi

echo ""
echo "=== Installation complete! ==="
echo "Run: marketfeed"
