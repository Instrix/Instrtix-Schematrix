"""Entry point for frozen builds: no arguments opens the editor window; any arguments go to the CLI."""
import os
import sys

# Windows and macOS builds carry their own Cairo (for PDF / PNG export). cairocffi looks it up with
# ctypes.util.find_library, which does not search the bundle: point it there before anything imports it.
if getattr(sys, 'frozen', False) and sys.platform in ('win32', 'darwin'):
    import ctypes.util
    _here = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    _cairo = os.path.join(_here, 'libcairo-2.dll' if sys.platform == 'win32' else 'libcairo.2.dylib')
    if os.path.exists(_cairo):
        _find = ctypes.util.find_library
        ctypes.util.find_library = lambda name: _cairo if name in ('cairo', 'cairo-2', 'libcairo-2') else _find(name)
        if sys.platform == 'win32':
            os.add_dll_directory(_here)                                  # the DLLs Cairo itself links to
            os.environ['PATH'] = _here + os.pathsep + os.environ.get('PATH', '')

from schematrix.cli import main  # noqa: E402

if __name__ == '__main__':
    main(sys.argv[1:])
