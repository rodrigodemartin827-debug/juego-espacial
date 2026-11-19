#!/bin/bash
# Espera a que termine el proceso $1 y luego genera en cola el resto de modelos.
while kill -0 "$1" 2>/dev/null; do sleep 15; done
shift
exec ./lote.sh "$@"
