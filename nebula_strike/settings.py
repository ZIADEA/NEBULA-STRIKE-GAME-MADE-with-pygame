# settings.py
import pygame

# ── Fenêtre ──────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
FPS           = 60
TITLE         = 'NEBULA STRIKE'

# ── Couleurs ─────────────────────────────────────────
C_BG        = (4,   4,   20 )
C_PLAYER    = (0,   200, 255)
C_BULLET_P  = (255, 255, 100)
C_BULLET_E  = (255, 60,  60 )
C_DRONE     = (200, 50,  50 )
C_DESTROYER = (255, 140, 0  )
C_CARRIER   = (180, 0,   220)
C_BOSS      = (255, 50,  150)
C_SHIELD    = (0,   150, 255)
C_POWERUP   = (0,   255, 150)
C_HUD_TEXT  = (200, 220, 255)

# ── Joueur ───────────────────────────────────────────
PLAYER_SPEED      = 5.5
PLAYER_HP         = 100
PLAYER_SHOOT_DELAY= 200
PLAYER_BULLET_SPD = 12
PLAYER_BULLET_DMG = 10
SHIELD_MAX        = 100
SHIELD_REGEN      = 0.02   # régénération lente (était 0.15 = trop rapide)

# ── Ennemis ──────────────────────────────────────────
DRONE_HP,     DRONE_SPD,     DRONE_DMG     = 20,  2.5, 15
DESTROYER_HP, DESTROYER_SPD, DESTROYER_DMG = 60,  1.5, 30
CARRIER_HP,   CARRIER_SPD,   CARRIER_DMG   = 120, 0.8, 0
BOSS_HP                                    = 2000
MEGA_BOSS_HP                               = 5000
TOTAL_WAVES                                = 10

# Niveau d'arme minimum garanti par vague (shmup classique : arme évolue avec la progression)
# Le joueur ne peut jamais tomber EN-DESSOUS de ce niveau dans cette vague
WAVE_MIN_WEAPON = {1:1, 2:1, 3:2, 4:2, 5:3, 6:3, 7:4, 8:4, 9:4, 10:5}

# ── Particules ──────────────────────────────────────────
MAX_PARTICLES = 600

# ── Scoring ──────────────────────────────────────────
SCORE_DRONE      = 100
SCORE_DESTROYER  = 300
SCORE_CARRIER    = 500
SCORE_BOSS       = 5000
SCORE_MEGA_BOSS  = 20000
