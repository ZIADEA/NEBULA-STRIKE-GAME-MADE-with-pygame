# systems/sound_manager.py
import numpy as np
import pygame

class SoundManager:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sounds = {}
        self._generate_all()

    def _generate_all(self):
        self.sounds['laser']      = self._laser()
        self.sounds['explosion']  = self._explosion()
        self.sounds['hit']        = self._hit()
        self.sounds['powerup']    = self._powerup()
        self.sounds['emp']        = self._emp()
        self.sounds['boss_enter'] = self._boss_enter()
        self.sounds['boss_phase'] = self._boss_phase()
        self.sounds['boss_die']   = self._boss_die()

    def _make(self, wave, volume=0.5):
        """Convertit un tableau numpy en son stéréo Pygame."""
        wave = (wave * 32767 * volume).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        return pygame.sndarray.make_sound(stereo)

    def _laser(self):
        t = np.linspace(0, 0.08, int(44100 * 0.08))
        freq = 880 * np.exp(-8 * t)
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * np.exp(-15 * t)
        return self._make(wave, 0.4)

    def _explosion(self):
        t = np.linspace(0, 0.4, int(44100 * 0.4))
        noise = np.random.uniform(-1, 1, len(t))
        env = np.exp(-6 * t) * (1 - np.exp(-200 * t))
        return self._make(noise * env, 0.8)

    def _hit(self):
        t = np.linspace(0, 0.15, int(44100 * 0.15))
        wave = np.sign(np.sin(2 * np.pi * 200 * np.exp(-5*t) * t))
        env  = np.exp(-20 * t)
        return self._make(wave * env, 0.5)

    def _powerup(self):
        freqs   = [261, 329, 392, 523]
        samples = int(44100 * 0.3)
        t       = np.linspace(0, 0.3, samples)
        wave    = np.zeros(samples)
        for i, f in enumerate(freqs):
            s = int(i * samples / 4)
            e = int((i+1) * samples / 4)
            wave[s:e] = np.sin(2*np.pi*f*t[s:e]) * np.exp(-3*np.linspace(0,1,e-s))
        return self._make(wave, 0.5)

    def _emp(self):
        t    = np.linspace(0, 0.5, int(44100 * 0.5))
        wave = np.sin(2 * np.pi * np.linspace(100, 50, len(t)) * t)
        env  = np.exp(-3 * t)
        return self._make(wave * env, 0.7)

    def _boss_enter(self):
        t    = np.linspace(0, 1.0, int(44100 * 1.0))
        wave = np.sin(2 * np.pi * np.linspace(80, 300, len(t)) * t)
        env  = np.exp(-2 * t)
        return self._make(wave * env, 0.6)

    def _boss_phase(self):
        t    = np.linspace(0, 0.3, int(44100 * 0.3))
        wave = np.sign(np.sin(2 * np.pi * 440 * t)) * np.exp(-5 * t)
        return self._make(wave, 0.5)

    def _boss_die(self):
        t     = np.linspace(0, 1.5, int(44100 * 1.5))
        noise = np.random.uniform(-1, 1, len(t))
        env   = np.exp(-2 * t) * (1 - np.exp(-50 * t))
        return self._make(noise * env, 0.9)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()
