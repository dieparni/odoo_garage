#!/bin/bash
set -uo pipefail
PROJECT_DIR="/opt/garage_pro"
LOG="/var/log/garage_build.log"
MAX=100; DELAY=15; N=1
cd "$PROJECT_DIR"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }

INIT='Tu es l'\''architecte du projet Garage Pro (Odoo 17 — carrosserie/peinture/mécanique).

Specs dans `garage-odoo-specs/`, plan dans `garage-odoo-specs/CLAUDE_CODE_PLAN.md`, conventions dans `CLAUDE.md`.

Environnement : Odoo 17 CE local, commande `odoo`, DB `garage_test`, module dans garage_pro/.

Mission : construire garage_pro agent par agent (1→11). Pour chaque agent :
1. LIRE la spec dans garage-odoo-specs/modules/
2. IMPLÉMENTER modèles → vues → sécurité → données
3. TESTER : `odoo -d garage_test --test-enable --test-tags garage_pro --stop-after-init`
4. CHALLENGER avec un subagent reviewer
5. VALIDER : `odoo -d garage_test -u garage_pro --stop-after-init`
6. Mettre à jour PROGRESS.md

Règles : lire la spec avant de coder, _inherit pour les natifs, corriger le code si test fail, notes détaillées dans PROGRESS.md si limite contexte.

Commence : lis PROGRESS.md, CLAUDE.md, le plan, puis lance l'\''agent suivant.'

RESUME='Reprends Garage Pro. Lis PROGRESS.md en premier — il dit où tu en es. Termine les modules 🔧 avant d'\''en commencer un nouveau. Ne recommence jamais un ✅. Odoo : `odoo -d garage_test -u garage_pro --stop-after-init`. Mets à jour PROGRESS.md à la fin.'

P="$INIT"
grep -q "Agent [0-9].*✅" "$PROJECT_DIR/PROGRESS.md" 2>/dev/null && P="$RESUME" && log "Mode reprise"

while [ $N -le $MAX ]; do
    log "=== Session #${N}/${MAX} ==="
    grep -q "Agent 10.*✅" "$PROJECT_DIR/PROGRESS.md" 2>/dev/null && { log "🎉 TERMINÉ"; break; }

    set +e
    claude -p "$P" \
        --allowedTools "Read,Write,Edit,Bash(odoo*:xmllint*:python*:flake8*:grep*:find*:ls*:cat*:head*:tail*:wc*:diff*:mkdir*:cp*:mv*:touch*:psql*:pip*:cd*:echo*:sed*:awk*:sort*:tree*:git*)" \
        --verbose 2>&1 | tee -a "$LOG"
    EC=$?; set -e
    log "Exit: $EC"

    cd "$PROJECT_DIR"
    git add -A 2>/dev/null || true
    git diff --cached --quiet 2>/dev/null || {
        git commit -m "🤖 Session #${N} — $(date '+%H:%M')" --no-verify 2>/dev/null || true
        git push origin main 2>/dev/null || true
    }

    TAIL=$(tail -30 "$LOG" 2>/dev/null)
    echo "$TAIL" | grep -qi "rate.* limit\|429\|overloaded\|529" && DELAY=60
    echo "$TAIL" | grep -qi "timeout\|timed out" && DELAY=30
    log "Pause ${DELAY}s..."; sleep $DELAY; DELAY=15

    P="$RESUME"; N=$((N+1))
done
log "Runner terminé (${N} sessions)"
