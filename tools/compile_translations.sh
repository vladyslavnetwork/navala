#!/bin/sh
# Компілює po/*.po у src/navala/locale/<мова>/LC_MESSAGES/navala.mo
# Потрібен пакет gettext:  sudo apt install gettext
set -e
cd "$(dirname "$0")/.."
for po in po/*.po; do
    lang=$(basename "$po" .po)
    mkdir -p "src/navala/locale/$lang/LC_MESSAGES"
    msgfmt --check -o "src/navala/locale/$lang/LC_MESSAGES/navala.mo" "$po"
    echo "  $lang: OK"
done
