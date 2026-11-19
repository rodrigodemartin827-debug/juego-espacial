#!/bin/bash
# Genera en cola los modelos pasados (uno detrás de otro) y deja el registro en $LOG.
cd "$(dirname "$0")"
for n in "$@"; do /tmp/claude-0/venv/bin/python generar.py "$n" 2>&1 | grep -E "^   [a-z_]+:|Error|Trace|line [0-9]+|SystemExit|presupuesto|normales" ; done
