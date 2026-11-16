import pygame
import random
import heapq
pygame.init()

WIDTH, HEIGHT = 800, 800
FPS = 60
GRID_SIZE = 25  
CELL_SIZE = WIDTH // GRID_SIZE

COLOR_BG = (22, 22, 29)        
COLOR_WALL = (145, 150, 163)    
COLOR_START = (39, 174, 96)      
COLOR_GOAL = (192, 57, 43)      
COLOR_PLAYER = (52, 152, 219)  
COLOR_VISITED = (44, 62, 80)    
COLOR_CURRENT = (241, 196, 15)  


COLOR_CANDY = (241, 196, 15)  
COLOR_POTION = (46, 204, 113)  
COLOR_SPIDER = (155, 89, 182)  
COLOR_TRAP = (231, 76, 60)      

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Candy Heist")
clock = pygame.time.Clock()

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = [True, True, True, True]
        self.visited = False
        self.item = None

    def draw(self, surface, is_generating=False):
        """Draws the background cell area and its walls."""
        x_pix = self.x * CELL_SIZE
        y_pix = self.y * CELL_SIZE

        if is_generating and self.visited:
            pygame.draw.rect(surface, COLOR_VISITED, (x_pix, y_pix, CELL_SIZE, CELL_SIZE))

        if self.walls[0]:
            pygame.draw.line(surface, COLOR_WALL, (x_pix, y_pix), (x_pix + CELL_SIZE, y_pix), 2)
        if self.walls[1]:
            pygame.draw.line(surface, COLOR_WALL, (x_pix + CELL_SIZE, y_pix), (x_pix + CELL_SIZE, y_pix + CELL_SIZE), 2)
        if self.walls[2]:
            pygame.draw.line(surface, COLOR_WALL, (x_pix + CELL_SIZE, y_pix + CELL_SIZE), (x_pix, y_pix + CELL_SIZE), 2)
        if self.walls[3]:
            pygame.draw.line(surface, COLOR_WALL, (x_pix, y_pix + CELL_SIZE), (x_pix, y_pix), 2)


        if not is_generating and self.item:
                    cx = x_pix + (CELL_SIZE // 2)
                    cy = y_pix + (CELL_SIZE // 2)
                    if self.item == "candy":
                        pygame.draw.circle(surface, COLOR_CANDY, (cx, cy), CELL_SIZE // 5)
                    elif self.item == "potion":
                        pygame.draw.circle(surface, COLOR_POTION, (cx, cy), CELL_SIZE // 6)
                    elif self.item == "spider":
                        pygame.draw.circle(surface, COLOR_SPIDER, (cx, cy), CELL_SIZE // 4)
                    elif self.item == "trap":
                        pygame.draw.rect(surface, COLOR_TRAP, (cx - 5, cy - 5, 10, 10))


class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.score = 0
        self.stun_timer = 0
        self.slow_timer = 0
        self.speed_boost_timer = 0
        self.move_delay = 0

    def update(self):
            if self.stun_timer > 0:
                self.stun_timer -= 1
            if self.slow_timer > 0:
                self.slow_timer -= 1
            if self.speed_boost_timer > 0:
                self.speed_boost_timer -= 1
            if self.move_delay > 0:
                self.move_delay -= 1

    def move(self, keys, grid):
            if self.stun_timer > 0 or self.move_delay > 0:
                return
   
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = 1
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = 1
   
            if dx != 0 or dy != 0:
                current_cell = grid[self.y][self.x]
                moved = False
                if dx == 1 and not current_cell.walls[1]:
                    self.x += 1
                    moved = True
                elif dx == -1 and not current_cell.walls[3]:
                    self.x -= 1
                    moved = True
                elif dy == 1 and not current_cell.walls[2]:
                    self.y += 1
                    moved = True
                elif dy == -1 and not current_cell.walls[0]:
                    self.y -= 1
                    moved = True
   
                if moved:
                    if self.speed_boost_timer > 0:
                        self.move_delay = 5  
                    elif self.slow_timer > 0:
                        self.move_delay = 22  
                    else:
                        self.move_delay = 10  
   
                    new_cell = grid[self.y][self.x]
                    if new_cell.item == "candy":
                        self.score += 1
                        new_cell.item = None
                    elif new_cell.item == "potion":
                        self.speed_boost_timer = 300  
                        new_cell.item = None
                    elif new_cell.item == "spider":
                        self.stun_timer = 120
                        new_cell.item = None
                    elif new_cell.item == "trap":
                        self.slow_timer = 240  
                        new_cell.item = None

    def draw(self, surface):
        """Draws the player node in the middle of their current tracking cell."""
        center_x = (self.x * CELL_SIZE) + (CELL_SIZE // 2)
        center_y = (self.y * CELL_SIZE) + (CELL_SIZE // 2)
        radius = CELL_SIZE // 3
        pygame.draw.circle(surface, COLOR_PLAYER, (center_x, center_y), radius)


def get_neighbors(cell, grid):
    """Gathers all unvisited neighbors adjacent to the cell."""
    neighbors = []
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
   
    for dx, dy in directions:
        nx, ny = cell.x + dx, cell.y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            neighbor = grid[ny][nx]
            if not neighbor.visited:
                neighbors.append(neighbor)
    return neighbors


def remove_walls(current, next_cell):
    """Safely tears down the matching wall variables between two neighboring cells."""
    dx = current.x - next_cell.x
    dy = current.y - next_cell.y

    if dx == -1:
        current.walls[1] = False
        next_cell.walls[3] = False
    elif dx == 1:
        current.walls[3] = False
        next_cell.walls[1] = False
       
    if dy == -1:
        current.walls[2] = False
        next_cell.walls[0] = False
    elif dy == 1:
        current.walls[0] = False
        next_cell.walls[2] = False

def braid_maze(grid):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = grid[y][x]
            if random.random() < 0.25:
                if x < GRID_SIZE - 1 and cell.walls[1]:
                    cell.walls[1] = False
                    grid[y][x + 1].walls[3] = False
                elif y < GRID_SIZE - 1 and cell.walls[2]:
                    cell.walls[2] = False
                    grid[y + 1][x].walls[0] = False

def spawn_items(grid):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if (x == 0 and y == 0) or (x == GRID_SIZE - 1 and y == GRID_SIZE - 1):
                continue
            rand = random.random()
            if rand < 0.15:
                grid[y][x].item = "candy"      
            elif rand < 0.20:
                grid[y][x].item = "potion"    
            elif rand < 0.25:
                grid[y][x].item = "spider"    
            elif rand < 0.30:
                grid[y][x].item = "trap"      

def reset_generation_state():
    """Initializes a new grid template, structural generation trackers, and stack chains."""
    grid = [[Cell(x, y) for x in range(GRID_SIZE)] for y in range(GRID_SIZE)]
    stack = []
    current = grid[0][0]
    current.visited = True
    generating = True
    return grid, stack, current, generating


def main():
    grid, stack, current, generating = reset_generation_state()
    player = Player()
    running = True

    while running:
        screen.fill(COLOR_BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_SPACE:
                                grid, stack, current, generating = reset_generation_state()
                                player.x, player.y = 0, 0
                                player.score = 0
                                player.stun_timer = 0
                                player.slow_timer = 0
                                player.speed_boost_timer = 0
                                player.move_delay = 0
               
        if generating:
                    neighbors = get_neighbors(current, grid)
                    if neighbors:
                        next_cell = random.choice(neighbors)
                        stack.append(current)
                        remove_walls(current, next_cell)
                        next_cell.visited = True
                        current = next_cell
                    elif stack:
                        current = stack.pop()
                    else:
                        braid_maze(grid)
                        spawn_items(grid)
                        generating = False
        else:
            player.update()
            keys = pygame.key.get_pressed()
            player.move(keys, grid)

        for row in grid:
            for cell in row:
                cell.draw(screen, is_generating=generating)

        if not generating:
            pygame.draw.rect(screen, COLOR_START, (2, 2, CELL_SIZE - 2, CELL_SIZE - 2))
            pygame.draw.rect(screen, COLOR_GOAL, ((GRID_SIZE - 1) * CELL_SIZE + 2, (GRID_SIZE - 1) * CELL_SIZE + 2, CELL_SIZE - 2, CELL_SIZE - 2))
            player.draw(screen)
        else:
            pygame.draw.rect(screen, COLOR_CURRENT, (current.x * CELL_SIZE + 3, current.y * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6))

        pygame.display.flip()
       
        clock.tick(120 if generating else FPS)

from collections import defaultdict, deque

DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
NAMES = ["U", "R", "D", "L"]


def passages(grid, position):
    x, y = position
    return [
        (i, (x + dx, y + dy))
        for i, (dx, dy) in enumerate(DIRS)
        if 0 <= x + dx < GRID_SIZE
        and 0 <= y + dy < GRID_SIZE
        and not grid[y][x].walls[i]
    ]


def astar(grid, start, goal):
    queue = [(0, start)]
    costs = {start: 0}
    parents = {start: None}

    while queue:
        _, current = heapq.heappop(queue)

        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = parents[current]
            return path[::-1]

        for _, neighbor in passages(grid, current):
            cost = costs[current] + 1
            if cost < costs.get(neighbor, float("inf")):
                costs[neighbor] = cost
                parents[neighbor] = current
                h = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                heapq.heappush(queue, (cost + h, neighbor))

    return []


class Predictor:
    def __init__(self):
        self.history = deque(maxlen=8)
        self.one = defaultdict(lambda: [0] * 4)
        self.two = defaultdict(lambda: [0] * 4)

    def record(self, direction):
        if self.history:
            self.one[self.history[-1]][direction] += 1
        if len(self.history) >= 2:
            self.two[tuple(self.history)[-2:]][direction] += 1
        self.history.append(direction)

    def probabilities(self, history=None):
        history = tuple(self.history if history is None else history)
        row = self.one[history[-1]] if history else [0] * 4

        if len(history) >= 2 and sum(self.two[history[-2:]]) >= 3:
            row = self.two[history[-2:]]

        return [(count + 1) / (sum(row) + 4) for count in row]


class Enemy:
    def __init__(self, position, boss=False):
        self.position = position
        self.boss = boss
        self.state = "WANDER"
        self.path = []
        self.candidates = []
        self.next_move = self.next_plan = self.search_until = 0

    def update(self, grid, player_position, predictor, now):
        if self.boss and now >= self.next_plan:
            self.next_plan = now + 650
            position = player_position
            history = tuple(predictor.history)
            probability = 1.0
            self.candidates = []
            options = []

            for _ in range(3):
                legal = passages(grid, position)
                if not legal:
                    break

                probabilities = predictor.probabilities(history)
                direction, position = max(
                    legal, key=lambda move: probabilities[move[0]]
                )
                probability *= probabilities[direction] / sum(
                    probabilities[i] for i, _ in legal
                )
                history = (*history[-1:], direction)
                path = astar(grid, self.position, position)
                self.candidates.append(position)

                if position != player_position:
                    utility = 8 * probability - 0.12 * len(path)
                    options.append((utility, path))

            self.path = (
                max(options, key=lambda option: option[0])[1]
                if options else astar(grid, self.position, player_position)
            )

        if now < self.next_move:
            return

        if not self.boss:
            chase = astar(grid, self.position, player_position)

            if self.position == player_position or 0 < len(chase) <= 6:
                self.state, self.path = "CHASE", chase

            elif self.state == "CHASE":
                self.state = "SEARCH"
                self.search_until = now + 3000

            elif self.state == "SEARCH" and now >= self.search_until:
                self.state, self.path = "WANDER", []

            if self.state == "WANDER" and not self.path:
                legal = passages(grid, self.position)
                self.path = [random.choice(legal)[1]] if legal else []

        if self.path:
            self.position = self.path.pop(0)

        self.next_move = now + (
            420 if self.boss or self.state == "CHASE" else 550
        )


def center(position):
    return (
        position[0] * CELL_SIZE + CELL_SIZE // 2,
        position[1] * CELL_SIZE + CELL_SIZE // 2,
    )


def main():
    global screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 90))
    font = pygame.font.Font(None, 24)
    title_font = pygame.font.Font(None, 48)
    restart_button = pygame.Rect(205, 430, 180, 45)
    quit_button = pygame.Rect(415, 430, 180, 45)
    running = True
    debug = False

    while running:
        grid, stack, current, generating = reset_generation_state()
        player = Player()
        predictor = Predictor()
        boss = Enemy((GRID_SIZE - 1, GRID_SIZE - 1), True)
        ghosts = []
        result = ""
        total = started = immunity_until = 0
        time_limit = remaining = 300
        restart = False

        while running and not restart:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_F1:
                        debug = not debug
                    elif event.key in (pygame.K_SPACE, pygame.K_r):
                        restart = True

                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1 and result
                ):
                    if restart_button.collidepoint(event.pos):
                        restart = True
                    elif quit_button.collidepoint(event.pos):
                        running = False

            if not running or restart:
                break

            if generating:
                for _ in range(14):
                    neighbors = get_neighbors(current, grid)

                    if neighbors:
                        next_cell = random.choice(neighbors)
                        stack.append(current)
                        remove_walls(current, next_cell)
                        next_cell.visited = True
                        current = next_cell

                    elif stack:
                        current = stack.pop()

                    else:
                        braid_maze(grid)
                        spawn_items(grid)
                        grid[0][1].item = "candy"

                        total = sum(
                            cell.item == "candy"
                            for row in grid for cell in row
                        )
                        positions = [
                            (x, y)
                            for y in range(GRID_SIZE)
                            for x in range(GRID_SIZE)
                            if (x, y) != boss.position and x + y > 12
                        ]
                        ghosts = [
                            Enemy(pos)
                            for pos in random.sample(positions, 3)
                        ]
                        hazards = sum(
                            cell.item in ("spider", "trap")
                            for row in grid for cell in row
                        )
                        time_limit = max(300, total * 2 + hazards * 3)
                        remaining, started = time_limit, now
                        generating = False
                        break

            elif not result:
                player.update()
                old_position = (player.x, player.y)
                player.move(pygame.key.get_pressed(), grid)
                position = (player.x, player.y)

                if position != old_position:
                    move = (
                        position[0] - old_position[0],
                        position[1] - old_position[1],
                    )
                    predictor.record(DIRS.index(move))

                if position == boss.position:
                    result = "You Lose - caught by the boss!"

                else:
                    for ghost in ghosts:
                        touching = ghost.position == position
                        ghost.update(grid, position, predictor, now)

                        if (
                            touching or ghost.position == position
                        ) and now >= immunity_until:
                            player.stun_timer = 120
                            immunity_until = now + 5000

                    if now - started >= 10000:
                        boss.update(grid, position, predictor, now)

                    remaining = max(
                        0, time_limit - (now - started) // 1000
                    )

                    if boss.position == position:
                        result = "You Lose - caught by the boss!"
                    elif remaining == 0:
                        result = "You Lose - time ran out!"
                    elif player.score == total:
                        result = "You Win!"

            screen.fill(COLOR_BG)
            for row in grid:
                for cell in row:
                    cell.draw(screen, is_generating=generating)

            if generating:
                pygame.draw.rect(
                    screen, COLOR_CURRENT,
                    (
                        current.x * CELL_SIZE + 3,
                        current.y * CELL_SIZE + 3,
                        CELL_SIZE - 6, CELL_SIZE - 6,
                    ),
                )

            else:
                for position, color in [
                    ((0, 0), COLOR_START),
                    (boss.position, COLOR_GOAL),
                ]:
                    cx, cy = center(position)
                    pygame.draw.rect(
                        screen, color, (cx - 13, cy - 13, 26, 26), 2
                    )

                if debug:
                    for position in boss.candidates:
                        pygame.draw.circle(
                            screen, COLOR_CANDY, center(position), 12, 2
                        )

                    for enemy in ghosts + [boss]:
                        points = [
                            center(pos)
                            for pos in [enemy.position] + enemy.path
                        ]
                        if len(points) > 1:
                            pygame.draw.lines(
                                screen,
                                COLOR_TRAP if enemy.boss else COLOR_SPIDER,
                                False, points, 2,
                            )

                for ghost in ghosts:
                    pygame.draw.circle(
                        screen, COLOR_SPIDER, center(ghost.position), 10
                    )
                    if debug:
                        x, y = center(ghost.position)
                        screen.blit(
                            font.render(
                                ghost.state, True, (255, 255, 255)
                            ),
                            (
                                max(0, min(WIDTH - 95, x - 28)),
                                max(0, y - 27),
                            ),
                        )

                pygame.draw.circle(
                    screen, COLOR_TRAP, center(boss.position), 14
                )
                player.draw(screen)

            text = (
                f"Candy: {player.score}/{total}   "
                f"Time: {remaining // 60}:{remaining % 60:02}"
            )
            if generating:
                text = "Generating maze..."

            screen.blit(
                font.render(text, True, COLOR_CANDY),
                (10, HEIGHT + 5),
            )
            screen.blit(
                font.render(
                    "WASD/Arrows: move | F1: debug | "
                    "Space/R: restart | Esc/Q: quit",
                    True, (230, 230, 230),
                ),
                (10, HEIGHT + 32),
            )

            if debug:
                history = " ".join(
                    NAMES[i] for i in predictor.history
                ) or "none"
                prediction = " ".join(
                    f"{name}:{p:.0%}"
                    for name, p in zip(NAMES, predictor.probabilities())
                )
                screen.blit(
                    font.render(
                        f"Last: {history} | Next: {prediction}",
                        True, COLOR_SPIDER,
                    ),
                    (10, HEIGHT + 59),
                )

            if result:
                pygame.draw.rect(
                    screen, COLOR_BG, (75, 315, 650, 185)
                )
                label = title_font.render(
                    result, True, COLOR_CANDY
                )
                screen.blit(
                    label, label.get_rect(center=(WIDTH // 2, 370))
                )
                for rect, label in [
                    (restart_button, "Restart"),
                    (quit_button, "Quit"),
                ]:
                    pygame.draw.rect(screen, COLOR_WALL, rect)
                    image = font.render(label, True, COLOR_BG)
                    screen.blit(
                        image, image.get_rect(center=rect.center)
                    )

            pygame.display.flip()
            clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()