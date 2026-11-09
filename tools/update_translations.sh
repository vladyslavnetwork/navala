#!/bin/sh
# Оновлює шаблон po/navala.pot з коду та підтягує нові рядки в усі po/*.po
set -e
cd "$(dirname "$0")/.."
xgettext --language=Python --keyword=_ --from-code=UTF-8 \
    --package-name=navala -o po/navala.pot src/navala/*.py
for po in po/*.po; do
    msgmerge --update --backup=none "$po" po/navala.pot
done
