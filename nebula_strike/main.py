# main.py — NEBULA STRIKE — Version visuelle complète
import pygame, sys, random
from settings import *
from entities.player         import Player
from entities.enemy          import EnemyDrone, EnemyDestroyer, EnemyCarrier
from entities.elite_enemy    import EliteEnemy
from entities.boss           import Boss
from entities.mega_boss      import MegaBoss
from entities.bullet         import PlayerBullet, EnemyBullet
from entities.powerup        import PowerUp
from systems.particles       import ParticleSystem
from systems.sound_manager   import SoundManager
from systems.hud             import HUD
from systems.wave_manager    import WaveManager
from systems.pathfinding     import AStar, NavigatorEnemy
from systems.boids           import Boid
from systems.adaptive_difficulty import AdaptiveDifficulty
from systems.background      import Background


class GameState:
    MENU, PLAYING, PAUSED, GAME_OVER, VICTORY = range(5)


def draw_debug_overlay(surface, ad, font):
    info = ad.get_debug_info()
    y = 10
    for key, val in info.items():
        color = (50, 255, 100) if key == 'difficulty' and float(info['difficulty']) < 1.2 else \
                (255, 200, 50) if key == 'difficulty' and float(info['difficulty']) < 1.6 else \
                (255, 80, 80)
        txt = font.render(f'[DEBUG] {key:14s}: {val}', True, color)
        surface.blit(txt, (WIDTH - txt.get_width() - 10, y))
        y += 20


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    # ── Systèmes globaux
    bg    = Background()
    ps    = ParticleSystem()
    sm    = SoundManager()
    hud   = HUD()
    astar = AStar()
    ad    = AdaptiveDifficulty()
    wm    = WaveManager(astar, ad)

    font     = pygame.font.SysFont('consolas', 32, bold=True)
    font_dbg = pygame.font.SysFont('consolas', 14)
    debug_mode = False

    # ── Groupes de sprites
    all_sprites = pygame.sprite.Group()
    enemies     = pygame.sprite.Group()
    p_bullets   = pygame.sprite.Group()
    e_bullets   = pygame.sprite.Group()
    powerups    = pygame.sprite.Group()
    boss_group  = pygame.sprite.GroupSingle()
    mega_group  = pygame.sprite.GroupSingle()

    def apply_wave_weapon(player, wave_num):
        """Garantit le niveau d'arme minimum pour la vague courante."""
        min_wl = WAVE_MIN_WEAPON.get(wave_num, 1)
        player.set_min_weapon(min_wl)

    def new_game():
        nonlocal state, wave
        for g in [all_sprites, enemies, p_bullets, e_bullets, powerups]:
            g.empty()
        boss_group.empty()
        mega_group.empty()
        p = Player(ps, sm)
        all_sprites.add(p)
        state = GameState.PLAYING
        wave  = 1
        apply_wave_weapon(p, wave)
        wm.start_wave(wave, enemies, all_sprites)
        return p

    state     = GameState.MENU
    wave      = 1
    player    = None
    msg_timer = 0
    msg_text  = ''

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── ÉVÉNEMENTS
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
                    if event.key == pygame.K_b:
                        ps.spawn_emp(player.pos.x, player.pos.y)
                        for e in list(enemies):
                            e.take_damage(50)
                        sm.play('emp')
                    if event.key == pygame.K_F1:
                        debug_mode = not debug_mode
                elif state == GameState.PAUSED:
                    if event.key == pygame.K_p:
                        state = GameState.PLAYING
                elif state in (GameState.GAME_OVER, GameState.VICTORY):
                    if event.key == pygame.K_r:
                        player = new_game()

        # ── MISE À JOUR
        bg.update(dt)

        if state == GameState.PLAYING:
            player.update(dt, p_bullets)
            ad.update(dt)

            for e in list(enemies):
                if isinstance(e, EnemyCarrier):
                    e.update(dt, player, enemies)
                elif isinstance(e, Boid):
                    e.update(dt, enemies, player)
                elif isinstance(e, EliteEnemy):
                    e.update(dt, player, e_bullets, p_bullets)
                elif isinstance(e, NavigatorEnemy):
                    e.update(dt, player)
                else:
                    e.update(dt, player, e_bullets)

            if boss_group.sprite:
                boss_group.sprite.update(dt, player, e_bullets, ps)

            if mega_group.sprite:
                mega_group.sprite.update(dt, player, e_bullets, ps)
                # Gestion spawn de drones demandés par le Mega Boss
                req = getattr(mega_group.sprite, 'spawn_drones_request', 0)
                if req > 0:
                    mega_group.sprite.spawn_drones_request = 0
                    for _ in range(req):
                        from entities.enemy import EnemyDrone
                        import random as _r
                        d = EnemyDrone(_r.randint(80, WIDTH-80), -40)
                        d.speed *= 1.5
                        enemies.add(d); all_sprites.add(d)

            p_bullets.update(dt)
            e_bullets.update(dt)
            powerups.update(dt)
            ps.update(dt)

            # Collisions balles joueur → ennemis
            hits = pygame.sprite.groupcollide(enemies, p_bullets, False, True)
            for enemy, bullets in hits.items():
                for b in bullets:
                    ad.metrics.bullets_hit += 1
                    if enemy.take_damage(PLAYER_BULLET_DMG, ps):
                        enemy.kill()
                        player.score += enemy.score_value
                        ad.metrics.kills += 1
                        sm.play('explosion')
                        if random.random() < ad.get_powerup_rate():
                            pw = PowerUp(enemy.rect.centerx, enemy.rect.centery)
                            powerups.add(pw)

            # Collisions balles joueur → boss
            if boss_group.sprite:
                boss_hits = pygame.sprite.spritecollide(boss_group.sprite, p_bullets, True)
                for _ in boss_hits:
                    ad.metrics.bullets_hit += 1
                    if boss_group.sprite.take_damage(PLAYER_BULLET_DMG):
                        player.score += SCORE_BOSS
                        ad.metrics.kills += 1
                        sm.play('boss_die')
                        boss_group.sprite.state = 'dead'

            # Collisions balles joueur → mega boss
            if mega_group.sprite:
                mega_hits = pygame.sprite.spritecollide(mega_group.sprite, p_bullets, True)
                for _ in mega_hits:
                    ad.metrics.bullets_hit += 1
                    if mega_group.sprite.take_damage(PLAYER_BULLET_DMG):
                        player.score += SCORE_MEGA_BOSS
                        ad.metrics.kills += 1

            # Balles ennemies → joueur
            if pygame.sprite.spritecollide(player, e_bullets, True,
                                           pygame.sprite.collide_circle):
                player.take_damage(15)
                ad.metrics.damage_taken += 15

            # Contact ennemi → joueur (timer pour éviter invincibilité permanente)
            if pygame.sprite.spritecollide(player, enemies, False):
                player.contact_timer = getattr(player, 'contact_timer', 0) + dt
                if player.contact_timer >= 0.5:
                    player.contact_timer = 0
                    player.take_damage(DRONE_DMG)
                    ad.metrics.damage_taken += DRONE_DMG
            else:
                player.contact_timer = 0

            # Power-ups
            for pw in pygame.sprite.spritecollide(player, powerups, True):
                pw.apply(player)
                sm.play('powerup')
                ad.metrics.powerups_taken += 1

            # Fin de vague
            if not enemies and not boss_group.sprite and not mega_group.sprite:
                wave += 1
                if wave == 9:
                    # BOSS — Niveau 9/10
                    boss = Boss(ps, sm)
                    boss_group.add(boss)
                    all_sprites.add(boss)
                    sm.play('boss_enter')
                    apply_wave_weapon(player, wave)
                    msg_text  = '⚠  BOSS  — NIVEAU 9 / 10'
                    msg_timer = 3.5
                elif wave == 10:
                    # MEGA BOSS — Niveau 10/10
                    mega = MegaBoss(ps, sm)
                    mega_group.add(mega)
                    all_sprites.add(mega)
                    sm.play('boss_enter')
                    apply_wave_weapon(player, wave)
                    msg_text  = '☠  MEGA BOSS  ★ NIVEAU FINAL 10 / 10 ★'
                    msg_timer = 5.0
                elif wave > 10:
                    state = GameState.VICTORY
                else:
                    wm.start_wave(wave, enemies, all_sprites)
                    apply_wave_weapon(player, wave)
                    msg_text  = f'NIVEAU  {wave} / 10'
                    msg_timer = 2.0

            # Vies / Game Over
            if player.hp <= 0:
                player.lives -= 1
                ad.metrics.deaths += 1
                if player.lives <= 0:
                    state = GameState.GAME_OVER
                else:
                    player.hp = PLAYER_HP
                    player.shield = SHIELD_MAX
                    player.invincible = True
                    player.invincible_timer = 3.0
                    # Pénalité classique shmup : perd 1 niveau d'arme (jamais sous le min de vague)
                    min_wl = WAVE_MIN_WEAPON.get(wave, 1)
                    player.downgrade_weapon(min_level=min_wl)

            msg_timer = max(0, msg_timer - dt)

        # ══ RENDU ══════════════════════════════════════════════
        # 1 — Fond nébuleuse + étoiles
        bg.draw(screen)

        # 2 — Traînées des balles (avant les sprites)
        for b in p_bullets:
            if hasattr(b, 'draw_trail'):
                b.draw_trail(screen)
        for b in e_bullets:
            if hasattr(b, 'draw_trail'):
                b.draw_trail(screen)

        # 3 — Particules
        ps.draw(screen)

        if state == GameState.MENU:
            # Titre avec glow
            font_xl = pygame.font.SysFont('consolas', 62, bold=True)
            font_sm = pygame.font.SysFont('consolas', 22)
            for offset, alpha in [(4, 40), (2, 80)]:
                glow_surf = font_xl.render('NEBULA STRIKE', True, (0, 140, 200))
                glow_surf.set_alpha(alpha)
                screen.blit(glow_surf, (WIDTH//2 - glow_surf.get_width()//2 + offset,
                                        HEIGHT//2 - 90 + offset))
            title = font_xl.render('NEBULA STRIKE', True, (0, 220, 255))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 90))
            s1 = font_sm.render('ENTRÉE — Jouer    P — Pause    B — EMP    F1 — Debug', True, (150, 180, 255))
            s2 = font_sm.render('WASD / Flèches — Déplacer    ESPACE — Tirer', True, (120, 150, 220))
            screen.blit(s1, (WIDTH//2 - s1.get_width()//2, HEIGHT//2 + 10))
            screen.blit(s2, (WIDTH//2 - s2.get_width()//2, HEIGHT//2 + 44))

        elif state in (GameState.PLAYING, GameState.PAUSED):
            # Ennemis + barres de vie
            enemies.draw(screen)
            boss_group.draw(screen)
            mega_group.draw(screen)
            for e in enemies:
                if hasattr(e, 'draw_health_bar'):
                    e.draw_health_bar(screen)

            # Balles
            p_bullets.draw(screen)
            e_bullets.draw(screen)
            powerups.draw(screen)

            # Joueur + bouclier
            if player:
                player.draw_shield_bubble(screen)
                screen.blit(player.image, player.rect)

            # Boss HP bar
            if boss_group.sprite:
                boss_group.sprite.draw_health_bar(screen)
            if mega_group.sprite:
                mega_group.sprite.draw_health_bar(screen)
            # HUD
            hud.draw(screen, player, wave, boss_group.sprite or mega_group.sprite)

            # Indicateur weapon level (coin bas-gauche)
            if player:
                wl       = player.weapon_level
                wl_color = [(80,220,255),(80,255,150),(220,255,80),(255,160,50),(255,80,200)][wl-1]
                wl_font  = pygame.font.SysFont('consolas', 16, bold=True)
                filled   = '\u25a0' * wl
                empty    = '\u25a1' * (5 - wl)
                wl_surf  = wl_font.render(f'ARME  {filled}{empty}  Lv.{wl}', True, wl_color)
                screen.blit(wl_surf, (10, HEIGHT - 60))
                if player.rapid_fire:
                    rf_surf = wl_font.render('CADENCE \u26a1 RAPIDE', True, (50,255,150))
                    screen.blit(rf_surf, (10, HEIGHT - 42))
            if msg_timer > 0:
                hud.show_message(screen, msg_text, (255, 220, 50))
            if debug_mode:
                draw_debug_overlay(screen, ad, font_dbg)

            if state == GameState.PAUSED:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))
                screen.blit(overlay, (0, 0))
                hud.show_message(screen, 'PAUSE', (200, 220, 255))

        elif state == GameState.GAME_OVER:
            t1 = font.render('GAME OVER', True, (220, 50, 50))
            t2 = pygame.font.SysFont('consolas', 20).render(
                f'Score : {player.score:08d}   [R] Rejouer', True, (200, 200, 200))
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))

        elif state == GameState.VICTORY:
            t1 = font.render('VICTOIRE !', True, (50, 255, 150))
            t2 = pygame.font.SysFont('consolas', 20).render(
                f'Score : {player.score:08d}   [R] Rejouer', True, (200, 200, 200))
            screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//3))
            screen.blit(t2, (WIDTH//2 - t2.get_width()//2, HEIGHT//2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()