# systems/particles.py
import pygame, random, math
from settings import MAX_PARTICLES

class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','color','size']

    def __init__(self, x, y, vx, vy, life, color, size=3):
        self.x, self.y       = float(x), float(y)
        self.vx, self.vy     = float(vx), float(vy)
        self.life            = float(life)
        self.max_life        = float(life)
        self.color           = color
        self.size            = size

    def update(self, dt):
        self.x    += self.vx * dt * 60
        self.y    += self.vy * dt * 60
        self.vy   += 0.05 * dt * 60   # légère gravité
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, self.life / self.max_life)
        size  = max(1, int(self.size * alpha))
        r, g, b = self.color
        r = int(r * alpha + 40 * (1 - alpha))
        g = int(g * alpha * 0.6)
        b = int(b * alpha)
        pygame.draw.circle(
            surface,
            (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b))),
            (int(self.x), int(self.y)),
            size
        )

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_explosion(self, x, y, color, count=40, speed=4):
        for _ in range(min(count, MAX_PARTICLES - len(self.particles))):
            angle = random.uniform(0, math.tau)
            spd   = random.uniform(speed * 0.3, speed)
            size  = random.uniform(2, 6)
            life  = random.uniform(0.3, 0.9)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                life, color, size
            ))

    def spawn_trail(self, x, y, color=(0, 150, 255)):
        vx = random.uniform(-0.5, 0.5)
        vy = random.uniform(0.5, 2.0)
        self.particles.append(Particle(x, y, vx, vy, 0.25, color, 2))

    def spawn_emp(self, x, y, radius=120):
        for i in range(60):
            angle = i * math.tau / 60
            spd   = radius / 0.5
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * spd / 60,
                math.sin(angle) * spd / 60,
                0.5, (0, 255, 200), 3
            ))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)