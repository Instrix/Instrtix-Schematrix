"""Rewrite README.md's relative links for PyPI, which shows the README without the repository around it.

    python packaging/pypi_readme.py v0.2.7      # images -> raw files at that tag, pages -> GitHub at that tag
"""
import re
import sys

REPO = 'https://github.com/Instrix/Instrtix-Schematrix'
RAW = 'https://raw.githubusercontent.com/Instrix/Instrtix-Schematrix'


def rewrite(text: str, ref: str) -> str:
    def link(m):
        bang, label, url = m.group(1), m.group(2), m.group(3)
        if re.match(r'[a-z]+:|#', url):
            return m.group(0)
        base = f'{RAW}/{ref}' if bang else f'{REPO}/blob/{ref}'
        return f'{bang}[{label}]({base}/{url})'
    return re.sub(r'(!?)\[([^\]]*)\]\(([^)\s]+)\)', link, text)


if __name__ == '__main__':
    ref = sys.argv[1] if len(sys.argv) > 1 else 'main'
    with open('README.md', encoding='utf-8') as f:
        text = f.read()
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(rewrite(text, ref))
