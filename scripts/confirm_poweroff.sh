#!/usr/bin/env bash
set -euo pipefail

TITLE="Power Off Pi"
MESSAGE="Power off the Raspberry Pi now?"

confirm_with_zenity() {
  zenity --question --title="$TITLE" --text="$MESSAGE"
}

confirm_with_xmessage() {
  xmessage -center -title "$TITLE" -buttons "Cancel:1,Power off:0" "$MESSAGE"
}

confirm_with_tk() {
  python3 - "$TITLE" "$MESSAGE" <<'PY'
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

title, message = sys.argv[1], sys.argv[2]
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
confirmed = messagebox.askyesno(title, message, default=messagebox.NO)
root.destroy()
raise SystemExit(0 if confirmed else 1)
PY
}

confirm_with_terminal() {
  printf "%s [y/N] " "$MESSAGE"
  read -r answer
  case "$answer" in
    y|Y|yes|YES)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if command -v zenity >/dev/null 2>&1; then
  confirm_with_zenity
elif command -v python3 >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
  confirm_with_tk
elif command -v xmessage >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
  confirm_with_xmessage
else
  confirm_with_terminal
fi

systemctl poweroff
