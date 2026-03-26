#!/bin/bash
LAST=$(grep "✅" /opt/garage_pro/PROGRESS.md 2>/dev/null | tail -1)
[ -n "${NOTIFICATION_EMAIL:-}" ] && [ -n "$LAST" ] && command -v mail &>/dev/null && \
    echo "Agent terminé : $LAST" | mail -s "[Garage Pro] Progression" "$NOTIFICATION_EMAIL" 2>/dev/null || true
