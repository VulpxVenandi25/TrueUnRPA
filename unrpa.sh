#!/usr/bin/env bash

# Launcher de la interfaz gráfica (pywebview) de unrpa.
# Extrae archivos .rpa al mismo directorio donde se encuentra cada archivo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY="python3"
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
	PY="$SCRIPT_DIR/.venv/bin/python"

	# Asegura que pywebview esté instalado en el virtualenv.
	if ! "$PY" -c "import webview" >/dev/null 2>&1; then
		echo "Instalando pywebview en el virtualenv…"
		"$PY" -m pip install --quiet pywebview
	fi

	# La interfaz usa el backend GTK/WebKit del sistema (bindings PyGObject).
	# Si el virtualenv no los ve, activa los paquetes de sistema.
	if ! "$PY" -c "import gi" >/dev/null 2>&1; then
		sed -i 's/^include-system-site-packages = false/include-system-site-packages = true/' \
			"$SCRIPT_DIR/.venv/pyvenv.cfg" 2>/dev/null || true
		echo "Activados los paquetes de sistema en el virtualenv (backend GTK)."
	fi
else
	if ! "$PY" -c "import webview" >/dev/null 2>&1; then
		echo "pywebview no está instalado. Instálalo con: pip install pywebview" >&2
		echo "y asegura que Python tenga los bindings de GTK (PyGObject + WebKit2GTK)." >&2
		exit 1
	fi
fi

export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

exec "$PY" "$SCRIPT_DIR/unrpa_gui.py" "$@"