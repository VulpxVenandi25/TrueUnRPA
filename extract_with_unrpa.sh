#!/usr/bin/env bash

# Extrae uno o varios archivos .rpa a su mismo directorio.
# Pensado para usarse desde el menú contextual de Nemo (acción "Extraer con UnRPA").

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY="python3"
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
	PY="$SCRIPT_DIR/.venv/bin/python"
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

if [ "$#" -eq 0 ]; then
	echo "Uso: $0 archivo.rpa [archivo2.rpa ...]" >&2
	exit 1
fi

failed=0
for file in "$@"; do
	echo ""
	echo "=== $file ==="
	if ! "$PY" "$SCRIPT_DIR/unrpa_extract.py" "$file"; then
		failed=1
	fi
done

if command -v notify-send >/dev/null 2>&1; then
	if [ "$failed" -eq 0 ]; then
		notify-send -i folder-sync-symbolic \
			"UnRPA: extracción completada" \
			"$(echo "$@" | tr ' ' '\n' | sed 's|.*/||' | tr '\n' ' ')"
	else
		notify-send -i dialog-error "UnRPA" "Hubo errores al extraer alguno de los archivos."
	fi
fi

exit "$failed"