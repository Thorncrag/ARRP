#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if command -v python3.12 >/dev/null 2>&1; then
  PYTHON=$(command -v python3.12)
elif [ -x /opt/homebrew/opt/python@3.12/bin/python3.12 ]; then
  PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12
else
  echo "Python 3.12 is required. On macOS, run: brew install python@3.12" >&2
  exit 1
fi

mkdir -p .tmp/cache/fontconfig .tmp/cache/pip
export PIP_CACHE_DIR="$ROOT/.tmp/cache/pip"

if [ ! -x .venv/bin/python ]; then
  "$PYTHON" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
fi
.venv/bin/python -m pip install --requirement requirements-local-tools.txt

missing=""
for command in pdftotext pdftoppm pdfinfo tesseract ocrmypdf qpdf gs pandoc node rg shellcheck exiftool; do
  if ! command -v "$command" >/dev/null 2>&1; then
    missing="$missing $command"
  fi
done

if [ -n "$missing" ]; then
  echo "Missing host commands:$missing" >&2
  echo "On macOS, install the supported toolchain with:" >&2
  echo "  brew install python@3.12 poppler tesseract ocrmypdf pandoc node ripgrep shellcheck exiftool" >&2
  exit 1
fi

echo "ARRP local tools are ready. Use .venv/bin/python for project Python commands."
echo "For sandboxed document commands, use PATH=\"/opt/homebrew/bin:\$PATH\" XDG_CACHE_HOME=\"\$PWD/.tmp/cache\"."
