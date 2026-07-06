# systems/adaptive_difficulty.py

class PlayerMetrics:
    def __init__(self):
        self.kills         = 0
        self.deaths        = 0
        self.bullets_fired = 0
        self.bullets_hit   = 0
        self.damage_taken  = 0
        self.time_elapsed  = 0.0
        self.powerups_taken= 0

    @property
    def accuracy(self):
        if self.bullets_fired == 0: return 0.5
        return min(1.0, self.bullets_hit / self.bullets_fired)

    @property
    def kpm(self):
        if self.time_elapsed < 1: return 0
        return self.kills / (self.time_elapsed / 60)

    @property
    def survival_ratio(self):
        if self.deaths == 0: return 1.0
        return max(0, 1 - self.deaths * 0.2)


class AdaptiveDifficulty:
    TARGET    = 1.0
    SMOOTHING = 0.05

    def __init__(self):
        self.difficulty_score = 1.0
        self.metrics          = PlayerMetrics()
        self.history          = []   # pour tracer le graphe

    def update(self, dt):
        self.metrics.time_elapsed += dt

        perf = (
            self.metrics.accuracy       * 0.4 +
            min(2, self.metrics.kpm/5)  * 0.3 +
            self.metrics.survival_ratio * 0.3
        ) * 2

        if perf > self.TARGET:
            self.difficulty_score = min(2.0,
                self.difficulty_score +
                self.SMOOTHING * dt * (perf - self.TARGET))
        else:
            self.difficulty_score = max(0.3,
                self.difficulty_score -
                self.SMOOTHING * dt * (self.TARGET - perf))

        # Sauvegarder l'historique toutes les secondes
        if int(self.metrics.time_elapsed) > len(self.history):
            self.history.append(round(self.difficulty_score, 3))

    def get_enemy_speed_mult(self):
        return 0.7 + self.difficulty_score * 0.4

    def get_spawn_rate_mult(self):
        return 0.6 + self.difficulty_score * 0.7

    def get_enemy_hp_mult(self):
        return 0.8 + self.difficulty_score * 0.6

    def get_powerup_rate(self):
        return max(0.05, 0.25 - self.difficulty_score * 0.08)

    def get_debug_info(self):
        m = self.metrics
        return {
            'difficulty' : round(self.difficulty_score, 2),
            'accuracy'   : f'{m.accuracy*100:.0f}%',
            'kpm'        : round(m.kpm, 1),
            'survival'   : round(m.survival_ratio, 2),
            'speed_mult' : round(self.get_enemy_speed_mult(), 2),
            'hp_mult'    : round(self.get_enemy_hp_mult(), 2),
        }