import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('NEBULA STRIKE — v0.1')
clock = pygame.time.Clock()

BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
CYAN  = (0,   200, 255)

player_x = WIDTH // 2
player_y = HEIGHT - 80
player_speed = 5

running = True

while running:
    dt = clock.tick(FPS) / 1000.0  # ← UNE seule fois, au début

    # ÉTAPE 1 : ÉVÉNEMENTS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # ÉTAPE 2 : MISE À JOUR
    keys = pygame.key.get_pressed()  # ← d'abord lire les touches

    if keys[pygame.K_LEFT]  and player_x > 20:          player_x -= player_speed * dt * 60
    if keys[pygame.K_RIGHT] and player_x < WIDTH - 20:  player_x += player_speed * dt * 60
    if keys[pygame.K_UP]    and player_y > 20:           player_y -= player_speed * dt * 60
    if keys[pygame.K_DOWN]  and player_y < HEIGHT - 20: player_y += player_speed * dt * 60

    # ÉTAPE 3 : RENDU
    screen.fill(BLACK)
    pygame.draw.polygon(screen, CYAN, [
        (player_x,      player_y - 20),
        (player_x - 15, player_y + 15),
        (player_x + 15, player_y + 15),
    ])
    pygame.display.flip()

pygame.quit()
sys.exit()