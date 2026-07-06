# entities/powerup.py
import pygame, random
from settings import *

class PowerUp(pygame.sprite.Sprite):
    # 4 types inspirés des vrais shoot'em up :
    # weapon = monte d'un niveau d'arme (permanent)
    # rapid  = cadence de tir ×2 pendant 10s
    # shield = bouclier rechargé à fond
    # heal   = +40 HP
    TYPES = ['weapon', 'weapon', 'rapid', 'shield', 'heal']   # weapon plus fréquent

    # Icône (lettre) et couleur par type
    _ICONS  = {'weapon': 'W', 'rapid': 'R', 'shield': 'S', 'heal': 'H'}
    _COLORS = {
        'weapon': (255, 220,  50),   # jaune
        'rapid' : ( 50, 255, 150),   # vert
        'shield': (  0, 150, 255),   # bleu
        'heal'  : (255,  80,  80),   # rouge
    }

    def __init__(self, x, y, kind=None):
        super().__init__()
        self.kind  = kind or random.choice(self.TYPES)
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self._draw()
        self.rect  = self.image.get_rect(center=(x, y))
        self.speed = 1.5
        self.timer = 0

    def _draw(self):
        color = self._COLORS[self.kind]
        # Fond hexagone approché (cercle avec bordure)
        pygame.draw.circle(self.image, color,           (14, 14), 13)
        pygame.draw.circle(self.image, (255, 255, 255), (14, 14), 13, 2)
        # Lettre au centre
        font = pygame.font.SysFont('consolas', 14, bold=True)
        lbl  = font.render(self._ICONS[self.kind], True, (0, 0, 0))
        self.image.blit(lbl, (14 - lbl.get_width()//2, 14 - lbl.get_height()//2))

    def update(self, dt):
        self.rect.y += self.speed
        self.timer  += dt
        # Clignoter après 5 secondes
        if self.timer > 5:
            if int(self.timer * 8) % 2 == 0:
                self.image.set_alpha(80)
            else:
                self.image.set_alpha(255)
        # Disparaître après 8 secondes
        if self.timer > 8:
            self.kill()

    def apply(self, player):
        if self.kind == 'weapon':
            player.upgrade_weapon()           # monte weapon_level (max 5)
        elif self.kind == 'rapid':
            player.rapid_fire  = True
            player.rapid_timer = 10.0
            player.shoot_delay = PLAYER_SHOOT_DELAY // 2
        elif self.kind == 'shield':
            player.shield = SHIELD_MAX
        elif self.kind == 'heal':
            player.hp = min(PLAYER_HP, player.hp + 40)
