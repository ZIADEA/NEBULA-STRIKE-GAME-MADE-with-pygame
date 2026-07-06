# systems/background.py — Fond nébuleuse + étoiles parallaxe
import pygame, random, math
from settings import WIDTH, HEIGHT


def _make_nebula_surface():
    """Génère une surface de nébuleuse procédurale 2x la hauteur."""
    surf = pygame.Surface((WIDTH, HEIGHT * 2), pygame.SRCALPHA)
    colors = [
        (80,  0,  120, 28),   # violet profond
        (0,   40, 120, 22),   # bleu nuit
        (120, 0,  60,  20),   # rose sombre
        (40,  0,  80,  18),   # indigo
        (0,   20, 80,  16),   # bleu foncé
    ]
    for _ in range(180):
        color  = random.choice(colors)
        cx     = random.randint(0, WIDTH)
        cy     = random.randint(0, HEIGHT * 2)
        radius = random.randint(60, 220)
        blob   = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        for r, a in [(radius, color[3]), (int(radius*0.6), min(60, color[3]*2))]:
            pygame.draw.circle(blob, (*color[:3], a), (radius, radius), r)
        surf.blit(blob, (cx - radius, cy - radius))
    return surf


class Background:
    """Système de fond : nébuleuse défilante + 3 couches d'étoiles scintillantes."""

    def __init__(self):
        self.nebula  = _make_nebula_surface()
        self.nebula_y = 0.0

        # 3 couches d'étoiles (lentes, moyennes, rapides)
        self.star_layers = [
            self._make_stars(80,  1, speed=0.3),
            self._make_stars(60,  2, speed=0.7),
            self._make_stars(40,  3, speed=1.5),
        ]

    def _make_stars(self, count, size, speed):
        stars = []
        for _ in range(count):
            brightness = random.randint(150, 255)
            stars.append({
                'x': random.uniform(0, WIDTH),
                'y': random.uniform(0, HEIGHT),
                'size':  size,
                'speed': speed,
                'base_brightness': brightness,
                'brightness': brightness,
                'twinkle_timer': random.uniform(0, 2),
            })
        return stars

    def update(self, dt):
        # Faire défiler la nébuleuse lentement
        self.nebula_y = (self.nebula_y + 0.15) % HEIGHT

        # Mettre à jour les étoiles
        for layer in self.star_layers:
            for s in layer:
                s['y'] += s['speed']
                if s['y'] > HEIGHT:
                    s['y'] = 0
                    s['x'] = random.uniform(0, WIDTH)
                # Scintillement (2% de chance par frame)
                if random.random() < 0.02:
                    s['brightness'] = random.randint(60, s['base_brightness'])
                else:
                    # Retour progressif à la luminosité de base
                    s['brightness'] = min(s['base_brightness'],
                                          s['brightness'] + 3)

    def draw(self, surface):
        # Fond de base (nuit spatiale)
        surface.fill((4, 4, 20))

        # Nébuleuse défilante (deux copies pour le loop)
        y = int(self.nebula_y) - HEIGHT
        surface.blit(self.nebula, (0, y))
        surface.blit(self.nebula, (0, y + HEIGHT * 2))

        # Étoiles avec scintillement
        for layer in self.star_layers:
            for s in layer:
                b = s['brightness']
                color = (b, b, min(255, b + 20))
                size  = s['size']
                x, y  = int(s['x']), int(s['y'])
                if size == 1:
                    surface.set_at((x, y), color)
                else:
                    pygame.draw.circle(surface, color, (x, y), size // 2)
