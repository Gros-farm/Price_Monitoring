#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT_PATH="$ROOT/scripts/agents/update_auchan_and_push.sh"
PLIST_PATH="$HOME/Library/LaunchAgents/com.grosfarm.price-monitor.auchan-agent.plist"
LOG_DIR="$ROOT/logs"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
chmod +x "$SCRIPT_PATH"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.grosfarm.price-monitor.auchan-agent</string>

  <key>ProgramArguments</key>
  <array>
    <string>$SCRIPT_PATH</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$ROOT</string>

  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key>
      <integer>6</integer>
      <key>Minute</key>
      <integer>10</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>12</integer>
      <key>Minute</key>
      <integer>10</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>18</integer>
      <key>Minute</key>
      <integer>10</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>23</integer>
      <key>Minute</key>
      <integer>10</integer>
    </dict>
  </array>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/auchan-agent.out.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/auchan-agent.err.log</string>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

echo "Installed Auchan schedule:"
echo "  06:10, 12:10, 18:10, 23:10 local time"
echo "Plist:"
echo "  $PLIST_PATH"
echo "Logs:"
echo "  $LOG_DIR/auchan-agent.out.log"
echo "  $LOG_DIR/auchan-agent.err.log"
