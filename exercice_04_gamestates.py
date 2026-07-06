import pygame, sys, random, numpy as np
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('NEBULA STRIKE — v0.4')
clock = pygame.time.Clock()

# ══════════════════════════════════════
# FONTS
# ══════════════════════════════════════
font_xl = pygame.font.SysFont('consolas', 52, bold=True)
font_lg = pygame.font.SysFont('consolas', 32, bold=True)
font_sm = pygame.font.SysFont('consolas', 18)

# ══════════════════════════════════════
# SONS
# ══════════════════════════════════════
def make_laser_sound():
    t = np.linspace(0, 0.08, int(44100 * 0.08))
    freq_sweep = 880 * np.exp(-8 * t)
    wave = np.sign(np.sin(2 * np.pi * freq_sweep * t))
    envelope = np.exp(-15 * t)
    wave = (wave * envelope * 32767 * 0.4).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((wave, wave)))

def make_explosion_sound():
    t = np.linspace(0, 0.4, int(44100 * 0.4))
    noise = np.random.uniform(-1, 1, len(t))
    envelope = np.exp(-6 * t) * (1 - np.exp(-200 * t))
    wave = (noise * envelope * 32767 * 0.8).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((wave, wave)))

laser_snd     = make_laser_sound()
explosion_snd = make_explosion_sound()

# ══════════════════════════════════════
# GAME STATE
# ══════════════════════════════════════
class GameState:
    MENU      = 'menu'
    PLAYING   = 'playing'
    PAUSED    = 'paused'
    GAME_OVER = 'game_over'

# ══════════════════════════════════════
# CLASSES
# ══════════════════════════════════════
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
        self._draw()
        self.rect  = self.image.get_rect(center=(WIDTH//2, HEIGHT - 80))
        self.pos   = pygame.math.Vector2(self.rect.center)
        self.speed = 5.5
        self.hp    = 100

    def _draw(self):
        img = self.image
        img.fill((0, 0, 0, 0))
        pygame.draw.polygon(img, (0, 200, 255), [
            (20, 0), (5, 45), (20, 35), (35, 45)
        ])

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.pos.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.pos.x += self.speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.pos.y -= self.speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.pos.y += self.speed

        # rester dans l'écran
        self.pos.x = max(22, min(WIDTH - 22,  self.pos.x))
        self.pos.y = max(22, min(HEIGHT - 22, self.pos.y))
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def shoot(self, bullets_group):
        b = Bullet(self.pos.x, self.pos.y - 25)
        bullets_group.add(b)
        laser_snd.play()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 255, 100), (0, 0, 4, 14), border_radius=2)
        self.rect  = self.image.get_rect(center=(x, y))
        self.speed = 10

    def update(self, dt):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (220, 50, 50), [
            (15, 30), (0, 0), (30, 0)
        ])
        self.rect  = self.image.get_rect(
            x=random.randint(20, WIDTH - 50),
            y=random.randint(-150, -30)
        )
        self.speed = random.uniform(1.5, 3.5)
        self.hp    = 20

    def update(self, dt):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

class Star(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        size = random.randint(1, 4)
        brightness = min(255, 100 + size * 40)
        self.image = pygame.Surface((size, size))
        self.image.fill((brightness, brightness, brightness))
        self.rect  = self.image.get_rect(
            x=random.randint(0, WIDTH),
            y=random.randint(0, HEIGHT)
        )
        self.speed = size * 0.8

    def update(self, dt):
        self.rect.y += self.speed
        if self.rect.y > HEIGHT:
            self.rect.y = 0
            self.rect.x = random.randint(0, WIDTH)

# ══════════════════════════════════════
# ÉVÉNEMENT PERSONNALISÉ — spawn ennemi
# ══════════════════════════════════════
SPAWN_ENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_ENEMY, 2000)  # toutes les 2 secondes

# ══════════════════════════════════════
# INITIALISATION
# ══════════════════════════════════════
def new_game():
    """Réinitialise tous les groupes et crée un nouveau joueur."""
    enemies.empty()
    bullets.empty()
    player_group.empty()
    p = Player()
    player_group.add(p)
    return p

stars   = pygame.sprite.Group()
for _ in range(120):
    stars.add(Star())

player_group = pygame.sprite.GroupSingle()
enemies      = pygame.sprite.Group()
bullets      = pygame.sprite.Group()

