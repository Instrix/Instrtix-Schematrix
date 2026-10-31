"""Cairo for PDF / PNG export on Windows and macOS, without asking anyone to install it.

The Windows and macOS downloads carry their own Cairo. A pip-installed Schematrix on a computer that has the app
but no system Cairo borrows the app's copy, so installing the app is all it takes. Must run before cairosvg /
cairocffi are imported (they look Cairo up once, through ctypes.util.find_library).
"""
import os
import sys

NAMES = ('cairo', 'cairo-2', 'libcairo-2')      # what cairocffi asks find_library for


def _app_cairo():
    if sys.platform == 'win32':          # the installer's per-user and all-users folders, and next to a portable zip
        roots = [os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'), os.environ.get('ProgramFiles', '')]
        found = [os.path.join(r, 'Schematrix', '_internal', 'libcairo-2.dll') for r in roots if r]
    elif sys.platform == 'darwin':
        found = [os.path.join(d, 'Schematrix.app', 'Contents', 'Frameworks', 'libcairo.2.dylib')
                 for d in ('/Applications', os.path.expanduser('~/Applications'))]
    else:
        return None                      # Linux: the system's libcairo2
    return next((f for f in found if os.path.isfile(f)), None)


def borrow_app_cairo():
    if sys.platform not in ('win32', 'darwin') or 'cairocffi' in sys.modules:
        return
    import ctypes.util
    find = ctypes.util.find_library
    if any(find(n) for n in NAMES):
        return                           # a system Cairo (or the app's own, inside the app): nothing to do
    lib = _app_cairo()
    if not lib:
        return
    if sys.platform == 'win32':          # the DLLs Cairo links to sit beside it
        os.add_dll_directory(os.path.dirname(lib))
        os.environ['PATH'] = os.path.dirname(lib) + os.pathsep + os.environ.get('PATH', '')
    ctypes.util.find_library = lambda name: lib if name in NAMES else find(name)
