"""Навала — аркадний шутер у дусі класичних ігор 1978 року."""

import math
import random

import pygame

from . import i18n, sprites
from .about import About
from .i18n import _

W, H = 640, 720
FPS = 60
TOP_Y = 64           # нижче — ігрове поле, вище — рахунок
GROUND_Y = 688
PLAYER_Y = 640
BUNKER_Y = 548
COLS, ROWS = 11, 5
CELL_W, CELL_H = 44, 36
ALIEN_W, ALIEN_H = 33, 24
ROW_KINDS = ["medusa", "beetle", "beetle", "bot", "bot"]
STEP_X, STEP_DOWN = 8, 16
EXTRA_LIFE_AT = 1500
UFO_POINTS = [50, 100, 150, 300]

BG = (6, 6, 18)
WHITE = (235, 235, 245)
GREY = (140, 140, 165)
YELLOW = (255, 220, 90)
RED = (255, 90, 90)
GROUND = (80, 255, 160)

MENU_ITEMS = ["start", "language", "sound", "fullscreen", "about", "quit"]
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
FIRE_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Alien:
    __slots__ = ("col", "row", "kind", "alive")

    def __init__(self, col, row, kind):
        self.col, self.row, self.kind, self.alive = col, row, kind, True


class Bunker:
    """Укриття з дрібних клітинок, яке поступово руйнується."""

    CELL = 4
    COLS, ROWS = 22, 16

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.cells = set()
        for cy in range(self.ROWS):
            for cx in range(self.COLS):
                if cy < 4 and (cx < 4 - cy or cx > self.COLS - 1 - (4 - cy)):
                    continue  # закруглені верхні кути
                arch = {9: (8, 13), 10: (7, 14)}.get(cy, (6, 15) if cy >= 11 else None)
                if arch and arch[0] <= cx <= arch[1]:
                    continue  # арка знизу
                self.cells.add((cx, cy))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.COLS * self.CELL, self.ROWS * self.CELL)

    def cells_in(self, rect):
        c = self.CELL
        x0, x1 = (rect.left - self.x) // c, (rect.right - 1 - self.x) // c
        y0, y1 = (rect.top - self.y) // c, (rect.bottom - 1 - self.y) // c
        return [(cx, cy) for cy in range(y0, y1 + 1) for cx in range(x0, x1 + 1)
                if (cx, cy) in self.cells]

    def hit(self, rect, going_up):
        """Повертає True, якщо снаряд влучив, і руйнує частину укриття."""
        if not self.rect.colliderect(rect):
            return False
        cells = self.cells_in(rect)
        if not cells:
            return False
        cx, cy = max(cells, key=lambda p: p[1]) if going_up else min(cells, key=lambda p: p[1])
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if (dx, dy) == (0, 0) or (abs(dx) + abs(dy) <= 2 and random.random() < 0.6):
                    self.cells.discard((cx + dx, cy + dy))
        return True

    def erase(self, rect):
        for cell in self.cells_in(rect):
            self.cells.discard(cell)

    def draw(self, surf):
        c = self.CELL
        for cx, cy in self.cells:
            surf.fill(GROUND, (self.x + cx * c, self.y + cy * c, c, c))


