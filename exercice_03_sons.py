import pygame
import numpy as np
import sys

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()

screen = pygame.display.set_mode((500, 300))
pygame.display.set_caption('Sons Procéduraux')
clock = pygame.time.Clock()
font = pygame.font.SysFont('consolas', 20)

def make_laser_sound(freq=880, duration=0.08, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq_sweep = freq * np.exp(-8 * t)
    wave = np.sign(np.sin(2 * np.pi * freq_sweep * t))
    envelope = np.exp(-15 * t)
    wave = (wave * envelope * 32767 * 0.4).astype(np.int16)
    stereo = np.column_stack((wave, wave))   # ✅ mono → stéréo
    return pygame.sndarray.make_sound(stereo)

def make_explosion_sound(duration=0.4, sample_rate=44100):
    samples = int(sample_rate * duration)
    noise = np.random.uniform(-1, 1, samples)
    t = np.linspace(0, duration, samples)
    envelope = np.exp(-6 * t) * (1 - np.exp(-200 * t))
    wave = (noise * envelope * 32767 * 0.8).astype(np.int16)
    stereo = np.column_stack((wave, wave))   # ✅ mono → stéréo
    return pygame.sndarray.make_sound(stereo)

def make_powerup_sound(duration=0.3, sample_rate=44100):
    freqs = [261, 329, 392, 523]
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples)
    wave = np.zeros(samples)

    for i, f in enumerate(freqs):
        start = int(i * samples / 4)
        end   = int((i + 1) * samples / 4)
        seg  = np.sin(2 * np.pi * f * t[start:end])
        fade = np.exp(-3 * np.linspace(0, 1, end - start))
        wave[start:end] = seg * fade

    wave = (wave * 32767 * 0.5).astype(np.int16)
    stereo = np.column_stack((wave, wave))   # ✅ mono → stéréo
    return pygame.sndarray.make_sound(stereo)

def make_warp_sound(duration=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq_sweep = np.linspace(200, 2000, len(t))
    wave = np.sin(2 * np.pi * freq_sweep * t)
    envelope = np.exp(-2 * t)
    wave = (wave * envelope * 32767 * 0.5).astype(np.int16)
    stereo = np.column_stack((wave, wave))   # ✅ mono → stéréo
    return pygame.sndarray.make_sound(stereo)

# Générer les sons
print("Génération des sons...")
laser_snd     = make_laser_sound()
explosion_snd = make_explosion_sound()
powerup_snd   = make_powerup_sound()
warp_snd      = make_warp_sound()
print("Sons prêts !")

# Game Loop
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  running = False
            if event.key == pygame.K_l:       laser_snd.play()
            if event.key == pygame.K_e:       explosion_snd.play()
            if event.key == pygame.K_p:       powerup_snd.play()
            if event.key == pygame.K_w:       warp_snd.play()

    screen.fill((10, 10, 30))

    instructions = [
        ("L", "Laser",     (0, 200, 255)),
        ("E", "Explosion", (255, 100, 50)),
        ("P", "Power-up",  (0, 255, 150)),
        ("W", "Warp",      (255, 220, 0)),
    ]

    title = font.render("APPUIE SUR UNE TOUCHE", True, (200, 200, 200))
    screen.blit(title, (500//2 - title.get_width()//2, 40))

    for i, (key, label, color) in enumerate(instructions):
        txt = font.render(f"[ {key} ]  →  {label}", True, color)
        screen.blit(txt, (500//2 - txt.get_width()//2, 100 + i * 45))

    pygame.display.flip()

pygame.quit()
sys.exit()