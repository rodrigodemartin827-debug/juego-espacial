#!/bin/bash
# Genera los modelos que aún no tienen JSON (es decir, sin terminar), de 6 en 6, y guarda y sube cada tanda.
# Se puede relanzar en cualquier momento: retoma donde se quedó.
cd "$(dirname "$0")"
RAIZ=..
LOG=${LOG:-$RAIZ/generacion.log}
guardar() {
  (cd ../../.. && rm -rf modelos/planeta_humano/*/_tmp_vistas && git add modelos/planeta_humano &&
   git commit -qm "feat(planeta humano): $1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014TTRpjRNrnBamiJ995yfrb" && git push -q origin HEAD) >> "$LOG" 2>&1
}
while true; do
  pend=$(python -c "
import generar, os
M = generar.cargar()
f = [n for n, i in sorted(M.items(), key=lambda x: x[1]['num']) if not os.path.exists(os.path.join('..', n, n + '.json'))]
print(' '.join(f[:6]))")
  [ -z "$pend" ] && break
  python generar.py $pend -j 3 >> "$LOG" 2>&1
  guardar "modelos: $pend"
done
echo "== FIN $(date)" >> "$LOG"
