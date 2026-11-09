"""Звуки, синтезовані в коді: жодних сторонніх аудіофайлів і ліцензій."""

import math
import random
from array import array

import pygame

RATE = 22050


def _tone(freq_start, freq_end, duration, volume=0.35, wave="square", noise=0.0):
    n = int(RATE * duration)
    buf = array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = freq_start + (freq_end - freq_start) * t
        phase += freq / RATE
        if wave == "square":
            s = 1.0 if (phase % 1.0) < 0.5 else -1.0
        else:
            s = math.sin(2 * math.pi * phase)
        if noise:
            s = s * (1 - noise) + random.uniform(-1, 1) * noise
        env = min(1.0, i / (RATE * 0.005)) * (1 - t) ** 1.5  # атака + затухання
        v = int(s * env * volume * 32767)
        buf.append(v)
        buf.append(v)  # стерео
    return buf


class Audio:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.ok = False
        self.sounds = {}
        self._march_step = 0
        try:
            pygame.mixer.pre_init(RATE, -16, 2, 512)
            pygame.mixer.init()
            self.ok = True
        except pygame.error:
            return  # немає звукової карти — граємо без звуку
        def snd(buf):
            return pygame.mixer.Sound(buffer=buf.tobytes())
        self.sounds = {
            "shoot": snd(_tone(1200, 300, 0.12, 0.25)),
            "alien_hit": snd(_tone(400, 60, 0.25, 0.35, noise=0.6)),
            "player_hit": snd(_tone(300, 30, 0.9, 0.45, noise=0.8)),
            "ufo_hit": snd(_tone(900, 200, 0.5, 0.35, wave="sine", noise=0.2)),
            "ufo": snd(_tone(700, 900, 0.18, 0.15, wave="sine")),
            "extra_life": snd(_tone(600, 1500, 0.4, 0.3, wave="sine")),
            "march": [snd(_tone(f, f * 0.9, 0.09, 0.4)) for f in (110, 98, 87, 82)],
        }

    def play(self, name):
        if not (self.enabled and self.ok):
            return
        if name == "march":
            self.sounds["march"][self._march_step % 4].play()
            self._march_step += 1
        else:
            self.sounds[name].play()
