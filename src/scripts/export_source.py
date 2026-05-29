#!/usr/bin/env python3
# tools/source_processor.py

import io
import pathlib
import pyperclip

TOOLS_DIR = pathlib.Path(__file__).parent
ROOT = TOOLS_DIR.parent
STYLES_DIR = ROOT / "data" / "styles"

def collect_files() -> list[pathlib.Path]:
    files = sorted(ROOT.rglob("*.py"))
    return files

def process_file(path: pathlib.Path) -> str:
    content = path.read_text("utf-8")
    relative = path.relative_to(ROOT.parent).as_posix()
    comment = "#" if path.suffix == ".py" else "/*"
    closing = "" if path.suffix == ".py" else " */"
    lines = content.splitlines()
    if lines and lines[0].lstrip().startswith(comment[0]):
        lines[0] = f"{comment} {relative}{closing}"
    else:
        lines.insert(0, f"{comment} {relative}{closing}\n")
    return "\n".join(lines)

def main():
    buf = io.StringIO()
    files = collect_files()
    for path in files:
        buf.write(f'<file path="{path.relative_to(ROOT.parent).as_posix()}">\n')
        buf.write(process_file(path))
        buf.write("\n</file>\n")
    result = buf.getvalue()
    pyperclip.copy(result)
    print(f"Copied {len(files)} files to clipboard.")

if __name__ == "__main__":
    main()