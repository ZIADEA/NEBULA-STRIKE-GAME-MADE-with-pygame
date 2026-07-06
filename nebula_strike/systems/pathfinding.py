# systems/pathfinding.py
import heapq, math, pygame
from settings import WIDTH, HEIGHT

CELL = 40
COLS = WIDTH  // CELL
ROWS = HEIGHT // CELL

class AStar:
    def __init__(self):
        self.grid = [[0]*COLS for _ in range(ROWS)]

    def set_obstacle(self, x, y, w, h):
        c0 = max(0, x // CELL)
        c1 = min(COLS-1, (x+w) // CELL)
        r0 = max(0, y // CELL)
        r1 = min(ROWS-1, (y+h) // CELL)
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                self.grid[r][c] = 1

    def clear(self):
        self.grid = [[0]*COLS for _ in range(ROWS)]

    def find_path(self, start_px, goal_px):
        start = (int(start_px[1])//CELL, int(start_px[0])//CELL)
        goal  = (int(goal_px[1]) //CELL, int(goal_px[0]) //CELL)

        # Clamp dans la grille
        start = (max(0,min(ROWS-1,start[0])), max(0,min(COLS-1,start[1])))
        goal  = (max(0,min(ROWS-1,goal[0])),  max(0,min(COLS-1,goal[1])))

        if self.grid[goal[0]][goal[1]] == 1:
            return []

        open_set  = [(0, start)]
        came_from = {}
        g_score   = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                return self._reconstruct(came_from, current)

            r, c = current
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),
                           (-1,-1),(-1,1),(1,-1),(1,1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < ROWS and 0 <= nc < COLS): continue
                if self.grid[nr][nc] == 1:                  continue

                move_cost = 1.414 if dr and dc else 1.0
                tentative = g_score[current] + move_cost
                neighbor  = (nr, nc)

                if tentative < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor]   = tentative
                    h = math.hypot(goal[0]-nr, goal[1]-nc)
                    heapq.heappush(open_set, (tentative+h, neighbor))

        return []

    def _reconstruct(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return [(c*CELL + CELL//2, r*CELL + CELL//2) for r, c in path]


class NavigatorEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y, astar):
        super().__init__()
        self.pos         = pygame.math.Vector2(x, y)
        self.astar       = astar
        self.path        = []
        self.path_timer  = 0
        self.hp          = 50
        self.max_hp      = 50
        self.score_value = 400

        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (0,255,180),
                            [(16,0),(32,32),(16,24),(0,32)])
        self.rect  = self.image.get_rect(center=(x, y))

    def update(self, dt, player, bullets_group=None):
        # Recalculer le chemin toutes les 0.8s
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path_timer = 0.8
            self.path = self.astar.find_path(
                (self.pos.x, self.pos.y),
                (player.pos.x, player.pos.y)
            )

        # Suivre le prochain waypoint
        if self.path:
            waypoint  = pygame.math.Vector2(self.path[0])
            direction = waypoint - self.pos
            if direction.length() < 8:
                self.path.pop(0)
            elif direction.length() > 0:
                self.pos += direction.normalize() * 2.5
        else:
            self.pos.y += 1.5

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.rect.top > HEIGHT:
            self.kill()

    def take_damage(self, dmg, ps=None):
        self.hp -= dmg
        if ps:
            ps.spawn_explosion(self.pos.x, self.pos.y, (0,255,180), count=6, speed=2)
        return self.hp <= 0

    def draw_health_bar(self, surface):
        w     = self.rect.width
        ratio = max(0, self.hp / self.max_hp)
        bar   = pygame.Rect(self.rect.left, self.rect.top - 8, w, 5)
        pygame.draw.rect(surface, (80,0,0),    bar)
        pygame.draw.rect(surface, (0,200,100), (bar.x, bar.y, int(w*ratio), 5))