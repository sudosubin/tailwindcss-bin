from __future__ import annotations

import os
import sys

from tailwindcss_bin import find_tailwindcss_bin
from tailwindcss_bin._plugins import apply_node_path


def _run() -> None:
    apply_node_path()
    tailwindcss = find_tailwindcss_bin()

    if sys.platform == "win32":
        import subprocess

        # Avoid emitting a traceback on interrupt
        try:
            completed_process = subprocess.run(
                [tailwindcss, *sys.argv[1:]], check=False
            )
        except KeyboardInterrupt:
            sys.exit(2)

        sys.exit(completed_process.returncode)
    else:
        os.execvp(tailwindcss, [tailwindcss, *sys.argv[1:]])


if __name__ == "__main__":
    _run()
