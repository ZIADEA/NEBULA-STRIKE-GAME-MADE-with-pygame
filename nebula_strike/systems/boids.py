# systems/boids.py
import pygame, math, random
from settings import WIDTH, HEIGHT

class Boid(pygame.sprite.Sprite):
    MAX_SPEED      = 3.0
    MAX_FORCE      = 0.1
    SEPARATION_DIST= 40
    ALIGNMENT_DIST = 80
    COHESION_DIST  = 100
    PLAYER_SEEK_DIST=300
    W_SEPARATION   = 1.8
    W_ALIGNMENT    = 1.0
    W_COHESION     = 1.0
    W_PLAYER       = 1.5

    def __init__(self, x, y):
        super().__init__()
        self.pos         = pygame.math.Vector2(x, y)
        self.vel         = pygame.math.Vector2(
            random.uniform(-1,1), random.uniform(-1,1)
        ).normalize() * 2
        self.acc         = pygame.math.Vector2(0, 0)
        self.hp          = 15
        self.max_hp      = 15
        self.score_value = 150

        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (255,100,0),
                            [(10,0),(20,18),(10,14),(0,18)])
        self.rect  = self.image.get_rect(center=(x, y))

    def update(self, dt, all_boids, player):
        neighbors = [b for b in all_boids
                     if b is not self and
                     self.pos.distance_to(b.pos) < self.COHESION_DIST]

        sep  = self._separation(neighbors) * self.W_SEPARATION
        ali  = self._alignment(neighbors)  * self.W_ALIGNMENT
        coh  = self._cohesion(neighbors)   * self.W_COHESION
        seek = self._seek_player(player)   * self.W_PLAYER

        self.acc  = sep + ali + coh + seek
        self.vel += self.acc

        # Limiter la vitesse
        if self.vel.length() > self.MAX_SPEED:
            self.vel = self.vel.normalize() * self.MAX_SPEED

        self.pos += self.vel

        # Wrap horizontal
        if self.pos.x < 0:      self.pos.x = WIDTH
        if self.pos.x > WIDTH:  self.pos.x = 0
        if self.pos.y > HEIGHT + 50: self.kill()

        # Rotation du sprite
        angle      = -math.degrees(math.atan2(self.vel.y, self.vel.x)) - 90
        orig       = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.polygon(orig, (255,100,0), [(10,0),(20,18),(10,14),(0,18)])
        self.image = pygame.transform.rotate(orig, angle)
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _separation(self, neighbors):
        steer = pygame.math.Vector2(0, 0)
        count = 0
        for n in neighbors:
            d = self.pos.distance_to(n.pos)
            if 0 < d < self.SEPARATION_DIST:
                diff   = (self.pos - n.pos).normalize() / d
                steer += diff
                count += 1
        if count > 0:
            steer /= count
            if steer.length() > 0:
                steer = steer.normalize() * self.MAX_SPEED - self.vel
                steer = self._limit(steer, self.MAX_FORCE)
        return steer

    def _alignment(self, neighbors):
        avg_vel = pygame.math.Vector2(0, 0)
        count   = 0
        for n in neighbors:
            if self.pos.distance_to(n.pos) < self.ALIGNMENT_DIST:
                avg_vel += n.vel
                count   += 1
        if count > 0:
            avg_vel /= count
            if avg_vel.length() > 0:
                avg_vel = avg_vel.normalize() * self.MAX_SPEED
            return self._limit(avg_vel - self.vel, self.MAX_FORCE)
        return pygame.math.Vector2(0, 0)

    def _cohesion(self, neighbors):
        center = pygame.math.Vector2(0, 0)
        count  = 0
        for n in neighbors:
            if self.pos.distance_to(n.pos) < self.COHESION_DIST:
                center += n.pos
                count  += 1
        if count > 0:
            center /= count
            return self._seek(center)
        return pygame.math.Vector2(0, 0)

    def _seek_player(self, player):
        d = self.pos.distance_to(player.pos)
        if d < self.PLAYER_SEEK_DIST:
            return self._seek(player.pos)
        return self._seek(pygame.math.Vector2(self.pos.x, self.pos.y + 200))

    def _seek(self, target):
        desired = target - self.pos
        if desired.length() > 0:
            desired = desired.normalize() * self.MAX_SPEED
        return self._limit(desired - self.vel, self.MAX_FORCE)

    def _limit(self, vec, max_len):
        if vec.length() > max_len:
            return vec.normalize() * max_len
        return vec

    def take_damage(self, dmg, ps=None):
        self.hp -= dmg
        if ps:
            ps.spawn_explosion(self.pos.x, self.pos.y, (255,100,0), count=5, speed=2)
        return self.hp <= 0

    def draw_health_bar(self, surface):
        w     = self.rect.width
        ratio = max(0, self.hp / self.max_hp)
        bar   = pygame.Rect(self.rect.left, self.rect.top - 8, w, 5)
        pygame.draw.rect(surface, (80,0,0),    bar)
        pygame.draw.rect(surface, (255,100,0), (bar.x, bar.y, int(w*ratio), 5))