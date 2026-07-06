# entities/mega_boss.py — MEGA BOSS — Vague 10
# Inspiré des boss de fin des vrais shoot'em up (DoDonPachi, 1942, Gradius)
import pygame, math, random
from settings import *


class MegaBossState:
    ENTER  = 'enter'
    PHASE1 = 'phase1'   # 100-70% HP : Fan lent + sinusoïdale
    PHASE2 = 'phase2'   #  70-50% HP : Fan + aiméd + spawn drones
    PHASE3 = 'phase3'   #  50-30% HP : Spirale + double ciblé
    PHASE4 = 'phase4'   #  30-10% HP : Berserk total + drones fréquents
    PHASE5 = 'phase5'   #  10- 0% HP : RAGE — tout simultané très rapide
    DEAD   = 'dead'


class MegaBoss(pygame.sprite.Sprite):
    """Boss monstrueux de la vague 10 — 5 phases de terreur."""

    def __init__(self, particle_system, sound_manager):
        super().__init__()
        self.ps          = particle_system
        self.sm          = sound_manager
        self.hp          = MEGA_BOSS_HP
        self.max_hp      = MEGA_BOSS_HP
        self.state       = MegaBossState.ENTER
        self.pos         = pygame.math.Vector2(WIDTH // 2, -160)
        self.target_y    = 160
        self.score_value = SCORE_MEGA_BOSS

        # Timers d'attaque
        self.fan_timer      = 0
        self.aim_timer      = 0
        self.spiral_timer   = 0
        self.drone_timer    = 0
        self.death_timer    = 0
        self.flash_timer    = 0
        self.fire_timer     = 0
        self.cross_timer    = 0   # tir en croix
        self.laser_timer    = 0   # laser tracking (phase 5)
        self.laser_charging = False
        self.laser_charge_t = 0
        self.laser_target_x = WIDTH // 2

        # Angle courant pour les spirales
        self.spiral_angle = 0

        # Surface de base (reconstruite à la mort flash)
        self.image_base = self._build_surface()
        self.image      = self.image_base.copy()
        self.rect       = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    # ── Construction visuelle ─────────────────────────────────────────────
    def _build_surface(self):
        w, h = 220, 160
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2

        # ── Ailes énergétiques (gradient violet → transparent)
        for i in range(5):
            alpha = int(80 - i * 14)
            wing_w = 90 + i * 12
            blob = pygame.Surface((wing_w * 2, 30), pygame.SRCALPHA)
            blob.fill((120, 0, 180, max(0, alpha)))
            surf.blit(blob, (cx - wing_w, cy - 15 + i * 4))

        # ── Corps principal — hexagone sombre
        pygame.draw.polygon(surf, (30, 10, 50), [
            (cx, 0), (cx+70, 40), (cx+80, cy), (cx+70, h-40),
            (cx, h),  (cx-70, h-40), (cx-80, cy), (cx-70, 40)
        ])
        pygame.draw.polygon(surf, (60, 20, 90), [
            (cx, 10), (cx+55, 45), (cx+65, cy), (cx+55, h-45),
            (cx, h-10), (cx-55, h-45), (cx-65, cy), (cx-55, 45)
        ])

        # ── Armure centrale (plaques métalliques)
        pygame.draw.ellipse(surf, (80, 30, 120),  (cx-50, cy-35, 100, 70))
        pygame.draw.ellipse(surf, (120, 50, 180), (cx-38, cy-25, 76, 50))

        # ── Turbines latérales ×2
        for sign, tx in [(-1, 22), (1, w - 22)]:
            pygame.draw.circle(surf, (50, 0, 80),    (tx, cy), 30)
            pygame.draw.circle(surf, (100, 0, 160),  (tx, cy), 22)
            pygame.draw.circle(surf, (180, 0, 255),  (tx, cy), 14)
            pygame.draw.circle(surf, (220, 100, 255),(tx, cy), 7)
            # Halo turbine
            for r, a in [(30, 25), (22, 55), (14, 90)]:
                blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(blob, (160, 0, 255, a), (r, r), r)
                surf.blit(blob, (tx - r, cy - r))

        # ── Tourelles supérieures ×3
        for tx in [cx - 55, cx, cx + 55]:
            pygame.draw.rect(surf, (50, 50, 70), (tx - 7, 5, 14, 28), border_radius=3)
            pygame.draw.rect(surf, (90, 90, 120), (tx - 5, 7, 10, 20), border_radius=2)
            pygame.draw.circle(surf, (0, 220, 255, 180), (tx, 5), 6)

        # ── Canons inférieurs ×4
        for tx in [cx - 40, cx - 14, cx + 14, cx + 40]:
            pygame.draw.rect(surf, (60, 60, 80), (tx - 5, h - 22, 10, 22), border_radius=2)
            pygame.draw.circle(surf, (255, 50, 80, 200), (tx, h - 4), 6)

        # ── ŒIL CENTRAL — core pulsant
        for r, col, a in [
            (28, (100, 0, 60), 60),
            (20, (200, 0, 80), 100),
            (13, (255, 50, 150), 180),
            (7,  (255, 200, 230), 255),
        ]:
            blob = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(blob, (*col, a), (r, r), r)
            surf.blit(blob, (cx - r, cy - r))

        # ── Bande centrale rouge
        pygame.draw.rect(surf, (120, 0, 40), (cx - 8, 0, 16, h))
        pygame.draw.rect(surf, (200, 0, 60), (cx - 4, 5, 8, h - 10))

        return surf

    # ── Barre de vie ──────────────────────────────────────────────────────
    def draw_health_bar(self, surface):
        ratio  = max(0, self.hp / self.max_hp)
        bar_w  = 500
        bar_x  = (WIDTH - bar_w) // 2
        bar_y  = HEIGHT - 36
        font   = pygame.font.SysFont('consolas', 18, bold=True)

        # Phase indicator
        phase_labels = {
            MegaBossState.PHASE1: '▶ PHASE I',
            MegaBossState.PHASE2: '▶▶ PHASE II',
            MegaBossState.PHASE3: '▶▶▶ PHASE III',
            MegaBossState.PHASE4: '▶▶▶▶ PHASE IV',
            MegaBossState.PHASE5: '▶▶▶▶▶ PHASE RAGE',
        }
        lbl = font.render(f'MEGA BOSS  {phase_labels.get(self.state, "")}', True, (255, 50, 150))
        surface.blit(lbl, (WIDTH // 2 - lbl.get_width() // 2, bar_y - 26))

        pygame.draw.rect(surface, (40, 0, 20),   (bar_x, bar_y, bar_w, 20), border_radius=5)

        # Couleur barre selon ratio HP
        if   ratio > 0.7: bar_color = (180, 0, 120)
        elif ratio > 0.5: bar_color = (200, 50, 0)
        elif ratio > 0.3: bar_color = (255, 120, 0)
        elif ratio > 0.1: bar_color = (255, 200, 0)
        else:              bar_color = (255, 50, 50)

        pygame.draw.rect(surface, bar_color,     (bar_x, bar_y, int(bar_w * ratio), 20), border_radius=5)
        pygame.draw.rect(surface, (255, 50, 150),(bar_x, bar_y, bar_w, 20), 2, border_radius=5)

        # Glow
        glow = pygame.Surface((bar_w, 8), pygame.SRCALPHA)
        glow.fill((255, 80, 180, 70))
        surface.blit(glow, (bar_x, bar_y))

        # Avertissement laser : ligne rouge clignotante sur la colonne ciblée
        if self.laser_charging:
            warn_alpha = int(abs(math.sin(self.laser_charge_t * 14)) * 220)
            warn_surf  = pygame.Surface((6, HEIGHT), pygame.SRCALPHA)
            warn_surf.fill((255, 20, 20, warn_alpha))
            tx = max(3, min(WIDTH - 3, int(self.laser_target_x)))
            surface.blit(warn_surf, (tx - 3, 0))

    # ── Update principal ──────────────────────────────────────────────────
    def update(self, dt, player, all_bullets, particle_system):
        dispatch = {
            MegaBossState.ENTER:  self._update_enter,
            MegaBossState.PHASE1: self._update_phase1,
            MegaBossState.PHASE2: self._update_phase2,
            MegaBossState.PHASE3: self._update_phase3,
            MegaBossState.PHASE4: self._update_phase4,
            MegaBossState.PHASE5: self._update_phase5,
            MegaBossState.DEAD:   self._update_dead,
        }
        dispatch[self.state](dt, player, all_bullets)

        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Flash rouge quand touché (priorité sur le laser)
        if self.flash_timer > 0:
            self.flash_timer -= dt
            flash   = self.image_base.copy()
            overlay = pygame.Surface(flash.get_size(), pygame.SRCALPHA)
            r_alpha = max(0, min(220, int(self.flash_timer * 700)))
            overlay.fill((255, 0, 0, r_alpha))
            flash.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = flash
            self.image.set_alpha(255)
        elif self.laser_charging:
            # Clignotement rouge pendant la charge du laser
            blink_on = int(self.laser_charge_t * 14) % 2 == 0
            self.image = self.image_base.copy()
            if blink_on:
                overlay = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                overlay.fill((255, 0, 80, 160))
                self.image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            self.image = self.image_base.copy()

        # Feu continu à partir de 50% HP
        if self.hp / self.max_hp < 0.5 and self.state not in (MegaBossState.DEAD, MegaBossState.ENTER):
            self.fire_timer += dt
            if self.fire_timer > 0.03:
                self.fire_timer = 0
                for _ in range(2):
                    ox = random.randint(-70, 70)
                    particle_system.spawn_explosion(
                        self.pos.x + ox, self.pos.y + 60,
                        (255, random.randint(60, 200), 0), count=3, speed=1.5
                    )

        self._check_transition()

    def _update_enter(self, dt, player, bullets):
        speed = 1.5 if self.pos.y < self.target_y - 20 else 0.5
        self.pos.y = min(self.target_y, self.pos.y + speed)
        if self.pos.y >= self.target_y:
            self.state = MegaBossState.PHASE1
            self.sm.play('boss_phase')

    # PHASE 1 — fan lent, mouvement sinusoïdal (100-70% HP)
    def _update_phase1(self, dt, player, bullets):
        t = pygame.time.get_ticks() * 0.001
        self.pos.x = WIDTH // 2 + math.sin(t * 0.6) * 180
        self.pos.x = max(120, min(WIDTH - 120, self.pos.x))
        self.pos.y = self.target_y + math.sin(t * 0.4) * 20

        self.fan_timer += dt
        if self.fan_timer >= 1.2:
            self.fan_timer = 0
            self._shoot_fan(bullets, count=10, speed=3.8)

        self.aim_timer += dt
        if self.aim_timer >= 2.0:
            self.aim_timer = 0
            self._shoot_aimed(player, bullets, speed=4.5)

    # PHASE 2 — fan + tir ciblé en rafale + spawn drones (70-50% HP)
    def _update_phase2(self, dt, player, bullets):
        t = pygame.time.get_ticks() * 0.001
        self.pos.x = WIDTH // 2 + math.sin(t * 0.9) * 200
        self.pos.x = max(110, min(WIDTH - 110, self.pos.x))

        self.fan_timer += dt
        if self.fan_timer >= 0.9:
            self.fan_timer = 0
            self._shoot_fan(bullets, count=12, speed=4.2)

        self.aim_timer += dt
        if self.aim_timer >= 0.7:
            self.aim_timer = 0
            self._shoot_aimed(player, bullets, speed=5.2)
            self._shoot_aimed(player, bullets, speed=5.2, offset=-18)
            self._shoot_aimed(player, bullets, speed=5.2, offset=18)

        self.drone_timer += dt
        if self.drone_timer >= 15.0:
            self.drone_timer = 0
            self._spawn_drones(bullets)

        # Tirs en croix (4 directions)
        self.cross_timer += dt
        if self.cross_timer >= 2.5:
            self.cross_timer = 0
            self._shoot_cross(bullets, speed=4.0)

    # PHASE 3 — spirale double + tirs ciblés × 3 + croix (50-30% HP)
    def _update_phase3(self, dt, player, bullets):
        t = pygame.time.get_ticks() * 0.001
        self.pos.x = WIDTH // 2 + math.sin(t * 1.2) * 220
        self.pos.y = self.target_y + math.sin(t * 0.8) * 50
        self.pos.x = max(100, min(WIDTH - 100, self.pos.x))

        self.spiral_timer += dt
        if self.spiral_timer >= 0.06:
            self.spiral_timer = 0
            self._shoot_spiral(bullets, arms=3)
            self._shoot_spiral(bullets, arms=3)   # double spirale décalée

        self.aim_timer += dt
        if self.aim_timer >= 0.55:
            self.aim_timer = 0
            for off in [-20, 0, 20]:
                self._shoot_aimed(player, bullets, speed=5.8, offset=off)

        self.cross_timer += dt
        if self.cross_timer >= 1.8:
            self.cross_timer = 0
            self._shoot_cross(bullets, speed=5.0)

        self.drone_timer += dt
        if self.drone_timer >= 12.0:
            self.drone_timer = 0
            self._spawn_drones(bullets)

    # PHASE 4 — berserk total : tout simultané + laser (30-10% HP)
    def _update_phase4(self, dt, player, bullets):
        t = pygame.time.get_ticks() * 0.001
        self.pos.x = WIDTH // 2 + math.sin(t * 1.8) * 230 + math.cos(t * 3.0) * 40
        self.pos.y = self.target_y + math.sin(t * 1.2) * 70
        self.pos.x = max(90, min(WIDTH - 90, self.pos.x))

        self.fan_timer += dt
        if self.fan_timer >= 0.6:
            self.fan_timer = 0
            self._shoot_fan(bullets, count=16, speed=5.0)

        self.spiral_timer += dt
        if self.spiral_timer >= 0.05:
            self.spiral_timer = 0
            self._shoot_spiral(bullets, arms=5)

        self.aim_timer += dt
        if self.aim_timer >= 0.45:
            self.aim_timer = 0
            for off in [-30, -10, 10, 30]:
                self._shoot_aimed(player, bullets, speed=6.2, offset=off)

        self.drone_timer += dt
        if self.drone_timer >= 10.0:
            self.drone_timer = 0
            self._spawn_drones(bullets)

        # LASER TRACKING — se charge 1.5s puis tire une salve verticale
        self.laser_timer += dt
        if not self.laser_charging and self.laser_timer >= 5.0:
            self.laser_charging  = True
            self.laser_charge_t  = 0
            self.laser_target_x  = player.pos.x
            self.laser_timer     = 0
        if self.laser_charging:
            self.laser_charge_t += dt
            if self.laser_charge_t >= 1.5:
                self.laser_charging = False
                self._shoot_laser_column(self.laser_target_x, bullets)

    # PHASE 5 — RAGE ABSOLUTE (10-0% HP) : infernale, inspirée de DoDonPachi
    def _update_phase5(self, dt, player, bullets):
        t = pygame.time.get_ticks() * 0.001
        # Tremblement de rage
        shake = 5
        self.pos.x = WIDTH // 2 + math.sin(t * 3.5) * 240 + random.randint(-shake, shake)
        self.pos.y = self.target_y + math.sin(t * 2.2) * 90 + random.randint(-shake, shake)
        self.pos.x = max(80, min(WIDTH - 80, self.pos.x))

        # Fan ultra-dense
        self.fan_timer += dt
        if self.fan_timer >= 0.38:
            self.fan_timer = 0
            self._shoot_fan(bullets, count=20, speed=5.5)

        # Spirale à 8 bras
        self.spiral_timer += dt
        if self.spiral_timer >= 0.035:
            self.spiral_timer = 0
            self._shoot_spiral(bullets, arms=8)

        # Tirs ciblés en éventail × 4
        self.aim_timer += dt
        if self.aim_timer >= 0.30:
            self.aim_timer = 0
            for off in [-40, -15, 15, 40]:
                self._shoot_aimed(player, bullets, speed=7.0, offset=off)

        # Spawn drones fréquent
        self.drone_timer += dt
        if self.drone_timer >= 6.0:
            self.drone_timer = 0
            self._spawn_drones(bullets)
            self.spawn_drones_request = 6   # plus de drones

        # Croix de feu
        self.cross_timer += dt
        if self.cross_timer >= 1.0:
            self.cross_timer = 0
            self._shoot_cross(bullets, speed=6.0)

        # Lasers frénétiques
        self.laser_timer += dt
        if not self.laser_charging and self.laser_timer >= 3.0:
            self.laser_charging  = True
            self.laser_charge_t  = 0
            self.laser_target_x  = player.pos.x
            self.laser_timer     = 0
        if self.laser_charging:
            self.laser_charge_t += dt
            if self.laser_charge_t >= 1.0:
                self.laser_charging = False
                # Triple laser
                for off in [-60, 0, 60]:
                    self._shoot_laser_column(self.laser_target_x + off, bullets)

    def _update_dead(self, dt, player, bullets):
        self.death_timer += dt
        for _ in range(8):
            ox = random.randint(-80, 80)
            oy = random.randint(-50, 50)
            self.ps.spawn_explosion(
                self.pos.x + ox, self.pos.y + oy,
                random.choice([(255, 50, 150), (255, 120, 0), (180, 0, 255)]),
                count=20, speed=5
            )
        if self.death_timer > 3.5:
            self.kill()

    # ── Patterns de tir ──────────────────────────────────────────────────
    def _shoot_fan(self, bullets, count=9, speed=4.0):
        """Éventail de balles descendantes."""
        from entities.bullet import EnemyBullet
        for i in range(count):
            angle = math.pi / 2 + (i - count // 2) * (math.pi / (count + 4))
            bullets.add(EnemyBullet(
                self.pos.x, self.pos.y + 70,
                math.cos(angle) * speed, math.sin(angle) * speed
            ))

    def _shoot_aimed(self, player, bullets, speed=5, offset=0):
        """Tir ciblé sur le joueur, avec décalage optionnel."""
        from entities.bullet import EnemyBullet
        dx   = (player.pos.x + offset) - self.pos.x
        dy   = player.pos.y - self.pos.y
        dist = math.hypot(dx, dy) or 1
        bullets.add(EnemyBullet(
            self.pos.x, self.pos.y + 70,
            dx / dist * speed, dy / dist * speed
        ))

    def _shoot_spiral(self, bullets, arms=3):
        """Spirale tournante — bras multiples."""
        from entities.bullet import EnemyBullet
        for arm in range(arms):
            angle = math.radians(self.spiral_angle + arm * (360 // arms))
            vx = math.cos(angle) * 4
            vy = math.sin(angle) * 4
            bullets.add(EnemyBullet(self.pos.x, self.pos.y + 30, vx, vy))
        self.spiral_angle = (self.spiral_angle + 7) % 360

    def _shoot_cross(self, bullets, speed=4.5):
        """Tir en croix : 4 directions + 4 diagonales (8 balles)."""
        from entities.bullet import EnemyBullet
        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            bullets.add(EnemyBullet(
                self.pos.x, self.pos.y + 40,
                math.cos(angle) * speed, math.sin(angle) * speed
            ))

    def _shoot_laser_column(self, target_x, bullets, count=12):
        """Laser vertical : colonne de balles rapides sur la position ciblée."""
        from entities.bullet import EnemyBullet
        for i in range(count):
            bullets.add(EnemyBullet(
                target_x, self.pos.y + 80 + i * 15,
                0, 7.5
            ))

    def _spawn_drones(self, _bullets):
        """Marque que des drones doivent spawner (géré par main.py via spawn_request)."""
        self.spawn_drones_request = 4   # main.py lit cet attribut

    # ── Dégâts / transitions ─────────────────────────────────────────────
    def take_damage(self, dmg):
        if self.state == MegaBossState.DEAD:
            return False
        self.hp -= dmg
        self.flash_timer = 0.10
        self.ps.spawn_explosion(self.pos.x, self.pos.y, (255, 50, 150), count=4, speed=2)
        return self.hp <= 0

    def _check_transition(self):
        ratio = self.hp / self.max_hp
        prev  = self.state
        if   self.state == MegaBossState.PHASE1 and ratio < 0.70:
            self.state = MegaBossState.PHASE2
        elif self.state == MegaBossState.PHASE2 and ratio < 0.50:
            self.state = MegaBossState.PHASE3
        elif self.state == MegaBossState.PHASE3 and ratio < 0.30:
            self.state = MegaBossState.PHASE4
        elif self.state == MegaBossState.PHASE4 and ratio < 0.10:
            self.state = MegaBossState.PHASE5
        elif self.hp <= 0 and self.state != MegaBossState.DEAD:
            self.state = MegaBossState.DEAD
            self.sm.play('boss_die')
        if self.state != prev and self.state != MegaBossState.DEAD:
            self.sm.play('boss_phase')
            # Flash épique au changement de phase
            for _ in range(3):
                self.ps.spawn_explosion(self.pos.x, self.pos.y,
                                        (255, 50, 150), count=30, speed=6)
