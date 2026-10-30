"""Entry point for frozen builds: no arguments opens the editor window; any arguments go to the CLI."""
import sys

from schematrix.cli import main

if __name__ == '__main__':
    main(sys.argv[1:])
