# unrpa - Extrae archivos del formato de archivo RPA.

[![PyPI](https://img.shields.io/pypi/v/unrpa)](https://pypi.org/project/unrpa/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/unrpa)](https://www.python.org/)
[![GitHub](https://img.shields.io/github/license/Lattyware/unrpa)](https://github.com/Lattyware/unrpa/blob/master/COPYING)
[![MyPy Check](https://github.com/Lattyware/unrpa/workflows/MyPy%20Check/badge.svg)](https://github.com/Lattyware/unrpa/actions?query=workflow%3A%22MyPy+Check%22)

## Acerca de

unrpa es una herramienta para extraer archivos del formato de archivo RPA
(del [motor de novelas visuales Ren'Py](http://www.renpy.org/)).

Un archivo RPA almacena un índice (comprimido con zlib y serializado con pickle)
de los archivos que contiene, seguido de los datos de esos archivos. Las distintas
versiones del formato usan formas diferentes de guardar el offset y (en algunos
casos) la clave de ofuscación necesarios para leer ese índice - unrpa sabe
detectar la versión de un archivo y leerlo automáticamente.

También se puede usar como una biblioteca (por ejemplo, para leer archivos sin
extraerlos o para dar soporte a nuevas versiones).

### Versiones soportadas

| Versión | Tipo                                          |
| ------- | --------------------------------------------- |
| RPA-1.0 | Oficial (`.rpi`, sin codificación del índice) |
| RPA-2.0 | Oficial                                       |
| RPA-3.0 | Oficial (ofuscado)                            |
| RPA-3.2 | Variante no oficial de RPA-3.0                |
| RPA-4.0 | Variante no oficial de RPA-3.0                |
| ALT-1.0 | Versión alternativa de RPA-3.0                |
| ZiX-12A | Propietario, ofuscado                         |
| ZiX-12B | Propietario, ofuscado                         |

## Cómo funciona

### Estructura de un archivo RPA

Un archivo RPA se compone de tres partes:

1. **Cabecera**: primera línea de texto que indica la versión y, según la
   versión, el *offset* (posición) donde empieza el índice y una *clave* de
   ofuscación, ambos en hexadecimal. Por ejemplo: `RPA-3.0 0x1A2B 0x3C4D`.
   Los archivos RPA-1.0 se detectan por su extensión (`.rpi`) y no tienen
   cabecera ni índice codificado.
2. **Índice**: un objeto Python (diccionario `ruta → entrada`) serializado con
   `pickle` y comprimido con `zlib`, situado en el offset indicado por la
   cabecera. Cada entrada describe dónde vive cada archivo: un offset y una
   longitud dentro del archivo, y opcionalmente un prefijo (bytes que se
   guardan directamente en el índice, habitual en archivos muy pequeños).
3. **Datos**: los contenidos de los archivos, almacenados a continuación.

### Flujo de extracción

El programa sigue estos pasos (`unrpa/__init__.py`):

1. **Detección de versión** (`detect_version()`): lee la primera línea del
   archivo y la compara contra cada versión conocida. Cada versión sabe
   detectarse a sí misma: RPA-1.0 por extensión (`ExtensionBasedVersion`) y las
   demás por su cabecera (`HeaderBasedVersion`). Si ninguna coincide, falla con
   `UnknownArchiveError`; si coinciden varias, con `AmbiguousArchiveError`.
   Cada versión vive en `unrpa/versions/` (`official_rpa.py`, `unofficial_rpa.py`,
   `alt.py`, `zix.py`).
2. **Offset y clave** (`find_offset_and_key()`): la versión detectada sabe leer
   su propia cabecera para obtener el offset y la clave. Los formatos ZiX-12A y
   ZiX-12B son especiales: la clave no está en la cabecera, sino escondida en el
   archivo `loader.pyo` del juego, por lo que se descompila con `uncompyle6`
   (dependencia opcional) para recuperarla.
3. **Lectura del índice** (`get_index()`): se posiciona en el offset, se lee el
   bloque hasta el final, se descomprime con `zlib` y se deserializa con
   `pickle`. Si hay clave, cada entrada (offset y longitud) se "desofusca"
   aplicando una XOR con ella (`deobfuscate_index()`); si no la hay, las
   entradas se normalizan tal cual.
4. **Extracción** (`extract_files()`): para cada entrada del índice se crea un
   `ArchiveView` (`unrpa/view.py`), un objeto con comportamiento de archivo que
   solo deja leer el tramo exacto del archivo RPA (offset + longitud, y el
   prefijo si existe). El contenido se escribe en el disco como cada archivo, y
   `postprocess()` permite a algunas versiones transformar los datos antes de
   guardarlos (p. ej. ZiX-12B vuelve a ofuscar con su propio algoritmo).

Tanto la línea de comandos, como la interfaz gráfica (`unrpa_gui.py`) y el
script de menú contextual (`extract_with_unrpa.sh`) usan exactamente esta
misma lógica a través de la clase `UnRPA`.

## Instalación

### Gestor de paquetes

La mejor forma de instalar unrpa es a través de tu gestor de paquetes, si hay un
paquete disponible para tu sistema operativo. Mantengo
[un paquete de AUR](https://aur.archlinux.org/packages/unrpa/) para usuarios de
Arch Linux.

### pip

También puedes instalar unrpa a través de pip, el gestor de paquetes de Python.
Puedes hacerlo en Windows con:

    py -3 -m pip install "unrpa"

O usa `python3` en lugar de `py -3` en sistemas unix. Puedes consultar
[la documentación oficial](https://packaging.python.org/tutorials/installing-packages/)
para más ayuda sobre cómo instalar a través de pip.

### Desde el código fuente

También puedes
[descargar la última versión](https://github.com/Lattyware/unrpa/releases/latest)
y extraerla.

## Requisitos

Necesitarás Python 3.7 o posterior para ejecutarlo (instálalo a través de tu
gestor de paquetes o
[directamente desde python.org](https://www.python.org/downloads/)).

Si intentas extraer archivos RPA más exóticos, puede haber dependencias
adicionales. unrpa debería indicarte cómo instalarlas si son necesarias. Por
ejemplo, los archivos ZiX requieren `uncompyle6`, que se puede instalar con:

    pip install "unrpa[ZiX]"

Los mantenedores de paquetes pueden consultar
[`setup.py`](https://github.com/Lattyware/unrpa/blob/master/setup.py) para ver el
conjunto completo de dependencias.

### Ejemplos

Cuando esté instalado a través de tu gestor de paquetes o pip, deberías poder usar
unrpa abriendo una terminal o el símbolo del sistema y haciendo algo como:

    unrpa -mp "ruta/al/directorio/de/salida" "ruta/al/archivo.rpa"

Si lo ejecutas desde el código fuente, tendrás que llamar a python directamente:

- En la mayoría de sistemas unix, abre una terminal en el directorio que contiene
  unrpa y luego:

      python3 -m unrpa -mp "ruta/al/directorio/de/salida" "ruta/al/archivo.rpa"

- En la mayoría de sistemas Windows, abre un símbolo del sistema en el directorio
  que contiene unrpa y luego:

  py -3 -m unrpa -mp "ruta/al/directorio/de/salida" "ruta/al/archivo.rpa"

## Uso desde la línea de comandos

```
usage: unrpa [-h] [-v] [-s] [-l | -t] [-p PATH] [-m] [--version]
             [--continue-on-error] [-f VERSION] [-o OFFSET] [-k KEY]
             FILENAME [FILENAME ...]
```

### Opciones

| Argumento posicional | Descripción                   |
| -------------------- | ----------------------------- |
| FILENAME             | el(los) archivo(s) a extraer. |

| Argumento opcional   | Descripción                                                                           |
| -------------------- | ------------------------------------------------------------------------------------- |
| -h, --help           | muestra este mensaje de ayuda y sale                                                  |
| -v, --verbose        | explica lo que se está haciendo, repítelo para más detalle (predeterminado: 1).       |
| -s, --silent         | sin salida no esencial.                                                               |
| -l, --list           | lista el contenido del(los) archivo(s) en una lista plana.                            |
| -t, --tree           | lista el contenido del(los) archivo(s) en una vista de árbol.                         |
| -p PATH, --path PATH | extrae los archivos a la ruta dada (predeterminado: el directorio de trabajo actual). |
| -m, --mkdir          | crea cualquier directorio que falte en la ruta de extracción dada.                    |
| --version            | muestra el número de versión del programa y sale                                      |

| Argumento avanzado          | Descripción                                                                                                                                             |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| --continue-on-error         | intenta continuar la extracción cuando algo sale mal.                                                                                                   |
| -f VERSION, --force VERSION | ignora la cabecera del archivo y asume esta versión exacta. Versiones posibles: RPA-1.0, RPA-2.0, RPA-3.0, ALT-1.0, ZiX-12A, ZiX-12B, RPA-3.2, RPA-4.0. |
| -o OFFSET, --offset OFFSET  | ignora la cabecera del archivo y usa este offset exacto.                                                                                                |
| -k KEY, --key KEY           | ignora la cabecera del archivo y usa esta clave exacta.                                                                                                 |

Nota: si usas `--offset` o `--key`, debes usar ambos.

## Uso como biblioteca

unrpa se puede usar desde tu propio código Python. La clase `UnRPA` acepta las
mismas opciones que la herramienta de línea de comandos:

```python
from unrpa import UnRPA

extractor = UnRPA("ruta/al/archivo.rpa", path="ruta/de/salida", mkdir=True)
extractor.extract_files()
```

Para inspeccionar el contenido de un archivo sin extraerlo, llama a `list_files()`
o a `list_files_tree()`. El método `tree()` devuelve el contenido de un archivo
como un objeto `TreeNode`, que puedes recorrer tú mismo.

Solo se admiten llamadas sucesivas a `extract_files()` por instancia de `UnRPA`:
crea una nueva instancia para cada archivo.

## Interfaz gráfica y accesos rápidos

Además de la línea de comandos, el proyecto incluye una interfaz gráfica y un
acceso directo para el gestor de archivos:

- **Interfaz gráfica (pywebview)** — `unrpa.sh` abre una ventana para
  seleccionar un archivo `.rpa` (o varios) y extraerlos a su mismo directorio.
  El lanzador prepara el entorno automáticamente (instala `pywebview` en el
  virtualenv si falta y activa los paquetes de sistema para el backend GTK).

      ./unrpa.sh

- **Acción de Nemo «Extraer con UnRPA»** — `extract_with_unrpa.sh` extrae cada
  archivo elegido con el botón derecho a su propio directorio y muestra una
  notificación del resultado. El archivo
  `~/.local/share/nemo/actions/unrpa.nemo_action` registra la opción en el menú
  contextual de los archivos `.rpa` de Nemo (el gestor de archivos de Cinnamon).
  Si el menú no aparece, reinicia Nemo con `nemo -q`.

Ambos usan la misma lógica compartida en `unrpa_extract.py`.

## Errores

### Errores comunes

- Comprueba que usas la última versión de Python 3.
- Comprueba que usas comillas alrededor de las rutas de los archivos.
- Las guías en vídeo pueden estar desactualizadas; consulta este archivo para
  recibir consejos actualizados sobre el uso de la herramienta.
- Si el archivo es una variante nueva o inusual, consulta los argumentos
  avanzados (`--force`, `--offset`/`--key`, `--continue-on-error`) que se indican
  arriba.

### Errores nuevos

Si algo sale mal al extraer un archivo, por favor
[crea un issue](https://github.com/Lattyware/unrpa/issues/new).

Se crean nuevas variantes del formato RPA con regularidad, así que los juegos
nuevos pueden no funcionar; normalmente el soporte se puede añadir rápidamente.

## Desarrollo

Para ejecutar el proyecto desde una copia del repositorio, instala las
dependencias e invócalo a través de Python:

    python3 -m unrpa --help

El proyecto usa [mypy](http://mypy-lang.org/) para la comprobación estática de
tipos (la configuración está en `mypy.ini`), y se ejecuta automáticamente en cada
push y pull request mediante una GitHub Action. Puedes ejecutarlo localmente con:

    mypy --config-file mypy.ini -punrpa

Las contribuciones, issues y sugerencias son bienvenidos a través de
[GitHub](https://github.com/Lattyware/unrpa).
