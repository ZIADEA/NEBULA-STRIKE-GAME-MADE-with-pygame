# entities/elite_enemy.py
import pygame, math, random
from settings import *

class EliteState:
    PATROL  = 'patrol'
    CHASE   = 'chase'
    ATTACK  = 'attack'
    EVADE   = 'evade'
    RETREAT = 'retreat'

class EliteEnemy(pygame.sprite.Sprite):
    DETECTION_RADIUS    = 280
    BULLET_AVOID_RADIUS = 100

    def __init__(self, x, y, ps=None, sm=None):
        super().__init__()
        self.ps          = ps
        self.sm          = sm
        self.hp          = 80
        self.max_hp      = 80
        self.state       = EliteState.PATROL
        self.pos         = pygame.math.Vector2(x, y)
        self.vel         = pygame.math.Vector2(1.5, 0)
        self.score_value = 800

        # Timers FSM
        self.attack_timer = 0
        self.state_timer  = 0
        self.evade_dir    = 1

        self.image = self._build_surface()
        self.rect  = self.image.get_rect(center=(x, y))

    def _build_surface(self):
        s = pygame.Surface((38, 38), pygame.SRCALPHA)
        pygame.draw.polygon(s, (200,0,200), [(19,0),(38,28),(19,22),(0,28)])
        pygame.draw.circle(s, (255,150,255), (19,19), 7)
        pygame.draw.line(s, (255,0,255), (0,0),  (7,7),  2)
        pygame.draw.line(s, (255,0,255), (38,0), (31,7), 2)
        return s

    def update(self, dt, player, bullets_group, p_bullets):
        self.state_timer += dt
        prev_state        = self.state

        # ══ TRANSITIONS D'ÉTAT ══════════════════════════
        dist_to_player = self.pos.distance_to(player.pos)
        nearest_bullet = self._nearest_bullet(p_bullets)

        # Priorité 1 : Esquiver une balle proche
        if nearest_bullet and nearest_bullet < self.BULLET_AVOID_RADIUS:
            if self.state != EliteState.EVADE:
                self.state       = EliteState.EVADE
                self.state_timer = 0
                self.evade_dir   = 1 if random.random() > 0.5 else -1

        # Priorité 2 : Retraite si HP faible
        elif self.hp / self.max_hp < 0.4:
            self.state = EliteState.RETREAT

        # Priorité 3 : Attaque si proche
        elif dist_to_player < self.DETECTION_RADIUS * 0.6:
            if self.state not in (EliteState.ATTACK, EliteState.EVADE):
                self.state       = EliteState.ATTACK
                self.state_timer = 0

        # Priorité 4 : Poursuite si détecté
        elif dist_to_player < self.DETECTION_RADIUS:
            if self.state == EliteState.PATROL:
                self.state = EliteState.CHASE

        # Retour patrouille si joueur perdu
        elif self.state == EliteState.CHASE and \
             dist_to_player > self.DETECTION_RADIUS * 1.3:
            self.state = EliteState.PATROL

        # Fin esquive après 0.6s
        if self.state == EliteState.EVADE and self.state_timer > 0.6:
            self.state = EliteState.CHASE if \
                dist_to_player < self.DETECTION_RADIUS else EliteState.PATROL

        # ══ COMPORTEMENTS PAR ÉTAT ══════════════════════
        if   self.state == EliteState.PATROL:  self._do_patrol(dt)
        elif self.state == EliteState.CHASE:   self._do_chase(dt, player)
        elif self.state == EliteState.ATTACK:  self._do_attack(dt, player, bullets_group)
        elif self.state == EliteState.EVADE:   self._do_evade(dt)
        elif self.state == EliteState.RETREAT: self._do_retreat(dt)

        # Log transition
        if self.state != prev_state:
            print(f'[Elite] {prev_state} → {self.state} | HP={self.hp}')

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        # Despawn si sort par le bas ou par le haut (retraite finie)
        if self.rect.top > HEIGHT + 60 or self.pos.y < -300:
            self.kill()

    # ── Comportements ───────────────────────────────────
    def _do_patrol(self, dt):
        # Si hors écran en haut, descendre jusqu'à entrer dans le champ de jeu
        if self.pos.y < 60:
            self.pos.y += 2.0
        else:
            self.pos.y += math.sin(pygame.time.get_ticks() * 0.002) * 0.5
        self.pos.x += self.vel.x * 1.5
        if self.pos.x < 30 or self.pos.x > WIDTH - 30:
            self.vel.x *= -1

    def _do_chase(self, dt, player):
        direction = player.pos - self.pos
        if direction.length() > 0:
            self.pos += direction.normalize() * 3.0

    def _do_attack(self, dt, player, bullets_group):
        # Reste sur place, tir triple toutes les 0.8s
        self.attack_timer += dt
        if self.attack_timer >= 0.8:
            self.attack_timer = 0
            self._aimed_shot(player, bullets_group)
            self._aimed_shot(player, bullets_group, spread=15)
            self._aimed_shot(player, bullets_group, spread=-15)

    def _do_evade(self, dt):
        self.pos.x += self.evade_dir * 5
        self.pos.x  = max(30, min(WIDTH-30, self.pos.x))

    def _do_retreat(self, dt):
        self.pos.y -= 1.5   # reculer vers le haut

    # ── Utilitaires ─────────────────────────────────────
    def _nearest_bullet(self, p_bullets):
        min_dist = float('inf')
        for b in p_bullets:
            d = self.pos.distance_to(pygame.math.Vector2(b.rect.center))
            if d < min_dist:
                min_dist = d
        return min_dist if min_dist < float('inf') else None

    def _aimed_shot(self, player, bullets_group, spread=0):
        from entities.bullet import EnemyBullet
        dx    = player.pos.x - self.pos.x
        dy    = player.pos.y - self.pos.y
        angle = math.atan2(dy, dx) + math.radians(spread)
        bullets_group.add(EnemyBullet(
            self.pos.x, self.pos.y,
            math.cos(angle) * 4.5,
            math.sin(angle) * 4.5
        ))

    def take_damage(self, dmg, ps=None):
        self.hp -= dmg
        if ps:
            ps.spawn_explosion(self.pos.x, self.pos.y, (200,0,200), count=6, speed=2)
        return self.hp <= 0

    def draw_health_bar(self, surface):
        w     = self.rect.width
        ratio = max(0, self.hp / self.max_hp)
        bar   = pygame.Rect(self.rect.left, self.rect.top - 8, w, 5)
        pygame.draw.rect(surface, (80,0,0),   bar)
        pygame.draw.rect(surface, (220,50,50),(bar.x, bar.y, int(w*ratio), 5))