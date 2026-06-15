#!/usr/bin/env bash
# Compila la relazione in PDF (due passate per ToC e riferimenti).
# Uso: ./build.sh   (dalla cartella relazione/)
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null
# pulizia file ausiliari
rm -f main.aux main.log main.out main.toc capitoli/*.aux
echo "OK -> $(pwd)/main.pdf"
