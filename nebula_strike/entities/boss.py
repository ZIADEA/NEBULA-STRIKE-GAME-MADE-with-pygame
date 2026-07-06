# entities/boss.py
import pygame, math, random
from settings import *

class BossState:
    ENTER  = 'enter'
    PHASE1 = 'phase1'
    PHASE2 = 'phase2'
    PHASE3 = 'phase3'
    DEAD   = 'dead'

class Boss(pygame.sprite.Sprite):
    def __init__(self, particle_system, sound_manager):
        super().__init__()
        self.ps          = particle_system
        self.sm          = sound_manager
        self.hp          = BOSS_HP
        self.max_hp      = BOSS_HP
        self.state       = BossState.ENTER
        self.pos         = pygame.math.Vector2(WIDTH//2, -100)
        self.target_y    = 130
        self.score_value = SCORE_BOSS
        self.shoot_timer = 0
        self.death_timer = 0
        self.flash_timer = 0      # flash blanc quand touché
        self.fire_timer  = 0      # particules de feu en phase 3
        self.image_base  = self._build_surface()
        self.image       = self.image_base.copy()
        self.rect        = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _build_surface(self):
        w, h = 140, 100
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx   = w // 2

        # ── Corps central métallique (ellipse grise)
        pygame.draw.ellipse(surf, (90, 90, 110),  (cx-45, 15, 90, 70))
        pygame.draw.ellipse(surf, (130,130,160),  (cx-38, 20, 76, 58))
        pygame.draw.ellipse(surf, (160,160,200),  (cx-28, 28, 56, 40))

        # ── Pods latéraux orange/jaune (pattes de crabe)
        for sign, px in [(-1, 4), (1, w-4)]:
            # Bras horizontal
            pygame.draw.ellipse(surf, (200, 90, 0),  (min(cx, px)-32, 30, 64, 22))
            pygame.draw.ellipse(surf, (255,140, 0),  (min(cx, px)-28, 33, 56, 16))
            # Pod moteur rond
            pod_cx = 14 if sign < 0 else w-14
            pygame.draw.circle(surf, (180, 70, 0),  (pod_cx, 45), 22)
            pygame.draw.circle(surf, (255,150, 0),  (pod_cx, 45), 16)
            pygame.draw.circle(surf, (255,220, 80), (pod_cx, 45), 8)
            # Halo pod
            for r, a in [(22, 30), (16, 60)]:
                blob = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(blob, (255, 120, 0, a), (r, r), r)
                surf.blit(blob, (pod_cx-r, 45-r))

        # ── Bande centrale verticale
        pygame.draw.rect(surf, (80, 0, 60),   (cx-12,  0, 24, h))
        pygame.draw.rect(surf, (150, 0,100),  (cx-8,   5, 16, h-10))

        # ── Noyau central lumineux (core)
        for r, col, a in [(18,(255,50,150),80),(12,(255,100,180),150),(7,(255,200,230),220)]:
            blob = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(blob, (*col, a), (r, r), r)
            surf.blit(blob, (cx-r, h//2-r))

        # ── Canons inférieurs
        for dx in [-20, 0, 20]:
            pygame.draw.rect(surf, (60, 60, 80), (cx+dx-4, h-18, 8, 18), border_radius=2)
            pygame.draw.circle(surf, (0, 200, 255, 150), (cx+dx, h-4), 5)

        return surf

    def draw_health_bar(self, surface):
        ratio  = max(0, self.hp / self.max_hp)
        bar_w  = 400
        bar_x  = (WIDTH - bar_w) // 2
        bar_y  = HEIGHT - 36
        font   = pygame.font.SysFont('consolas', 18, bold=True)
        lbl    = font.render('— B O S S —', True, C_BOSS)
        surface.blit(lbl, (WIDTH//2 - lbl.get_width()//2, bar_y - 24))
        pygame.draw.rect(surface, (60, 0, 20),    (bar_x, bar_y, bar_w, 18), border_radius=4)
        color = C_BOSS if ratio > 0.3 else (255, 140, 0)
        pygame.draw.rect(surface, color,          (bar_x, bar_y, int(bar_w*ratio), 18), border_radius=4)
        pygame.draw.rect(surface, (255, 100, 150),(bar_x, bar_y, bar_w, 18), 2, border_radius=4)
        # Glow sur la barre
        glow = pygame.Surface((bar_w, 6), pygame.SRCALPHA)
        glow.fill((255, 150, 200, 80))
        surface.blit(glow, (bar_x, bar_y))

    def update(self, dt, player, all_bullets, particle_system):
        if   self.state == BossState.ENTER:  self._update_enter(dt)
        elif self.state == BossState.PHASE1: self._update_phase1(dt, player, all_bullets)
        elif self.state == BossState.PHASE2: self._update_phase2(dt, player, all_bullets)
        elif self.state == BossState.PHASE3: self._update_phase3(dt, player, all_bullets)
        elif self.state == BossState.DEAD:   self._update_dead(dt)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Flash blanc quand touché
        if self.flash_timer > 0:
            self.flash_timer -= dt
            flash = self.image_base.copy()
            overlay = pygame.Surface(flash.get_size(), pygame.SRCALPHA)
            alpha = max(0, min(200, int(self.flash_timer * 600)))
            overlay.fill((255, 255, 255, alpha))
            flash.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = flash
        else:
            self.image = self.image_base.copy()

        # Feu continu en phase 3 (HP < 50%)
        if self.hp / self.max_hp < 0.5:
            self.fire_timer += dt
            if self.fire_timer > 0.04:
                self.fire_timer = 0
                ox = random.randint(-45, 45)
                particle_system.spawn_explosion(
                    self.pos.x + ox, self.pos.y + 40,
                    (255, random.randint(80, 180), 0),
                    count=3, speed=1.5
                )

        self._check_transition()

    def _update_enter(self, dt):
        self.pos.y = min(self.target_y, self.pos.y + 2)
        if self.pos.y >= self.target_y:
            self.state = BossState.PHASE1

    def _update_phase1(self, dt, player, all_bullets):
        self.pos.x += math.sin(pygame.time.get_ticks() * 0.002) * 2
        self.pos.x  = max(80, min(WIDTH-80, self.pos.x))
        self.shoot_timer += dt
        if self.shoot_timer >= 1.5:
            self.shoot_timer = 0
            self._shoot_fan(all_bullets, count=7)

    def _update_phase2(self, dt, player, all_bullets):
        self.pos.x += math.sin(pygame.time.get_ticks() * 0.003) * 2.5
        self.pos.y  = 120 + math.sin(pygame.time.get_ticks() * 0.001) * 40
        self.shoot_timer += dt
        if self.shoot_timer >= 0.8:
            self.shoot_timer = 0
            self._shoot_aimed(player, all_bullets)

    def _update_phase3(self, dt, player, all_bullets):
        self.pos.x += math.sin(pygame.time.get_ticks() * 0.005) * 4
        self.pos.x  = max(80, min(WIDTH-80, self.pos.x))
        self.shoot_timer += dt
        if self.shoot_timer >= 0.5:
            self.shoot_timer = 0
            self._shoot_fan(all_bullets, count=12)
            self._shoot_aimed(player, all_bullets)
        self.ps.spawn_explosion(
            self.pos.x + random.randint(-40,40),
            self.pos.y + random.randint(-20,20),
            (255,50,50), count=3, speed=1.5
        )

    def _update_dead(self, dt):
        self.death_timer += dt
        for _ in range(5):
            ox = random.randint(-50, 50)
            oy = random.randint(-30, 30)
            self.ps.spawn_explosion(self.pos.x+ox, self.pos.y+oy, C_BOSS, count=15, speed=4)
        if self.death_timer > 2.5:
            self.kill()

    def _shoot_fan(self, bullets, count=7):
        from entities.bullet import EnemyBullet
        for i in range(count):
            angle = math.pi/2 + (i - count//2) * math.pi / (count*2)
            bullets.add(EnemyBullet(
                self.pos.x, self.pos.y+40,
                math.cos(angle)*3.5, math.sin(angle)*3.5
            ))

    def _shoot_aimed(self, player, bullets):
        from entities.bullet import EnemyBullet
        dx   = player.pos.x - self.pos.x
        dy   = player.pos.y - self.pos.y
        dist = math.hypot(dx, dy) or 1
        bullets.add(EnemyBullet(
            self.pos.x, self.pos.y+40,
            dx/dist*5, dy/dist*5
        ))

    def take_damage(self, dmg):
        if self.state == BossState.DEAD: return False
        self.hp -= dmg
        self.flash_timer = 0.12   # flash blanc
        self.ps.spawn_explosion(self.pos.x, self.pos.y, C_BOSS, count=5, speed=2)
        return self.hp <= 0

    def _check_transition(self):
        ratio = self.hp / self.max_hp
        if self.state == BossState.PHASE1 and ratio < 0.6:
            self.state = BossState.PHASE2
            self.sm.play('boss_phase')
        elif self.state == BossState.PHASE2 and ratio < 0.3:
            self.state = BossState.PHASE3
            self.sm.play('boss_phase')
        elif ratio <= 0 and self.state != BossState.DEAD:
            self.state = BossState.DEAD
            self.sm.play('boss_die')