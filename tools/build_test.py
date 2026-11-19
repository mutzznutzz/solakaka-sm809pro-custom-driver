"""Build with a clean DLL search path, excluding unrelated tools on PATH."""
import os
import pathlib
import subprocess
import sys


def main():
    project = pathlib.Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    windows = pathlib.Path(env.get('SystemRoot', r'C:\Windows'))
    # Inherited Poppler/Conda/etc. paths can supply an incompatible icuuc.dll.
    # Let Windows resolve its OS DLLs and PyInstaller resolve Python/Qt locally.
    env['PATH'] = os.pathsep.join(str(p) for p in (
        pathlib.Path(sys.executable).parent, pathlib.Path(sys.base_prefix),
        windows/'System32', windows))
    return subprocess.call([sys.executable, '-m', 'PyInstaller', '--clean',
                            '--noconfirm', '--distpath', 'dist/wheel-fix-test-v2',
                            'SM809Pro.spec'], cwd=project, env=env)


if __name__ == '__main__':
    raise SystemExit(main())
