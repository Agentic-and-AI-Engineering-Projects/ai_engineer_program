#!/usr/bin/env bash
# Build a PDF from a markdown resume using pandoc + Chrome headless.
# Usage: ./_build_resume_pdf.sh <RESUME_FILE.md>
# Produces: <RESUME_FILE>.pdf with the same compression styling as the .docx
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "usage: $0 <resume.md>" >&2
    exit 1
fi

INPUT_MD="$1"
BASENAME="${INPUT_MD%.md}"
HTML_TMP="/tmp/${BASENAME##*/}.html"
PDF_OUT="${BASENAME}.pdf"
CSS_FILE="$(dirname "$0")/_resume_pdf.css"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 1. Markdown → standalone HTML with embedded CSS
pandoc "$INPUT_MD" -s --embed-resources --standalone -c "$CSS_FILE" -o "$HTML_TMP"

# 2. HTML → PDF via Chrome headless (no headers/footers, A4-ish letter)
"$CHROME" \
    --headless=new \
    --disable-gpu \
    --no-pdf-header-footer \
    --print-to-pdf="$PDF_OUT" \
    --print-to-pdf-no-header \
    --virtual-time-budget=2000 \
    "file://$HTML_TMP" 2>/dev/null

# 3. Clean up
rm -f "$HTML_TMP"

echo "PDF: $PDF_OUT"
