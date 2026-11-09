# Navala / Навала

Ретро-аркада в дусі класичних ігор кінця 1970-х: хвилі прибульців марширують донизу,
ти ховаєшся за укриттями й відстрілюєшся. Написано на Python + pygame-ce.

Мови: English, Українська, Polski, Deutsch, Français, Español (перемикаються в меню,
за замовчуванням береться мова системи).

## Керування

| Клавіша | Дія |
|---|---|
| ← → або A / D | рух |
| Пробіл або ↑ | постріл |
| P / Esc | пауза (з паузи Esc — у головне меню) |
| F11 | повний екран |

## Запуск із вихідного коду

```bash
sudo apt install python3-venv gettext
./tools/compile_translations.sh          # .po -> .mo
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
navala                                   # або: navala --lang uk --windowed
```

## Структура

```
src/navala/        код гри (game.py — логіка, sprites.py — піксель-арт, sound.py — синтез звуків)
po/                переклади (*.po) і шаблон navala.pot
tools/             скрипти для перекладів
snap/              snapcraft.yaml, іконка і .desktop-файл для Snap Store
```

## Як додати нову мову

1. `cp po/navala.pot po/it.po` і перекласти рядки `msgstr`.
2. Додати мову в список `LANGUAGES` у `src/navala/i18n.py`.
3. `./tools/compile_translations.sh`

Після змін у тексті гри: `./tools/update_translations.sh` оновить шаблон і всі .po-файли.

## Збірка snap

```bash
sudo snap install snapcraft --classic
sudo snap install lxd && sudo lxd init --auto
snapcraft pack
sudo snap install --dangerous ./navala_1.0.0_amd64.snap
```

Ліцензія: MIT.
