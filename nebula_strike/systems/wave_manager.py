# systems/wave_manager.py — 10 vagues progressives
# Inspiré des shoot'em up classiques : montée en difficulté cohérente
import random
from entities.enemy        import EnemyDrone, EnemyDestroyer, EnemyCarrier
from entities.elite_enemy  import EliteEnemy
from systems.boids         import Boid
from systems.pathfinding   import NavigatorEnemy
from settings              import WIDTH


class WaveManager:
    def __init__(self, astar=None, adaptive_diff=None):
        self.astar = astar
        self.ad    = adaptive_diff

    def start_wave(self, wave_num, enemies_group, all_sprites):
        """Génère la vague — 10 vagues avec montée progressive."""
        hp_mult  = self.ad.get_enemy_hp_mult()    if self.ad else 1.0
        spd_mult = self.ad.get_enemy_speed_mult()  if self.ad else 1.0
        before_count = len(enemies_group)

        builders = {
            1: self._wave_1,
            2: self._wave_2,
            3: self._wave_3,
            4: self._wave_4,
            5: self._wave_5,
            6: self._wave_6,
            7: self._wave_7,
            8: self._wave_8,
        }
        # Vagues 1-8 gérées ici ; 9 = Boss ; 10 = Mega Boss (gérés dans main.py)
        if wave_num in builders:
            builders[wave_num](enemies_group, all_sprites, hp_mult, spd_mult)

        # Sécurité anti-blocage: une vague ne doit jamais démarrer à 0 ennemi.
        spawned = len(enemies_group) - before_count
        if wave_num <= 8 and spawned <= 0:
            for _ in range(6):
                e = EnemyDrone(random.randint(80, WIDTH-80), random.randint(-180, -40))
                e.speed *= max(1.0, spd_mult)
                enemies_group.add(e)
                all_sprites.add(e)
            spawned = len(enemies_group) - before_count

        difficulty = self.ad.difficulty_score if self.ad else 1.0
        print(f'[Wave] Vague {wave_num} | diff={difficulty:.2f} '
              f'hp×{hp_mult:.2f} spd×{spd_mult:.2f} | spawned={spawned}')

    # ── Vague 1 — Tutoriel : 5 drones en formation ──────────────────────
    def _wave_1(self, eg, sg, hp, spd):
        positions = [150, 280, 450, 620, 750]
        for x in positions:
            e = EnemyDrone(x, random.randint(-120, -40))
            e.speed *= spd
            eg.add(e); sg.add(e)

    # ── Vague 2 — 8 drones + 2 destroyers ───────────────────────────────
    def _wave_2(self, eg, sg, hp, spd):
        for _ in range(8):
            e = EnemyDrone(random.randint(80, WIDTH-80), random.randint(-180, -40))
            e.speed *= spd
            eg.add(e); sg.add(e)
        for _ in range(2):
            e = EnemyDestroyer(random.randint(100, WIDTH-100), random.randint(-200, -80))
            e.hp *= hp
            eg.add(e); sg.add(e)

    # ── Vague 3 — Pression accrue : drones + destroyers + 1 Élite ───────
    def _wave_3(self, eg, sg, hp, spd):
        for _ in range(6):
            e = EnemyDrone(random.randint(60, WIDTH-60), random.randint(-200, -40))
            e.speed *= spd
            eg.add(e); sg.add(e)
        for _ in range(3):
            e = EnemyDestroyer(random.randint(100, WIDTH-100), random.randint(-250, -80))
            e.hp *= hp
            eg.add(e); sg.add(e)
        e = EliteEnemy(WIDTH // 2, -30)
        eg.add(e); sg.add(e)

    # ── Vague 4 — Forteresse : Destroyers + 1 Carrier + 1 Élite ─────────
    def _wave_4(self, eg, sg, hp, spd):
        for _ in range(5):
            e = EnemyDestroyer(random.randint(80, WIDTH-80), random.randint(-250, -60))
            e.hp    *= hp
            e.speed *= spd
            eg.add(e); sg.add(e)
        c = EnemyCarrier(WIDTH // 2, -100)
        c.hp *= hp
        eg.add(c); sg.add(c)
        e = EliteEnemy(random.randint(150, WIDTH-150), -30)
        eg.add(e); sg.add(e)

    # ── Vague 5 — Essaim Boids + 2 Élites ───────────────────────────────
    def _wave_5(self, eg, sg, hp, spd):
        for _ in range(16):
            b = Boid(random.randint(80, WIDTH-80), random.randint(-300, -30))
            eg.add(b); sg.add(b)
        for _ in range(2):
            e = EliteEnemy(random.randint(100, WIDTH-100), -30)
            eg.add(e); sg.add(e)

    # ── Vague 6 — Siège : 2 Carriers + 8 Destroyers ─────────────────────
    def _wave_6(self, eg, sg, hp, spd):
        for i, x in enumerate([WIDTH//3, 2*WIDTH//3]):
            c = EnemyCarrier(x, -100 - i*40)
            c.hp *= hp * 1.2
            eg.add(c); sg.add(c)
        for _ in range(8):
            e = EnemyDestroyer(random.randint(60, WIDTH-60), random.randint(-300, -60))
            e.hp    *= hp
            e.speed *= spd
            eg.add(e); sg.add(e)

    # ── Vague 7 — Chasseurs intelligents : Navigateurs A* + 3 Élites ─────
    def _wave_7(self, eg, sg, hp, spd):
        if self.astar:
            for _ in range(4):
                nav = NavigatorEnemy(
                    random.randint(60, WIDTH-60), random.randint(-250, -60),
                    self.astar
                )
                eg.add(nav); sg.add(nav)
        for _ in range(3):
            e = EliteEnemy(random.randint(80, WIDTH-80), -30)
            eg.add(e); sg.add(e)
        for _ in range(4):
            e = EnemyDrone(random.randint(60, WIDTH-60), random.randint(-200, -40))
            e.speed *= spd * 1.3
            eg.add(e); sg.add(e)

    # ── Vague 8 — Assaut total : tous les types ensemble ─────────────────
    def _wave_8(self, eg, sg, hp, spd):
        for _ in range(10):
            e = EnemyDrone(random.randint(60, WIDTH-60), random.randint(-250, -30))
            e.speed *= spd * 1.2
            eg.add(e); sg.add(e)
        for _ in range(5):
            e = EnemyDestroyer(random.randint(80, WIDTH-80), random.randint(-300, -60))
            e.hp    *= hp * 1.3
            e.speed *= spd
            eg.add(e); sg.add(e)
        c = EnemyCarrier(WIDTH // 2, -120)
        c.hp *= hp * 1.5
        eg.add(c); sg.add(c)
        for _ in range(3):
            e = EliteEnemy(random.randint(80, WIDTH-80), -30)
            eg.add(e); sg.add(e)
        if self.astar:
            nav = NavigatorEnemy(random.randint(60, WIDTH-60), -100, self.astar)
            eg.add(nav); sg.add(nav)

    # ─────────────────────────────────────────────────────────────────────
    # Vague 9 = Boss normal  (géré dans main.py)
    # Vague 10 = MEGA BOSS   (géré dans main.py)