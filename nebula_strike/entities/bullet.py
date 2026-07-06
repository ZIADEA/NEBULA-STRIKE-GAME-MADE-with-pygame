# entities/bullet.py — Projectiles avec traînées lumineuses et glow
import pygame, math
from settings import *


def _glow(surf, color, cx, cy, radius, alpha=80):
    """Dessine un halo lumineux semi-transparent."""
    blob = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(blob, (*color, alpha), (radius, radius), radius)
    surf.blit(blob, (cx - radius, cy - radius))


class PlayerBullet(pygame.sprite.Sprite):
    TRAIL_LEN = 8  # nombre de points de traînée

    def __init__(self, x, y, angle=0, color=None):
        super().__init__()
        self.color = color or (80, 220, 255)   # cyan par défaut, rose pour triple
        self._build_image()
        self.rect  = self.image.get_rect(center=(x, y))
        rad        = math.radians(angle)
        self.vx    = math.sin(rad)  * PLAYER_BULLET_SPD
        self.vy    = -math.cos(rad) * PLAYER_BULLET_SPD
        # Traînée : liste de positions récentes
        self.trail = [(float(x), float(y))] * self.TRAIL_LEN

    def _build_image(self):
        w, h   = 8, 20
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        r, g, b = self.color
        # Halo externe
        _glow(self.image, (r, g, b), cx, cy, 8, 50)
        # Corps de la balle (losange allongé)
        pts = [(cx, 0), (cx+3, cy), (cx, h-2), (cx-3, cy)]
        pygame.draw.polygon(self.image, (min(255, r+60), min(255, g+60), min(255, b+60)), pts)
        # Noyau blanc brillant
        pygame.draw.ellipse(self.image, (255, 255, 255), (cx-1, cy-4, 2, 8))

    def update(self, dt):
        # Décaler la traînée
        self.trail = self.trail[1:] + [(self.rect.centerx, self.rect.centery)]
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.bottom < 0 or self.rect.top > HEIGHT
                or self.rect.right < 0 or self.rect.left > WIDTH):
            self.kill()

    def draw_trail(self, surface):
        """À appeler AVANT draw() du groupe pour les traînées."""
        r, g, b = self.color
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(180 * i / self.TRAIL_LEN)
            size  = max(1, i // 2)
            blob  = pygame.Surface((size*2+1, size*2+1), pygame.SRCALPHA)
            pygame.draw.circle(blob, (r, g, b, alpha), (size, size), size)
            surface.blit(blob, (int(tx)-size, int(ty)-size))


class EnemyBullet(pygame.sprite.Sprite):
    TRAIL_LEN = 6

    def __init__(self, x, y, vx, vy):
        super().__init__()
        self.vx = vx
        self.vy = vy
        self._build_image()
        self.rect  = self.image.get_rect(center=(x, y))
        self.trail = [(float(x), float(y))] * self.TRAIL_LEN

    def _build_image(self):
        self.image = pygame.Surface((14, 14), pygame.SRCALPHA)
        # Halo orange
        _glow(self.image, (255, 60, 0), 7, 7, 7, 70)
        # Cercle rouge vif
        pygame.draw.circle(self.image, (255, 80, 40), (7, 7), 4)
        # Noyau orange brillant
        pygame.draw.circle(self.image, (255, 180, 0), (7, 7), 2)

    def update(self, dt):
        self.trail = self.trail[1:] + [(self.rect.centerx, self.rect.centery)]
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.bottom < 0 or self.rect.top > HEIGHT
                or self.rect.right < 0 or self.rect.left > WIDTH):
            self.kill()

    def draw_trail(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(160 * i / self.TRAIL_LEN)
            size  = max(1, i // 2)
            blob  = pygame.Surface((size*2+1, size*2+1), pygame.SRCALPHA)
            pygame.draw.circle(blob, (255, 80, 0, alpha), (size, size), size)
            surface.blit(blob, (int(tx)-size, int(ty)-size))

