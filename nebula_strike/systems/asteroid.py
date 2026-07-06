# main.py — version finale avec IA
import pygame, sys, random
from settings import *
from entities.player       import Player
from entities.enemy        import EnemyDrone, EnemyDestroyer, EnemyCarrier
from entities.elite_enemy  import EliteEnemy
from entities.boss         import Boss
from entities.bullet       import PlayerBullet, EnemyBullet
from entities.powerup      import PowerUp
from systems.particles         import ParticleSystem
from systems.sound_manager     import SoundManager
from systems.hud               import HUD
from systems.wave_manager      import WaveManager
from systems.pathfinding       import AStar, NavigatorEnemy
from systems.boids             import Boid
from systems.adaptive_difficulty import AdaptiveDifficulty
from systems.asteroid          import Asteroid

class GameState:
    MENU, PLAYING, PAUSED, GAME_OVER, VICTORY = range(5)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    # Systèmes
    ps   = ParticleSystem()
    sm   = SoundManager()
    hud  = HUD()
    ad   = AdaptiveDifficulty()
    astar= AStar()
    wm   = WaveManager()

    font_debug = pygame.font.SysFont('consolas', 14)
    debug_mode = False

    # Groupes
    all_sprites = pygame.sprite.Group()
    enemies     = pygame.sprite.Group()
    p_bullets   = pygame.sprite.Group()
    e_bullets   = pygame.sprite.Group()
    powerups    = pygame.sprite.Group()
    asteroids   = pygame.sprite.Group()
    boss_group  = pygame.sprite.GroupSingle()

    # Étoiles
    class Star(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            size       = random.randint(1, 4)
            brightness = min(255, 100 + size * 40)
            self.image = pygame.Surface((size, size))
            self.image.fill((brightness, brightness, brightness))
            self.rect  = self.image.get_rect(
                x=random.randint(0, WIDTH),
                y=random.randint(0, HEIGHT)
            )
            self.speed = size * 0.8

        def update(self, dt):
            self.rect.y += self.speed
            if self.rect.y > HEIGHT:
                self.rect.y = 0
                self.rect.x = random.randint(0, WIDTH)

    stars = pygame.sprite.Group()
    for _ in range(150):
        stars.add(Star())

    def new_game():
        nonlocal state, wave
        for g in [all_sprites, enemies, p_bullets,
                  e_bullets, powerups, asteroids]:
            g.empty()
        boss_group.empty()
        astar.clear()
        ad.__init__()

        p     = Player(ps, sm)
        all_sprites.add(p)
        state = GameState.PLAYING
        wave  = 1
        _start_wave(wave)
        return p

    def _start_wave(wave_num):
        """Spawn les ennemis selon la vague et la difficulté adaptative."""
        hp_mult  = ad.get_enemy_hp_mult()
        spd_mult = ad.get_enemy_speed_mult()

        astar.clear()

        # Astéroïdes obstacles dès la vague 3
        if wave_num >= 3:
            for _ in range(random.randint(2, 4)):
                a = Asteroid(astar)
                asteroids.add(a)

        if wave_num <= 2:
            for _ in range(4 + wave_num):
                e = EnemyDrone(
                    random.randint(80, WIDTH-80),
                    random.randint(-200, -40)
                )
                e.speed *= spd_mult
                enemies.add(e)

        elif wave_num <= 4:
            for _ in range(3):
                e = EnemyDrone(
                    random.randint(80, WIDTH-80),
                    random.randint(-200, -40)
                )
                e.speed *= spd_mult
                enemies.add(e)
            for _ in range(2):
                e = EnemyDestroyer(
                    random.randint(100, WIDTH-100),
                    random.randint(-200, -60)
                )
                e.hp     *= hp_mult
                enemies.add(e)

        elif wave_num == 5:
            # Essaim Boids
            for _ in range(12):
                b = Boid(
                    random.randint(100, WIDTH-100),
                    random.randint(-200, -30)
                )
                enemies.add(b)
            # + Elite FSM
            e = EliteEnemy(WIDTH//2, -60, ps, sm)
            enemies.add(e)

        elif wave_num % 2 == 0:
            # Vagues paires : NavigatorEnemy avec A*
            for _ in range(3):
                n = NavigatorEnemy(
                    random.randint(80, WIDTH-80),
                    random.randint(-200, -40),
                    astar
                )
                enemies.add(n)
            for _ in range(2):
                e = EnemyDrone(
                    random.randint(80, WIDTH-80),
                    random.randint(-200, -40)
                )
                e.speed *= spd_mult
                enemies.add(e)

        else:
            # Vague standard
            n_drones     = int((wave_num + 2) * spd_mult)
            n_destroyers = max(0, wave_num - 2)
            for _ in range(n_drones):
                e = EnemyDrone(
                    random.randint(60, WIDTH-60),
                    random.randint(-250, -40)
                )
                e.speed *= spd_mult
                enemies.add(e)
            for _ in range(n_destroyers):
                e = EnemyDestroyer(
                    random.randint(80, WIDTH-80),
                    random.randint(-250, -60)
                )
                e.hp *= hp_mult
                enemies.add(e)
            # Elite si difficulté > 1.2
            if ad.difficulty_score > 1.2:
                e = EliteEnemy(
                    random.randint(100, WIDTH-100), -60, ps, sm)
                enemies.add(e)

        print(f'[Wave {wave_num}] diff={ad.difficulty_score:.2f} '
              f'hp×{hp_mult:.2f} spd×{spd_mult:.2f}')

    state     = GameState.MENU
    wave      = 1
    player    = None
    msg_timer = 0
    msg_text  = ''
    font      = pygame.font.SysFont('consolas', 32, bold=True)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── ÉVÉNEMENTS ──────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if state == GameState.MENU:
                    if event.key == pygame.K_RETURN:
                        player = new_game()

                elif state == GameState.PLAYING:
                    if event.key == pygame.K_p:
                        state = GameState.PAUSED
                    if event.key == pygame.K_F1:
                        debug_mode = not debug_mode
                    if event.key == pygame.K_b:
                        ps.spawn_emp(player.pos.x, player.pos.y)
                        for e in enemies:
                            e.take_damage(50)
                        sm.play('emp')

                elif state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        state = GameState.PLAYING

                elif state in (GameState.GAME_OVER, GameState.VICTORY):
                    if event.key == pygame.K_r:
                        player = new_game()

        # ── MISE À JOUR ─────────────────────────────────
        stars.update(dt)

        if state == GameState.PLAYING:
            ad.update(dt)
            player.update(dt, p_bullets)
            ad.metrics.bullets_fired = max(
                ad.metrics.bullets_fired,
                len(list(p_bullets))
            )

            asteroids.update(dt)

            # Update ennemis selon leur type
            for e in list(enemies):
                if isinstance(e, Boid):
                    e.update(dt, list(enemies), player)
                elif isinstance(e, EliteEnemy):
                    e.update(dt, player, e_bullets, p_bullets)
                elif isinstance(e, NavigatorEnemy):
                    e.update(dt, player)
                elif isinstance(e, EnemyCarrier):
                    e.update(dt, player, enemies)
                else:
                    e.update(dt, player, e_bullets)

            if boss_group.sprite:
                boss_group.sprite.update(dt, player, e_bullets, ps)

            p_bullets.update(dt)
            e_bullets.update(dt)
            powerups.update(dt)
            ps.update(dt)

            # ── Collisions ──────────────────────────────
            # Balles joueur → ennemis
            hits = pygame.sprite.groupcollide(
                enemies, p_bullets, False, True)
            for enemy, bullets in hits.items():
                for b in bullets:
                    ad.metrics.bullets_hit += 1
                    if enemy.take_damage(PLAYER_BULLET_DMG, ps):
                        enemy.kill()
                        player.score        += enemy.score_value
                        ad.metrics.kills    += 1
                        sm.play('explosion')
                        if random.random() < ad.get_powerup_rate():
                            pw = PowerUp(
                                enemy.rect.centerx,
                                enemy.rect.centery
                            )
                            powerups.add(pw)

            # Balles joueur → boss
            if boss_group.sprite:
                boss_hits = pygame.sprite.spritecollide(
                    boss_group.sprite, p_bullets, True)
                for _ in boss_hits:
                    ad.metrics.bullets_hit += 1
                    if boss_group.sprite.take_damage(PLAYER_BULLET_DMG):
                        player.score += SCORE_BOSS

            # Balles ennemies → joueur
            if pygame.sprite.spritecollide(
                    player, e_bullets, True,
                    pygame.sprite.collide_circle):
                player.take_damage(15)
                ad.metrics.damage_taken += 15

            # Ennemis → joueur contact
            if pygame.sprite.spritecollide(player, enemies, False):
                player.take_damage(DRONE_DMG)
                ad.metrics.damage_taken += DRONE_DMG

            # Power-ups → joueur
            pw_hits = pygame.sprite.spritecollide(player, powerups, True)
            for pw in pw_hits:
                pw.apply(player)
                sm.play('powerup')
                ad.metrics.powerups_taken += 1

            # ── Fin de vague ────────────────────────────
            if not enemies and not boss_group.sprite:
                wave += 1
                if wave == 6:
                    boss = Boss(ps, sm)
                    boss_group.add(boss)
                    msg_text  = 'ATTENTION — BOSS !'
                    msg_timer = 2.5
                    sm.play('boss_enter')
                elif wave > 6 and not boss_group.sprite:
                    state = GameState.VICTORY
                else:
                    _start_wave(wave)
                    msg_text  = f'VAGUE {wave}'
                    msg_timer = 1.5

            # ── Game Over ───────────────────────────────
            if player.hp <= 0:
                player.lives    -= 1
                ad.metrics.deaths += 1
                if player.lives <= 0:
                    state = GameState.GAME_OVER
                else:
                    player.hp             = PLAYER_HP
                    player.shield         = SHIELD_MAX
                    player.invincible     = True
                    player.invincible_timer = 3.0

            msg_timer = max(0, msg_timer - dt)

        # ── RENDU ───────────────────────────────────────
        screen.fill(C_BG)
        stars.draw(screen)
        ps.draw(screen)
        asteroids.draw(screen)

        if state == GameState.MENU:
            t1 = font.render('NEBULA STRIKE', True, (0,200,255))
            t2 = pygame.font.SysFont('consolas',18).render(
                'ENTRÉE pour jouer', True, (200,200,200))
            t3 = pygame.font.SysFont('consolas',15).render(
                'Flèches/WASD : déplacer | ESPACE : tirer | B : bombe | F1 : debug',
                True, (150,150,150))
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))
            screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2+50))

        elif state == GameState.PLAYING:
            asteroids.draw(screen)
            enemies.draw(screen)
            boss_group.draw(screen)
            for e in enemies:
                if hasattr(e, 'draw_health_bar'):
                    e.draw_health_bar(screen)
            p_bullets.draw(screen)
            e_bullets.draw(screen)
            powerups.draw(screen)
            screen.blit(player.image, player.rect)
            hud.draw(screen, player, wave, boss_group.sprite)
            if msg_timer > 0:
                hud.show_message(screen, msg_text, (255,220,50))

            # Mode debug F1
            if debug_mode:
                info  = ad.get_debug_info()
                y_pos = 10
                for key, val in info.items():
                    color = (50,255,100)  if key == 'difficulty' and \
                                float(str(info['difficulty'])) < 1.2 else \
                            (255,200,50)  if key == 'difficulty' and \
                                float(str(info['difficulty'])) < 1.6 else \
                            (255,80,80)
                    txt = font_debug.render(
                        f'[DEBUG] {key:12s}: {val}', True, color)
                    screen.blit(txt, (WIDTH - txt.get_width() - 10, y_pos))
                    y_pos += 18

        elif state == GameState.PAUSED:
            enemies.draw(screen)
            screen.blit(player.image, player.rect)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            screen.blit(overlay, (0,0))
            hud.show_message(screen, 'PAUSE', (200,200,255))

        elif state == GameState.GAME_OVER:
            t1 = font.render('GAME OVER', True, (220,50,50))
            t2 = pygame.font.SysFont('consolas',20).render(
                f'SCORE : {player.score:08d}', True, (255,220,50))
            t3 = pygame.font.SysFont('consolas',18).render(
                '[R] Rejouer', True, (200,200,200))
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))
            screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2+60))

        elif state == GameState.VICTORY:
            t1 = font.render('VICTOIRE !', True, (50,255,150))
            t2 = pygame.font.SysFont('consolas',20).render(
                f'SCORE FINAL : {player.score:08d}', True, (255,220,50))
            t3 = pygame.font.SysFont('consolas',18).render(
                '[R] Rejouer', True, (200,200,200))
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))
            screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2+60))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()