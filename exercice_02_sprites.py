import pygame, sys, math, random
pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('NEBULA STRIKE — v0.2')
clock = pygame.time.Clock()

# ══════════════════════════════════════
# CLASSE PLAYER
# ══════════════════════════════════════
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
        self.draw_ship()

        self.rect = self.image.get_rect(center=(400, 500))
        self.speed = 6

    def draw_ship(self):
        img = self.image
        img.fill((0, 0, 0, 0))

        pygame.draw.polygon(img, (0, 200, 255), [
            (20, 0),
            (5, 45),
            (20, 35),
            (35, 45)
        ])

        for r, alpha in [(12, 40), (8, 80), (5, 140)]:
            glow = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 150, 255, alpha), (r, r), r)
            img.blit(glow, (20-r, 38-r))

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:  self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        if keys[pygame.K_UP]:    self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:  self.rect.y += self.speed

        self.rect.clamp_ip(screen.get_rect())


# ══════════════════════════════════════
# CLASSE STAR
# ══════════════════════════════════════
class Star(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = random.randint(1, 4)
        self.speed = self.size * 0.8

        brightness = min(255, 100 + self.size * 40)  # ✅ corrigé
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((brightness, brightness, brightness))

        self.rect = self.image.get_rect(
            x=random.randint(0, 800),
            y=random.randint(0, 600)
        )

    def update(self, dt):
        self.rect.y += self.speed
        if self.rect.y > 600:
            self.rect.y = 0
            self.rect.x = random.randint(0, 800)


# ══════════════════════════════════════
# CRÉER LES OBJETS ET GROUPES
# ══════════════════════════════════════
player = Player()

all_sprites = pygame.sprite.Group()
stars_group = pygame.sprite.Group()

for _ in range(120):
    s = Star()
    stars_group.add(s)
    all_sprites.add(s)

all_sprites.add(player)

# ══════════════════════════════════════
# GAME LOOP
# ══════════════════════════════════════
running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False

    stars_group.update(dt)
    player.update(dt)

    screen.fill((5, 5, 20))
    stars_group.draw(screen)
    screen.blit(player.image, player.rect)

    pygame.display.flip()

pygame.quit()
sys.exit()