# entities/enemy.py
import pygame, math, random
from settings import *

class BaseEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y, hp, speed, color, size):
        super().__init__()
        self.hp      = hp
        self.max_hp  = hp
        self.speed   = speed
        self.color   = color
        self.image   = self._build_surface(size, color)
        self.rect    = self.image.get_rect(center=(x, y))
        self.pos     = pygame.math.Vector2(x, y)

    def _build_surface(self, size, color):
        raise NotImplementedError

    def take_damage(self, dmg, ps=None):
        self.hp -= dmg
        if ps:
            ps.spawn_explosion(self.pos.x, self.pos.y, self.color, count=8, speed=1.5)
        return self.hp <= 0

    def draw_health_bar(self, surface):
        w     = self.rect.width
        ratio = max(0, self.hp / self.max_hp)
        bar   = pygame.Rect(self.rect.left, self.rect.top - 8, w, 5)
        pygame.draw.rect(surface, (80,0,0), bar)
        pygame.draw.rect(surface, (220,50,50), (bar.x, bar.y, int(w*ratio), 5))


class EnemyDrone(BaseEnemy):
    def __init__(self, x, y):
        super().__init__(x, y, DRONE_HP, DRONE_SPD, C_DRONE, 34)
        self.zigzag_amp  = random.uniform(60, 120)
        self.zigzag_freq = random.uniform(1.5, 3.0)
        self.time        = random.uniform(0, math.tau)
        self.score_value = SCORE_DRONE

    def _build_surface(self, size, color):
        surf = pygame.Surface((size, size+8), pygame.SRCALPHA)
        r    = size // 2
        # Halo rouge
        blob = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(blob, (200, 0, 0, 40), (r, r), r)
        surf.blit(blob, (0, 0))
        # Corps
        pygame.draw.polygon(surf, (180, 30, 30), [(r,0),(size,size-4),(r,size-10),(0,size-4)])
        pygame.draw.polygon(surf, color,         [(r,4),(size-4,size-6),(r,size-12),(4,size-6)])
        # Moteur glow
        for rr, a in [(8,40),(5,100)]:
            blob = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
            pygame.draw.circle(blob, (255, 80, 0, a), (rr, rr), rr)
            surf.blit(blob, (r-rr, size-rr))
        pygame.draw.circle(surf, (255,120,0), (r, size-2), 3)
        return surf

    def update(self, dt, player=None, bullets_group=None):
        self.time  += dt
        self.pos.x += math.sin(self.time * self.zigzag_freq) * self.zigzag_amp * dt
        self.pos.y += self.speed
        self.pos.x  = max(14, min(WIDTH-14, self.pos.x))
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.rect.top > HEIGHT: self.kill()


class EnemyDestroyer(BaseEnemy):
    def __init__(self, x, y):
        super().__init__(x, y, DESTROYER_HP, DESTROYER_SPD, C_DESTROYER, 40)
        self.shoot_timer = 0
        self.shoot_delay = 2.5
        self.score_value = SCORE_DESTROYER

    def _build_surface(self, size, color):
        surf = pygame.Surface((size+10, size+16), pygame.SRCALPHA)
        cx   = (size+10) // 2
        # Halo orange
        blob = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(blob, (255,100,0,30), (size//2, size//2), size//2)
        surf.blit(blob, (5, 0))
        # Fuselage
        pygame.draw.polygon(surf, (200,80,0), [(cx,0),(5,size),(cx,size-8),(size+5,size)])
        pygame.draw.polygon(surf, color,      [(cx,4),(9,size-4),(cx,size-12),(size+1,size-4)])
        # Canon central
        pygame.draw.rect(surf, (100,40,0), (cx-3, size-4, 6, 12), border_radius=2)
        # Glow canon
        blob2 = pygame.Surface((10,10), pygame.SRCALPHA)
        pygame.draw.circle(blob2, (255,150,0,160), (5,5), 5)
        surf.blit(blob2, (cx-5, size+4))
        return surf

    def update(self, dt, player=None, bullets_group=None):
        self.pos.y += self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if bullets_group and player:
            self.shoot_timer += dt
            if self.shoot_timer >= self.shoot_delay:
                self.shoot_timer = 0
                self._shoot(player, bullets_group)
        if self.rect.top > HEIGHT: self.kill()

    def _shoot(self, player, bullets_group):
        from entities.bullet import EnemyBullet
        dx   = player.pos.x - self.pos.x
        dy   = player.pos.y - self.pos.y
        dist = math.hypot(dx, dy) or 1
        bullets_group.add(EnemyBullet(
            self.pos.x, self.pos.y+20,
            dx/dist * 4, dy/dist * 4
        ))


class EnemyCarrier(BaseEnemy):
    def __init__(self, x, y):
        super().__init__(x, y, CARRIER_HP, CARRIER_SPD, C_CARRIER, 55)
        self.spawn_timer    = 0
        self.spawn_interval = 8.0
        self.score_value    = SCORE_CARRIER

    def _build_surface(self, size, color):
        surf = pygame.Surface((size+20, size//2+20), pygame.SRCALPHA)
        cx   = (size+20) // 2
        cy   = (size//2+20) // 2
        # Halo violet
        blob = pygame.Surface((size+20, size//2+20), pygame.SRCALPHA)
        pygame.draw.ellipse(blob, (120, 0, 160, 25), (0,0,size+20, size//2+20))
        surf.blit(blob, (0, 0))
        # Corps principal
        pygame.draw.ellipse(surf, (100, 0, 140), (10, 4, size, size//2))
        pygame.draw.ellipse(surf, color,         (14, 7, size-8, size//2-8))
        # Bandes
        pygame.draw.rect(surf, (80, 0, 120), (cx-4, 2, 8, size//2+4))
        # Pods latéraux
        for pod_x in [6, size+14]:
            pygame.draw.circle(surf, (160, 0, 200), (pod_x, cy), 8)
            pygame.draw.circle(surf, (220, 80, 255), (pod_x, cy), 5)
            # Glow pod
            blob2 = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(blob2, (200, 0, 255, 60), (10, 10), 10)
            surf.blit(blob2, (pod_x-10, cy-10))
        # Noyau central
        pygame.draw.ellipse(surf, (220, 100, 255), (cx-10, cy-6, 20, 12))
        return surf

    def update(self, dt, player=None, enemies_group=None):
        self.pos.y += self.speed * 0.5
        self.pos.x += math.sin(pygame.time.get_ticks()*0.001) * 0.8
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if enemies_group:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                for offset in [-40, 40]:
                    enemies_group.add(EnemyDrone(self.pos.x+offset, self.pos.y+30))
        if self.rect.top > HEIGHT: self.kill()