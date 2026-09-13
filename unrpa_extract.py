#!/usr/bin/env python3

import os
import sys

from unrpa import UnRPA
from unrpa.errors import UnRPAError


def extract(path):
    """Extract an RPA archive into the directory that contains it.

    Returns a dict with the result of the operation.
    """
    path = os.path.abspath(path)
    out_dir = os.path.dirname(path)

    try:
        extractor = UnRPA(path, path=out_dir, mkdir=True)
        with open(path, "rb") as archive:
            names = sorted(extractor.get_index(archive).keys())
        extractor.extract_files()
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "path": path, "message": str(error)}

    files = []
    for name in names:
        target = os.path.join(out_dir, name)
        files.append(
            {
                "name": name,
                "path": target,
                "exists": os.path.isfile(target),
            }
        )

    return {
        "ok": True,
        "path": path,
        "dir": out_dir,
        "total": len(files),
        "files": files,
    }


def main():
    failed = 0
    for arg in sys.argv[1:]:
        result = extract(arg)
        if result["ok"]:
            print(
                f"OK {result['path']} -> {result['dir']} "
                f"({result['total']} archivo(s))"
            )
        else:
            failed += 1
            print(f"ERROR {result['path']}: {result['message']}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()