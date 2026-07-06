# systems/hud.py
import pygame
from settings import *

class HUD:
    def __init__(self):
        self.font_lg = pygame.font.SysFont('consolas', 24, bold=True)
        self.font_sm = pygame.font.SysFont('consolas', 16)
        self.font_xl = pygame.font.SysFont('consolas', 48, bold=True)

    def draw(self, surface, player, wave, boss=None):
        self._draw_hp_bar(surface, player)
        self._draw_shield_bar(surface, player)
        self._draw_score(surface, player.score)
        self._draw_wave(surface, wave)
        self._draw_lives(surface, player.lives)
        if boss and boss.alive():
            self._draw_boss_hp(surface, boss)

    def _draw_hp_bar(self, surface, player):
        ratio = player.hp / 100
        pygame.draw.rect(surface, (60, 0, 0),   (20, 20, 200, 16), border_radius=4)
        color = (100,220,100) if ratio > 0.5 else \
                (220,200,50)  if ratio > 0.25 else (220,50,50)
        pygame.draw.rect(surface, color, (20, 20, int(200*ratio), 16), border_radius=4)
        pygame.draw.rect(surface, (200,200,200), (20, 20, 200, 16), 1, border_radius=4)
        txt = self.font_sm.render(f'HP {player.hp}/100', True, C_HUD_TEXT)
        surface.blit(txt, (228, 20))

    def _draw_shield_bar(self, surface, player):
        ratio = player.shield / SHIELD_MAX
        pygame.draw.rect(surface, (0,20,60),    (20, 42, 200, 12), border_radius=3)
        pygame.draw.rect(surface, C_SHIELD,     (20, 42, int(200*ratio), 12), border_radius=3)
        pygame.draw.rect(surface, (100,150,200),(20, 42, 200, 12), 1, border_radius=3)
        txt = self.font_sm.render(f'SH {int(player.shield)}/{SHIELD_MAX}', True, C_HUD_TEXT)
        surface.blit(txt, (228, 43))

    def _draw_score(self, surface, score):
        txt = self.font_lg.render(f'SCORE {score:08d}', True, (255,220,80))
        surface.blit(txt, (WIDTH//2 - txt.get_width()//2, 10))

    def _draw_wave(self, surface, wave):
        txt = self.font_sm.render(f'VAGUE {wave}', True, C_HUD_TEXT)
        surface.blit(txt, (WIDTH - txt.get_width() - 20, 20))

    def _draw_lives(self, surface, lives):
        for i in range(lives):
            x = WIDTH - 20 - i * 22
            pygame.draw.polygon(surface, C_PLAYER, [
                (x, 58), (x-8, 72), (x, 66), (x+8, 72)
            ])

    def _draw_boss_hp(self, surface, boss):
        ratio  = max(0, boss.hp / boss.max_hp)
        bar_w  = 400
        bar_x  = (WIDTH - bar_w) // 2
        bar_y  = HEIGHT - 36
        lbl    = self.font_lg.render('— BOSS —', True, C_BOSS)
        surface.blit(lbl, (WIDTH//2 - lbl.get_width()//2, bar_y - 26))
        pygame.draw.rect(surface, (60,0,20),    (bar_x, bar_y, bar_w, 18), border_radius=4)
        pygame.draw.rect(surface, C_BOSS,       (bar_x, bar_y, int(bar_w*ratio), 18), border_radius=4)
        pygame.draw.rect(surface, (255,100,150),(bar_x, bar_y, bar_w, 18), 1, border_radius=4)

    def show_message(self, surface, text, color=(255,255,255)):
        txt = self.font_xl.render(text, True, color)
        x   = WIDTH//2  - txt.get_width()//2
        y   = HEIGHT//2 - txt.get_height()//2
        bg  = pygame.Surface((txt.get_width()+40, txt.get_height()+20), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg,  (x-20, y-10))
        surface.blit(txt, (x, y))