class Game:
    def __init__(self, screen, settings, audio):
        self.screen = screen
        self.settings = settings
        self.audio = audio
        self.running = True
        self.time = 0.0
        self.fonts = {}
        self.held = set()

        self.alien_imgs = {k: [sprites.make(f, color) for f in frames]
                           for k, (_pts, color, frames) in sprites.ALIENS.items()}
        self.player_img = sprites.make(sprites.PLAYER, sprites.PLAYER_COLOR)
        self.life_img = sprites.make(sprites.PLAYER, sprites.PLAYER_COLOR, 2)
        self.ufo_img = sprites.make(sprites.UFO, sprites.UFO_COLOR)
        self.expl_imgs = {}
        rnd = random.Random(7)
        self.stars = [(rnd.randrange(W), rnd.randrange(TOP_Y, GROUND_Y), rnd.random() * 6.28)
                      for _ in range(70)]

        self.state = "menu"
        self.menu_index = 0
        self.state_timer = 0.0
        self.score = 0
        self.new_record = False
        self.invaded = False
        self.paused_from = "playing"
        self.about = About()

    # ---------- допоміжне ----------

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)  # вбудований FreeSans: є кирилиця
        return self.fonts[size]

    def text(self, msg, size, color, center=None, topleft=None, topright=None):
        img = self.font(size).render(msg, True, color)
        rect = img.get_rect()
        if center:
            rect.center = center
        elif topleft:
            rect.topleft = topleft
        elif topright:
            rect.topright = topright
        self.screen.blit(img, rect)
        return rect

    def expl_img(self, color):
        if color not in self.expl_imgs:
            self.expl_imgs[color] = sprites.make(sprites.EXPLOSION, color)
        return self.expl_imgs[color]

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass
        self.settings.save()

    # ---------- ігровий цикл ----------

    def new_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.extra_life_given = False
        self.new_record = False
        self.invaded = False
        self.start_wave()

    def start_wave(self):
        self.aliens = [Alien(c, r, ROW_KINDS[r]) for r in range(ROWS) for c in range(COLS)]
        self.ox = (W - COLS * CELL_W) // 2
        self.oy = TOP_Y + 56 + min(self.level - 1, 6) * STEP_DOWN
        self.direction = 1
        self.frame = 0
        self.step_timer = 0.0
        gap = (W - 4 * Bunker.COLS * Bunker.CELL) // 5
        self.bunkers = [Bunker(gap + i * (gap + Bunker.COLS * Bunker.CELL), BUNKER_Y)
                        for i in range(4)]
        self.player_x = W / 2
        self.bullet = None
        self.bombs = []
        self.bomb_timer = 1.5
        self.ufo = None
        self.ufo_timer = random.uniform(15, 25)
        self.explosions = []
        self.set_state("ready", 1.6)

    def set_state(self, state, timer=0.0):
        self.state = state
        self.state_timer = timer

    def alien_rect(self, a):
        return pygame.Rect(self.ox + a.col * CELL_W + (CELL_W - ALIEN_W) // 2,
                           self.oy + a.row * CELL_H, ALIEN_W, ALIEN_H)

    def player_rect(self):
        w, h = self.player_img.get_size()
        return pygame.Rect(int(self.player_x - w / 2), PLAYER_Y, w, h)

    def add_score(self, points):
        self.score += points
        if not self.extra_life_given and self.score >= EXTRA_LIFE_AT:
            self.extra_life_given = True
            self.lives += 1
            self.audio.play("extra_life")
        if self.score > self.settings["high_score"]:
            self.settings["high_score"] = self.score
            self.new_record = True

    def end_game(self):
        self.settings.save()
        self.set_state("game_over", 1.0)

    def fire(self):
        if self.state == "playing" and self.bullet is None:
            self.bullet = pygame.Rect(int(self.player_x) - 1, PLAYER_Y - 12, 3, 12)
            self.audio.play("shoot")

    # ---------- події ----------

    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            self.settings.save()
            self.running = False
            return
        if ev.type == pygame.KEYUP:
            self.held.discard(ev.key)
            return
        if ev.type != pygame.KEYDOWN:
            return
        self.held.add(ev.key)
        key = ev.key
        if key == pygame.K_F11:
            self.toggle_fullscreen()
            return

        if self.state == "menu":
            self.menu_key(key)
        elif self.state == "about":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.about.activate(self.settings["fullscreen"])
            else:
                self.set_state("menu")
        elif self.state == "paused":
            if key in (pygame.K_p, pygame.K_PAUSE) or key in CONFIRM_KEYS:
                self.set_state(self.paused_from, self.state_timer)
            elif key == pygame.K_ESCAPE:
                self.settings.save()
                self.set_state("menu")
        elif self.state == "game_over":
            if self.state_timer <= 0 and (key in CONFIRM_KEYS or key == pygame.K_ESCAPE):
                self.set_state("menu")
        else:  # ready / playing / dying / wave_clear
            if key in (pygame.K_p, pygame.K_PAUSE, pygame.K_ESCAPE):
                self.paused_from = self.state
                self.set_state("paused", self.state_timer)
            elif key in FIRE_KEYS:
                self.fire()

    def menu_key(self, key):
        item = MENU_ITEMS[self.menu_index]
        if key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(MENU_ITEMS)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(MENU_ITEMS)
        elif key == pygame.K_ESCAPE:
            self.settings.save()
            self.running = False
        elif key in LEFT_KEYS + RIGHT_KEYS + CONFIRM_KEYS:
            delta = -1 if key in LEFT_KEYS else 1
            if item == "language":
                codes = i18n.CODES
                code = codes[(codes.index(i18n.current_language()) + delta) % len(codes)]
                i18n.set_language(code)
                self.settings["language"] = code
                self.settings.save()
            elif item == "sound":
                self.settings["sound"] = self.audio.enabled = not self.audio.enabled
                self.settings.save()
            elif item == "fullscreen":
                self.toggle_fullscreen()
            elif key in CONFIRM_KEYS:
                if item == "start":
                    self.new_game()
                elif item == "about":
                    self.about.status = None
                    self.set_state("about")
                elif item == "quit":
                    self.settings.save()
                    self.running = False

    # ---------- оновлення ----------

    def update(self, dt):
        self.time += dt
        if self.state in ("menu", "paused", "about"):
            return
        if self.state == "game_over":
            self.state_timer -= dt
            return

        self.update_explosions(dt)
        if self.state == "ready":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.set_state("playing")
            return
        if self.state == "wave_clear":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.level += 1
                self.start_wave()
            return
        if self.state == "dying":
            self.update_bombs(dt)
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.lives -= 1
                if self.lives <= 0 or self.invaded:
                    self.lives = 0
                    self.end_game()
                else:
                    self.player_x = W / 2
                    self.bombs.clear()
                    self.set_state("playing")
            return

        # --- state == "playing" ---
        move = any(k in self.held for k in RIGHT_KEYS) - any(k in self.held for k in LEFT_KEYS)
        half = self.player_img.get_width() / 2
        self.player_x = max(16 + half, min(W - 16 - half, self.player_x + move * 260 * dt))
        if any(k in self.held for k in FIRE_KEYS):
            self.fire()

        self.update_bullet(dt)
        self.update_aliens(dt)
        self.update_bombs(dt)
        self.update_ufo(dt)

        if self.state == "playing" and not any(a.alive for a in self.aliens):
            self.bullet = None
            self.bombs.clear()
            self.set_state("wave_clear", 1.8)

    def update_explosions(self, dt):
        for e in self.explosions:
            e[2] -= dt
        self.explosions = [e for e in self.explosions if e[2] > 0]

    def update_bullet(self, dt):
        if self.bullet is None:
            return
        self.bullet.y -= int(720 * dt) or 1
        b = self.bullet
        if b.bottom < TOP_Y:
            self.bullet = None
            return
        for bomb in self.bombs:
            if bomb.colliderect(b):
                self.bombs.remove(bomb)
                self.explosions.append([b.centerx, b.top, 0.2, WHITE])
                self.bullet = None
                return
        for bunker in self.bunkers:
            if bunker.hit(b, going_up=True):
                self.bullet = None
                return
        for a in self.aliens:
            if a.alive:
                r = self.alien_rect(a)
                if r.colliderect(b):
                    a.alive = False
                    points, color, _f = sprites.ALIENS[a.kind]
                    self.add_score(points)
                    self.explosions.append([r.centerx, r.centery, 0.3, color])
                    self.audio.play("alien_hit")
                    self.bullet = None
                    return
        if self.ufo:
            r = self.ufo_rect()
            if r.colliderect(b):
                points = random.choice(UFO_POINTS)
                self.add_score(points)
                self.explosions.append([r.centerx, r.centery, 1.0, sprites.UFO_COLOR, points])
                self.audio.play("ufo_hit")
                self.ufo = None
                self.bullet = None

    def step_interval(self):
        alive = sum(a.alive for a in self.aliens)
        interval = 0.02 + 0.7 * alive / (COLS * ROWS)
        return interval * max(0.55, 1 - 0.07 * (self.level - 1))

    def update_aliens(self, dt):
        self.step_timer += dt
        if self.step_timer < self.step_interval():
            return
        self.step_timer = 0.0
        alive = [a for a in self.aliens if a.alive]
        if not alive:
            return
        rects = [self.alien_rect(a) for a in alive]
        left = min(r.left for r in rects)
        right = max(r.right for r in rects)
        if (self.direction > 0 and right + STEP_X > W - 12) or \
           (self.direction < 0 and left - STEP_X < 12):
            self.oy += STEP_DOWN
            self.direction *= -1
        else:
            self.ox += self.direction * STEP_X
        self.frame ^= 1
        self.audio.play("march")

        for a in alive:
            r = self.alien_rect(a)
            for bunker in self.bunkers:
                if bunker.rect.colliderect(r):
                    bunker.erase(r)
            if r.bottom >= PLAYER_Y:
                self.invaded = True
                self.kill_player()
                return

    def update_bombs(self, dt):
        if self.state == "playing":
            self.bomb_timer -= dt
            max_bombs = min(2 + self.level, 6)
            if self.bomb_timer <= 0 and len(self.bombs) < max_bombs:
                self.drop_bomb()
                self.bomb_timer = random.uniform(0.4, 1.2) * max(0.4, 1 - 0.08 * (self.level - 1))
        speed = int((210 + 15 * self.level) * dt) or 1
        player = self.player_rect()
        for bomb in list(self.bombs):
            bomb.y += speed
            if bomb.bottom >= GROUND_Y:
                self.bombs.remove(bomb)
                self.explosions.append([bomb.centerx, GROUND_Y - 6, 0.2, RED])
                continue
            if any(bunker.hit(bomb, going_up=False) for bunker in self.bunkers):
                self.bombs.remove(bomb)
                continue
            if self.state == "playing" and bomb.colliderect(player):
                self.bombs.remove(bomb)
                self.invaded = False
                self.kill_player()

    def drop_bomb(self):
        bottom = {}
        for a in self.aliens:
            if a.alive and (a.col not in bottom or a.row > bottom[a.col].row):
                bottom[a.col] = a
        if not bottom:
            return
        shooters = list(bottom.values())
        if random.random() < 0.4:  # іноді цілять прямо в гравця
            shooter = min(shooters, key=lambda a: abs(self.alien_rect(a).centerx - self.player_x))
        else:
            shooter = random.choice(shooters)
        r = self.alien_rect(shooter)
        self.bombs.append(pygame.Rect(r.centerx - 2, r.bottom, 4, 12))

    def kill_player(self):
        if self.state != "playing":
            return
        r = self.player_rect()
        self.explosions.append([r.centerx, r.centery, 1.4, sprites.PLAYER_COLOR])
        self.audio.play("player_hit")
        self.bullet = None
        self.set_state("dying", 1.6)

    def ufo_rect(self):
        w, h = self.ufo_img.get_size()
        return pygame.Rect(int(self.ufo[0]), TOP_Y + 12, w, h)

    def update_ufo(self, dt):
        if self.ufo is None:
            self.ufo_timer -= dt
            if self.ufo_timer <= 0 and sum(a.alive for a in self.aliens) > 7:
                direction = random.choice((-1, 1))
                start = -self.ufo_img.get_width() if direction > 0 else W
                self.ufo = [float(start), direction, 0.0]
                self.ufo_timer = random.uniform(18, 30)
            return
        self.ufo[0] += self.ufo[1] * 140 * dt
        self.ufo[2] -= dt
        if self.ufo[2] <= 0:
            self.audio.play("ufo")
            self.ufo[2] = 0.25
        if self.ufo[0] > W + 10 or self.ufo[0] < -self.ufo_img.get_width() - 10:
            self.ufo = None

    # ---------- малювання ----------

    def draw(self):
        s = self.screen
        s.fill(BG)
        for x, y, phase in self.stars:
            level = int(70 + 30 * (1 + math.sin(phase + self.time * 1.7)))
            s.set_at((x, y), (level, level, level + 30))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "about":
            self.about.draw(self, W, H, (WHITE, GREY, YELLOW, RED))
        else:
            self.draw_play()
        pygame.display.flip()

    def draw_header(self):
        self.text(_("SCORE"), 22, GREY, topleft=(20, 10))
        self.text(f"{self.score:05d}", 34, WHITE, topleft=(20, 30))
        self.text(_("HI-SCORE"), 22, GREY, topright=(W - 20, 10))
        self.text(f"{self.settings['high_score']:05d}", 34, WHITE, topright=(W - 20, 30))

    def draw_menu(self):
        hi = self.settings["high_score"]
        self.text(_("HI-SCORE") + f"  {hi:05d}", 24, GREY, center=(W // 2, 28))

        bob = int(4 * math.sin(self.time * 2))
        title = _("NAVALA")
        self.text(title, 96, (90, 40, 140), center=(W // 2 + 4, 120 + 4 + bob))
        self.text(title, 96, YELLOW, center=(W // 2, 120 + bob))
        self.text(_("Defend the Earth from the alien invasion!"), 26, WHITE, center=(W // 2, 185))

        on, off = _("On"), _("Off")
        labels = {
            "start": _("Start game"),
            "language": _("Language: {name}").format(name=i18n.language_name(i18n.current_language())),
            "sound": _("Sound: {state}").format(state=on if self.audio.enabled else off),
            "fullscreen": _("Fullscreen: {state}").format(
                state=on if self.settings["fullscreen"] else off),
            "about": _("About"),
            "quit": _("Quit"),
        }
        for i, item in enumerate(MENU_ITEMS):
            y = 240 + i * 38
            selected = i == self.menu_index
            label = labels[item]
            if selected and item in ("language", "sound", "fullscreen"):
                label = f"<  {label}  >"
            rect = self.text(label, 34, YELLOW if selected else GREY, center=(W // 2, y))
            if selected:
                self.screen.blit(self.alien_imgs["bot"][int(self.time * 3) % 2],
                                 (rect.left - 50, y - ALIEN_H // 2))

        self.text(_("POINTS"), 26, GREY, center=(W // 2, 482))
        rows = [(self.ufo_img, _("= ? mystery"))]
        rows += [(self.alien_imgs[k][0], _("= {points} points").format(points=sprites.ALIENS[k][0]))
                 for k in ("medusa", "beetle", "bot")]
        for i, (img, label) in enumerate(rows):
            y = 518 + i * 36
            self.screen.blit(img, img.get_rect(center=(W // 2 - 80, y)))
            self.text(label, 28, WHITE, topleft=(W // 2 - 40, y - 10))

        self.text(_("ARROWS move    SPACE fire    P pause    F11 fullscreen"), 22, GREY,
                  center=(W // 2, H - 26))

    def draw_play(self):
        s = self.screen
        self.draw_header()
        for bunker in self.bunkers:
            bunker.draw(s)
        for a in self.aliens:
            if a.alive:
                s.blit(self.alien_imgs[a.kind][self.frame], self.alien_rect(a))
        if self.ufo:
            s.blit(self.ufo_img, self.ufo_rect())
        if self.state != "dying" and not (self.state == "game_over" and self.lives <= 0):
            s.blit(self.player_img, self.player_rect())
        if self.bullet:
            s.fill(WHITE, self.bullet)
        for bomb in self.bombs:
            zig = int(self.time * 20 + bomb.x) % 2
            for k in range(0, bomb.height, 4):
                s.fill(RED, (bomb.x + (zig if (k // 4) % 2 else 1 - zig) * 2, bomb.y + k, 2, 4))
        for e in self.explosions:
            if len(e) > 4:  # очки за НЛО
                self.text(str(e[4]), 30, e[3], center=(e[0], e[1]))
            elif int(e[2] * 20) % 2 or e[2] < 1:
                img = self.expl_img(e[3])
                s.blit(img, img.get_rect(center=(e[0], e[1])))

        s.fill(GROUND, (0, GROUND_Y, W, 2))
        for i in range(min(self.lives - 1, 6)):
            s.blit(self.life_img, (20 + i * 34, GROUND_Y + 10))
        self.text(_("LEVEL {n}").format(n=self.level), 24, GREY, topright=(W - 20, GROUND_Y + 8))

        center = (W // 2, H // 2 + 40)
        if self.state == "ready":
            self.overlay_box([(_("LEVEL {n}").format(n=self.level), 48, YELLOW),
                              (_("Get ready!"), 30, WHITE)], center)
        elif self.state == "wave_clear":
            self.overlay_box([(_("Wave cleared!"), 44, YELLOW)], center)
        elif self.state == "paused":
            self.overlay_box([(_("PAUSED"), 56, YELLOW),
                              (_("P — continue    ESC — main menu"), 26, WHITE)], center)
        elif self.state == "game_over":
            lines = [(_("GAME OVER"), 64, RED)]
            if self.new_record:
                lines.append((_("NEW HIGH SCORE!"), 34, YELLOW))
            if self.state_timer <= 0:
                lines.append((_("Press ENTER to continue"), 26, WHITE))
            self.overlay_box(lines, center)

    def overlay_box(self, lines, center):
        heights = [self.font(size).get_linesize() for _t, size, _c in lines]
        widths = [self.font(size).size(t)[0] for t, size, _c in lines]
        box = pygame.Rect(0, 0, max(widths) + 60, sum(heights) + 36)
        box.center = center
        shade = pygame.Surface(box.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 200))
        self.screen.blit(shade, box)
        pygame.draw.rect(self.screen, GREY, box, 2)
        y = box.top + 18
        for (t, size, color), h in zip(lines, heights):
            self.text(t, size, color, center=(box.centerx, y + h // 2))
            y += h


def run(screen, settings, audio):
    game = Game(screen, settings, audio)
    clock = pygame.time.Clock()
    while game.running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for ev in pygame.event.get():
            game.handle_event(ev)
        game.update(dt)
        game.draw()
    settings.save()
