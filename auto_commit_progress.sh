#!/bin/bash
cd /opt/garage_pro || exit 1
while true; do
    sleep 300
    git add -A 2>/dev/null || true
    git diff --cached --quiet 2>/dev/null || {
        git commit -m "🤖 Auto-save — $(date '+%Y-%m-%d %H:%M')" --no-verify 2>/dev/null || true
        git push origin main 2>/dev/null || true
    }
done
