# entities/player.py
import pygame, math
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, particle_system, sound_manager):
        super().__init__()
        self.ps          = particle_system
        self.sm          = sound_manager
        self.image_orig  = self._build_surface()
        self.image       = self.image_orig.copy()
        self.rect        = self.image.get_rect(center=(WIDTH//2, HEIGHT-80))
        self.pos         = pygame.math.Vector2(self.rect.center)

        # Stats
        self.hp          = PLAYER_HP
        self.shield      = SHIELD_MAX
        self.score       = 0
        self.lives       = 3

        # Système de tir : weapon_level 1→5 (comme dans les vrais shoot'em up)
        # 1 = 1 tir  2 = 2 tirs  3 = 3 tirs  4 = 4 tirs  5 = 5 tirs en éventail
        self.weapon_level  = 1
        self.shoot_delay   = PLAYER_SHOOT_DELAY
        self.last_shot     = 0
        self.rapid_fire    = False   # power-up cadence rapide
        self.rapid_timer   = 0

        # Invincibilité
        self.invincible      = False
        self.invincible_timer= 0
        self.blink_timer     = 0

    def _build_surface(self, tilt=0):
        """Construit le vaisseau avec effets de lueur."""
        surf = pygame.Surface((60, 70), pygame.SRCALPHA)
        # Pods latéraux (orange/violet)
        pygame.draw.ellipse(surf, (180, 80, 20), (0,  40, 18, 26))
        pygame.draw.ellipse(surf, (180, 80, 20), (42, 40, 18, 26))
        pygame.draw.ellipse(surf, (255, 140, 40), (2,  42, 14, 20))
        pygame.draw.ellipse(surf, (255, 140, 40), (44, 42, 14, 20))
        # Fuselage principal
        pygame.draw.polygon(surf, (60, 160, 220),
                            [(30,0),(8,55),(20,48),(30,52),(40,48),(52,55)])
        pygame.draw.polygon(surf, (100, 200, 255),
                            [(30,4),(14,48),(30,40),(46,48)])
        # Cockpit avec glow
        pygame.draw.ellipse(surf, (180, 240, 255, 220), (20, 8, 20, 24))
        pygame.draw.ellipse(surf, (255, 255, 255, 120), (24, 10, 12, 14))
        # Halo moteur (glow bleu)
        for r, a in [(14,25),(10,50),(6,100)]:
            blob = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(blob, (0, 180, 255, a), (r, r), r)
            surf.blit(blob, (30-r, 58-r))
        # Flamme moteur
        pygame.draw.ellipse(surf, (0, 200, 255, 200), (24, 56, 12, 10))
        if tilt != 0:
            surf = pygame.transform.rotate(surf, tilt)
        return surf

    def update(self, dt, bullets_group):
        now  = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        # Mouvement
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += PLAYER_SPEED
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= PLAYER_SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += PLAYER_SPEED

        # Normaliser diagonal
        if dx and dy:
            factor = PLAYER_SPEED / math.sqrt(dx*dx + dy*dy)
            dx    *= factor
            dy    *= factor

        self.pos.x = max(30, min(WIDTH-30,  self.pos.x + dx))
        self.pos.y = max(30, min(HEIGHT-30, self.pos.y + dy))
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Inclinaison légère selon la direction (tilt)
        if not self.invincible:
            tilt = -8 if dx < 0 else (8 if dx > 0 else 0)
            self.image = self._build_surface(tilt)

        # Trainée moteur
        if now % 2 == 0:
            self.ps.spawn_trail(self.pos.x, self.pos.y + 34)

        # Tir
        if keys[pygame.K_SPACE] and now - self.last_shot > self.shoot_delay:
            self._shoot(bullets_group)
            self.last_shot = now

        # Régénération bouclier
        self.shield = min(SHIELD_MAX, self.shield + SHIELD_REGEN)

        # Invincibilité / clignotement
        if self.invincible:
            self.invincible_timer -= dt
            self.blink_timer      += dt
            if self.invincible_timer <= 0:
                self.invincible = False
                self.image      = self.image_orig.copy()
            elif int(self.blink_timer * 10) % 2 == 0:
                self.image.set_alpha(60)
            else:
                self.image.set_alpha(255)

        # Timer triple shot
        if self.rapid_fire:
            self.rapid_timer -= dt
            if self.rapid_timer <= 0:
                self.rapid_fire  = False
                self.shoot_delay = PLAYER_SHOOT_DELAY

    def _shoot(self, bullets_group):
        """Tir basé sur weapon_level — inspiré des vrais shoot'em up (1942, Galaga...)."""
        from entities.bullet import PlayerBullet
        self.sm.play('laser')

        # Configuration par niveau : liste d'angles en degrés
        patterns = {
            1: [0],
            2: [-10, 10],
            3: [-14, 0, 14],
            4: [-18, -6, 6, 18],
            5: [-20, -10, 0, 10, 20],
        }
        # Couleur selon le niveau (rouge → orange → jaune → vert → cyan)
        colors = {
            1: (80,  220, 255),   # cyan
            2: (80,  255, 150),   # vert
            3: (220, 255,  80),   # jaune
            4: (255, 160,  50),   # orange
            5: (255,  80, 200),   # rose/magenta
        }
        angles = patterns[self.weapon_level]
        color  = colors[self.weapon_level]
        for angle in angles:
            bullets_group.add(PlayerBullet(self.pos.x, self.pos.y - 24, angle, color=color))

    def upgrade_weapon(self):
        """Monte d'un niveau d'arme (max 5)."""
        self.weapon_level = min(5, self.weapon_level + 1)

    def set_min_weapon(self, level):
        """Garantit un niveau d'arme minimum (progression par vague)."""
        if self.weapon_level < level:
            self.weapon_level = level

    def downgrade_weapon(self, min_level=1):
        """Pénalité classique de mort : perd 1 niveau d'arme (min = niveau de la vague)."""
        self.weapon_level = max(min_level, self.weapon_level - 1)

    def draw_shield_bubble(self, surface):
        """Dessine la bulle de bouclier autour du vaisseau."""
        if self.shield > 10:
            ratio  = self.shield / SHIELD_MAX
            alpha  = int(60 * ratio)
            radius = 40
            bubble = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(bubble, (0, 150, 255, alpha),
                               (radius, radius), radius)
            pygame.draw.circle(bubble, (100, 200, 255, min(180, alpha*2)),
                               (radius, radius), radius, 2)
            surface.blit(bubble, (self.rect.centerx - radius,
                                  self.rect.centery - radius))

    def take_damage(self, dmg):
        if self.invincible:
            return
        # Bouclier absorbe d'abord
        if self.shield > 0:
            absorbed     = min(self.shield, dmg)
            self.shield -= absorbed
            dmg         -= absorbed
        # Dégâts restants sur les HP
        if dmg > 0:
            self.hp -= dmg
            self.ps.spawn_explosion(self.pos.x, self.pos.y, (0,200,255), count=15, speed=2)
            self.sm.play('hit')
            # Invincibilité seulement quand les HP sont touchés
            self.invincible       = True
            self.invincible_timer = 1.0
            self.blink_timer      = 0