state  = GameState.MENU
player = None
score  = 0

# ══════════════════════════════════════
# GAME LOOP
# ══════════════════════════════════════
running = True
shoot_delay = 250   # ms entre deux tirs
last_shot   = 0

while running:
    dt = clock.tick(FPS) / 1000.0

    # ── ÉVÉNEMENTS ──────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # ── MENU ──────────────────────────────────
            if state == GameState.MENU:
                if event.key == pygame.K_RETURN:
                    player = new_game()
                    score  = 0
                    state  = GameState.PLAYING

            # ── PLAYING ───────────────────────────────
            elif state == GameState.PLAYING:
                if event.key == pygame.K_p:
                    state = GameState.PAUSED
                if event.key == pygame.K_ESCAPE:
                    state = GameState.MENU

            # ── PAUSED ────────────────────────────────
            elif state == GameState.PAUSED:
                if event.key == pygame.K_p:
                    state = GameState.PLAYING

            # ── GAME OVER ─────────────────────────────
            elif state == GameState.GAME_OVER:
                if event.key == pygame.K_r:
                    player = new_game()
                    score  = 0
                    state  = GameState.PLAYING
                if event.key == pygame.K_ESCAPE:
                    state = GameState.MENU

        # ── SPAWN ENNEMI (événement timer) ────────────
        if event.type == SPAWN_ENEMY and state == GameState.PLAYING:
            enemies.add(Enemy())

    # ── MISE À JOUR ─────────────────────────────────────
    if state == GameState.PLAYING:

        stars.update(dt)
        player.update(dt)
        bullets.update(dt)
        enemies.update(dt)

        # Tir automatique (ESPACE enfoncé)
        now  = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and now - last_shot > shoot_delay:
            player.shoot(bullets)
            last_shot = now

        # ── Collisions balles → ennemis ─────────────
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy in hits:
            enemy.hp -= 10
            if enemy.hp <= 0:
                enemy.kill()
                explosion_snd.play()
                score += 100

        # ── Collisions ennemis → joueur ─────────────
        if pygame.sprite.spritecollide(player, enemies, True):
            player.hp -= 20
            explosion_snd.play()
            if player.hp <= 0:
                state = GameState.GAME_OVER

    elif state != GameState.PAUSED:
        # Étoiles continuent en menu et game over
        stars.update(dt)

    # ── RENDU ───────────────────────────────────────────
    screen.fill((5, 5, 20))
    stars.draw(screen)

    # ── MENU ────────────────────────────────────────────
    if state == GameState.MENU:
        t1 = font_xl.render('NEBULA STRIKE', True, (0, 200, 255))
        t2 = font_sm.render('ENTRÉE  pour jouer', True, (200, 200, 200))
        t3 = font_sm.render('ESPACE  pour tirer  |  P  pour pause', True, (150, 150, 150))
        screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
        screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))
        screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2 + 40))

    # ── PLAYING ─────────────────────────────────────────
    elif state == GameState.PLAYING:
        enemies.draw(screen)
        bullets.draw(screen)
        screen.blit(player.image, player.rect)

        # HUD simple
        hp_txt    = font_sm.render(f'HP : {player.hp}', True, (0, 255, 100))
        score_txt = font_sm.render(f'SCORE : {score}', True, (255, 220, 50))
        screen.blit(hp_txt,    (20, 20))
        screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 10))

    # ── PAUSED ──────────────────────────────────────────
    elif state == GameState.PAUSED:
        enemies.draw(screen)
        bullets.draw(screen)
        screen.blit(player.image, player.rect)

        # Overlay semi-transparent
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        t1 = font_lg.render('PAUSE', True, (200, 200, 255))
        t2 = font_sm.render('P  pour continuer', True, (180, 180, 180))
        screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//2 - 40))
        screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2 + 20))

    # ── GAME OVER ───────────────────────────────────────
    elif state == GameState.GAME_OVER:
        t1 = font_xl.render('GAME OVER', True, (220, 50, 50))
        t2 = font_lg.render(f'SCORE : {score}', True, (255, 220, 50))
        t3 = font_sm.render('R  pour rejouer  |  ÉCHAP  pour menu', True, (180, 180, 180))
        screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
        screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))
        screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2 + 60))

    pygame.display.flip()

pygame.quit()
sys.exit()