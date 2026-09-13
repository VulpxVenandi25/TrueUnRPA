#!/usr/bin/env python3

import os
import sys

import webview

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unrpa_extract import extract as extract_archive


HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  :root {
    --bg: #1e1e2e;
    --panel: #27273a;
    --panel2: #2f2f45;
    --text: #e5e5ea;
    --muted: #9a9aa5;
    --accent: #7aa2f7;
    --ok: #9ece6a;
    --err: #f7768e;
    --border: #3b3b52;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, sans-serif;
    background: var(--bg); color: var(--text);
    padding: 28px; display: flex; flex-direction: column; gap: 18px;
    height: 100vh;
  }
  h1 { font-size: 22px; display: flex; align-items: center; gap: 10px; }
  h1 .dot { width: 12px; height: 12px; border-radius: 50%; background: var(--accent); display: inline-block; }
  .card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; padding: 18px;
  }
  .row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  button {
    background: var(--accent); color: #1e1e2e; border: none;
    padding: 10px 18px; border-radius: 8px; font-size: 14px;
    font-weight: 600; cursor: pointer;
  }
  button.secondary { background: var(--panel2); color: var(--accent); border: 1px solid var(--border); }
  button:disabled { opacity: 0.45; cursor: not-allowed; }
  #path { color: var(--muted); font-size: 13px; word-break: break-all; flex: 1; }
  #status { font-size: 13px; min-height: 18px; }
  #status.ok { color: var(--ok); }
  #status.err { color: var(--err); }
  #outputArea {
    flex: 1; overflow-y: auto; background: var(--panel);
    border: 1px solid var(--border); border-radius: 12px; padding: 16px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 13px; line-height: 1.7;
  }
  #outputArea .empty { color: var(--muted); }
  #outputArea .ok { color: var(--ok); }
  #outputArea .missing { color: var(--err); }
  #progress { display: none; }
</style>
</head>
<body>
  <h1><span class="dot"></span> unrpa — Extraer archivos RPA</h1>

  <div class="card row">
    <button id="pickBtn" disabled>Seleccionar archivo .rpa</button>
    <button id="extractBtn" class="secondary" disabled>Extraer</button>
    <span id="path">Ningún archivo seleccionado.</span>
  </div>

  <div id="status"></div>
  <div id="progress">Extrayendo…</div>

  <div id="outputArea"><span class="empty">El contenido del archivo se listará aquí.</span></div>

<script>
  let api = null;

  window.addEventListener('pywebviewready', function () {
    api = window.pywebview.api;
    document.getElementById('pickBtn').disabled = false;
  });

  async function setStatus(text, cls) {
    const el = document.getElementById('status');
    el.textContent = text;
    el.className = cls || '';
  }

  async function writeOutput(render) {
    const el = document.getElementById('outputArea');
    el.innerHTML = render;
  }

  document.getElementById('pickBtn').addEventListener('click', async function () {
    const path = await api.select_file();
    if (path) {
      document.getElementById('path').textContent = path;
      document.getElementById('extractBtn').disabled = false;
      await writeOutput('<span class="empty">Pulsé “Extraer” para extraerlo en su mismo directorio.</span>');
      await setStatus('');
    }
  });

  document.getElementById('extractBtn').addEventListener('click', async function () {
    const path = document.getElementById('path').textContent;
    const btn = this;
    btn.disabled = true;
    document.getElementById('pickBtn').disabled = true;
    document.getElementById('progress').style.display = 'block';
    await setStatus('');

    const result = await api.extract(path);

    document.getElementById('progress').style.display = 'none';
    btn.disabled = false;
    document.getElementById('pickBtn').disabled = false;

    if (!result.ok) {
      await setStatus('Error al extraer.', 'err');
      await writeOutput(
        '<div class="missing">' + result.message.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</div>'
      );
      return;
    }

    await setStatus(
      'Extracción completada: ' + result.total + ' archivo(s) en ' + result.dir,
      'ok'
    );
    const lines = result.files.map(function (f) {
      const mark = f.exists ? '<span class="ok">✔</span>' : '<span class="missing">✖</span>';
      return mark + '&nbsp; ' + f.name.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    }).join('<br>');
    await writeOutput(lines || '<span class="empty">El archivo no contenía archivos.</span>');
  });
</script>
</body>
</html>
"""


window: "webview.Window"


class Api:
    """Bridge between the webview interface and unrpa."""

    def select_file(self):
        result = window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Archivos RPA (*.rpa)", "Todos los archivos (*)"),
        )
        return result[0] if result else None

    def extract(self, path):
        if not path or path.startswith("Ningún archivo"):
            return {"ok": False, "message": "No se seleccionó ningún archivo."}

        result = extract_archive(path)
        return result


def main():
    global window

    window = webview.create_window(
        "unrpa — Extraer archivos RPA",
        html=HTML,
        js_api=Api(),
        width=780,
        height=640,
        min_size=(640, 480),
    )
    webview.start()


if __name__ == "__main__":
    main()