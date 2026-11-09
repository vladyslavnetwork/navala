"""Піксельні спрайти, намальовані рядками тексту (X — піксель)."""

import pygame

ALIENS = {
    # тип: (очки, колір, [кадр1, кадр2])
    "medusa": (30, (255, 110, 220), [
        ["...XXXXX...",
         "..XXXXXXX..",
         ".XX.XXX.XX.",
         ".XXXXXXXXX.",
         "...X...X...",
         "..X.XXX.X..",
         ".X.......X.",
         "..X.....X.."],
        ["...XXXXX...",
         "..XXXXXXX..",
         ".XX.XXX.XX.",
         ".XXXXXXXXX.",
         "...X...X...",
         "...X.X.X...",
         "..X..X..X..",
         ".X.......X."],
    ]),
    "beetle": (20, (90, 220, 255), [
        ["X...XXX...X",
         ".X.XXXXX.X.",
         "..XX.X.XX..",
         ".XXXXXXXXX.",
         "XXXXXXXXXXX",
         "X.XX...XX.X",
         "..X.....X..",
         ".X.......X."],
        ["....XXX....",
         "X..XXXXX..X",
         ".XXX.X.XXX.",
         ".XXXXXXXXX.",
         "XXXXXXXXXXX",
         "..XX...XX..",
         ".X..X.X..X.",
         "X.........X"],
    ]),
    "bot": (10, (120, 255, 120), [
        ["..XXXXXXX..",
         ".XXXXXXXXX.",
         "XX..XXX..XX",
         "XXXXXXXXXXX",
         ".XXX...XXX.",
         "..X.XXX.X..",
         ".X.......X.",
         "X.........X"],
        ["..XXXXXXX..",
         ".XXXXXXXXX.",
         "XX..XXX..XX",
         "XXXXXXXXXXX",
         ".XXX...XXX.",
         "...X.X.X...",
         "..X.X.X.X..",
         "...X...X..."],
    ]),
}

PLAYER = [
    "......X......",
    ".....XXX.....",
    ".....XXX.....",
    ".XXXXXXXXXXX.",
    "XXXXXXXXXXXXX",
    "XXXX.XXX.XXXX",
    "XXXXXXXXXXXXX",
    "XXXXXXXXXXXXX",
]

UFO = [
    ".....XXXXXX.....",
    "...XXXXXXXXXX...",
    "..XXXXXXXXXXXX..",
    ".XX.XX.XX.XX.XX.",
    "XXXXXXXXXXXXXXXX",
    "..XXX..XX..XXX..",
    "...X........X...",
]

EXPLOSION = [
    "X...X...X..",
    ".X..X..X...",
    "..X...X..X.",
    "XX.......XX",
    "...X...X...",
    ".X..X.X..X.",
    "X...X...X..",
]

PLAYER_COLOR = (80, 255, 160)
UFO_COLOR = (255, 70, 70)


def make(rows, color, scale=3):
    w, h = len(rows[0]), len(rows)
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "X":
                surf.fill(color, (x * scale, y * scale, scale, scale))
    return surf
