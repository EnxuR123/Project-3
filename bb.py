import pygame
import random
import heapq
from collections import defaultdict, deque

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
COLOR_CANDY = (241, 196, 15)
COLOR_POTION = (46, 204, 113)
COLOR_SPIDER = (155, 89, 182)
COLOR_TRAP = (231, 76, 60)

DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
NAMES = ["U", "R", "D", "L"]

screen = pygame.display.set_mode((WIDTH, HEIGHT + 90))
pygame.display.set_caption("The Candy Heist")
clock = pygame.time.Clock()


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = [True, True, True, True]
        self.visited = False
        self.item = None

    def draw(self, surface):
        x = self.x * CELL_SIZE
        y = self.y * CELL_SIZE
        corners = [
            (x, y),
            (x + CELL_SIZE, y),
            (x + CELL_SIZE, y + CELL_SIZE),
            (x, y + CELL_SIZE),
        ]

        for i, wall in enumerate(self.walls):
            if wall:
                pygame.draw.line(
                    surface, COLOR_WALL,
                    corners[i], corners[(i + 1) % 4], 2
                )

        cx = x + CELL_SIZE // 2
        cy = y + CELL_SIZE // 2

        if self.item == "candy":
            pygame.draw.circle(
                surface, COLOR_CANDY, (cx, cy), CELL_SIZE // 5
            )
        elif self.item == "potion":
            pygame.draw.circle(
                surface, COLOR_POTION, (cx, cy), CELL_SIZE // 6
            )
        elif self.item == "spider":
            pygame.draw.circle(
                surface, COLOR_SPIDER, (cx, cy), CELL_SIZE // 4
            )
        elif self.item == "trap":
            pygame.draw.rect(
                surface, COLOR_TRAP, (cx - 5, cy - 5, 10, 10)
            )


class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.score = 0
        self.facing = 1
        self.stun_timer = 0
        self.slow_timer = 0
        self.speed_boost_timer = 0
        self.move_delay = 0

    def update(self):
        for name in (
            "stun_timer", "slow_timer",
            "speed_boost_timer", "move_delay"
        ):
            setattr(self, name, max(0, getattr(self, name) - 1))

    def move(self, keys, grid):
        controls = [
            (0, (pygame.K_w, pygame.K_UP)),
            (2, (pygame.K_s, pygame.K_DOWN)),
            (3, (pygame.K_a, pygame.K_LEFT)),
            (1, (pygame.K_d, pygame.K_RIGHT)),
        ]

        direction = None
        for facing, buttons in controls:
            if any(keys[key] for key in buttons):
                direction = facing
                self.facing = facing
                break

        if (
            direction is None
            or self.stun_timer > 0
            or self.move_delay > 0
        ):
            return

        if grid[self.y][self.x].walls[direction]:
            return

        dx, dy = DIRS[direction]
        self.x += dx
        self.y += dy

        if self.speed_boost_timer > 0:
            self.move_delay = 5
        elif self.slow_timer > 0:
            self.move_delay = 22
        else:
            self.move_delay = 10

        cell = grid[self.y][self.x]
        if cell.item == "candy":
            self.score += 1
        elif cell.item == "potion":
            self.speed_boost_timer = 300
        elif cell.item == "spider":
            self.stun_timer = 120
        elif cell.item == "trap":
            self.slow_timer = 240

        cell.item = None

    def draw(self, surface):
        x, y = center((self.x, self.y))
        pygame.draw.circle(
            surface, COLOR_PLAYER, (x, y), CELL_SIZE // 3
        )

        # White line shows which way you are looking.
        dx, dy = DIRS[self.facing]
        pygame.draw.line(
            surface, (255, 255, 255),
            (x, y), (x + dx * 8, y + dy * 8), 2
        )


def get_neighbors(cell, grid):
    neighbors = []
    for dx, dy in DIRS:
        x, y = cell.x + dx, cell.y + dy
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            if not grid[y][x].visited:
                neighbors.append(grid[y][x])
    return neighbors


def remove_walls(current, next_cell):
    direction = DIRS.index(
        (next_cell.x - current.x, next_cell.y - current.y)
    )
    current.walls[direction] = False
    next_cell.walls[(direction + 2) % 4] = False


def braid_maze(grid):
    for row in grid:
        for cell in row:
            if random.random() < 0.25:
                if cell.x < GRID_SIZE - 1 and cell.walls[1]:
                    remove_walls(cell, grid[cell.y][cell.x + 1])
                elif cell.y < GRID_SIZE - 1 and cell.walls[2]:
                    remove_walls(cell, grid[cell.y + 1][cell.x])


def spawn_items(grid, candy_percent=15):
    cells = [
        cell for row in grid for cell in row
        if (cell.x, cell.y) not in (
            (0, 0), (GRID_SIZE - 1, GRID_SIZE - 1)
        )
    ]
    random.shuffle(cells)

    for cell in cells:
        cell.item = None

    # Percentage of the whole map, rounded to a whole cell.
    count = min(
        len(cells),
        max(1, round(GRID_SIZE * GRID_SIZE * candy_percent / 100))
    )

    for cell in cells[:count]:
        cell.item = "candy"

    remaining = cells[count:]
    for item in ("potion", "spider", "trap"):
        amount = min(
            len(remaining), round(GRID_SIZE * GRID_SIZE * 0.05)
        )
        for cell in remaining[:amount]:
            cell.item = item
        remaining = remaining[amount:]

    return count


def reset_generation_state():
    grid = [
        [Cell(x, y) for x in range(GRID_SIZE)]
        for y in range(GRID_SIZE)
    ]
    current = grid[0][0]
    current.visited = True
    return grid, [], current, True


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
                h = (
                    abs(neighbor[0] - goal[0])
                    + abs(neighbor[1] - goal[1])
                )
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
        history = tuple(
            self.history if history is None else history
        )
        row = self.one[history[-1]] if history else [0] * 4

        if len(history) >= 2 and sum(self.two[history[-2:]]) >= 3:
            row = self.two[history[-2:]]

        return [
            (count + 1) / (sum(row) + 4)
            for count in row
        ]


class Enemy:
    def __init__(self, position, boss=False):
        self.position = position
        self.boss = boss
        self.state = "WANDER"
        self.path = []
        self.candidates = []
        self.next_move = 0
        self.next_plan = 0
        self.search_until = 0

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
                    legal,
                    key=lambda move: probabilities[move[0]]
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
                if options
                else astar(grid, self.position, player_position)
            )

        if self.boss:
            if player_position != getattr(self, "last_player_position", None):
                self.last_player_position = player_position
                self.last_player_move = now

            direct_path = astar(grid, self.position, player_position)

            if (
                not self.path
                or len(direct_path) <= 3
                or now - self.last_player_move >= 1500
            ):
                self.path = direct_path

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
        position[1] * CELL_SIZE + CELL_SIZE // 2
    )


# Built-in pixel letters. No font or image files are needed.
GLYPHS = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01111 10000 10000 10000 10000 10000 01111",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01111 10000 10000 10111 10001 10001 01110",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 10010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 10000 11110 00001 00001 11110",
    "6": "01110 10000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00001 01110",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    ":": "00000 00100 00100 00000 00100 00100 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
}


def pixel_text(text, y, scale=3, color=(255, 255, 255)):
    x = (WIDTH - (len(text) * 6 - 1) * scale) // 2

    for letter in text.upper():
        for row, line in enumerate(GLYPHS.get(letter, "").split()):
            for column, pixel in enumerate(line):
                if pixel == "1":
                    pygame.draw.rect(
                        screen, color,
                        (
                            x + column * scale,
                            y + row * scale,
                            scale, scale
                        )
                    )
        x += 6 * scale


def start_menu(candy_percent=15):
    presets = [5, 15, 30]
    start_button = pygame.Rect(175, 320, 450, 70)
    minus_button = pygame.Rect(180, 450, 60, 50)
    plus_button = pygame.Rect(560, 450, 60, 50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return None
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return candy_percent

                if event.key in (pygame.K_LEFT, pygame.K_a):
                    candy_percent = max(1, candy_percent - 1)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    candy_percent = min(70, candy_percent + 1)

                if event.key in (pygame.K_UP, pygame.K_w):
                    candy_percent = next(
                        (p for p in reversed(presets) if p < candy_percent),
                        5
                    )
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    candy_percent = next(
                        (p for p in presets if p > candy_percent),
                        30
                    )

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    return candy_percent
                if minus_button.collidepoint(event.pos):
                    candy_percent = max(1, candy_percent - 1)
                if plus_button.collidepoint(event.pos):
                    candy_percent = min(70, candy_percent + 1)

        difficulty = {
            5: "EASY", 15: "NORMAL", 30: "HARD"
        }.get(candy_percent, "CUSTOM")

        screen.fill((0, 0, 0))
        pixel_text("THE CANDY HEIST", 180, 4, (160, 160, 160))

        if pygame.time.get_ticks() // 600 % 2 == 0:
            pixel_text("PRESS START", 335, 6)

        pixel_text(difficulty, 465, 3)

        for button in (minus_button, plus_button):
            pygame.draw.rect(screen, (255, 255, 255), button, 2)
            cx, cy = button.center
            pygame.draw.line(
                screen, (255, 255, 255),
                (cx - 10, cy), (cx + 10, cy), 3
            )

        cx, cy = plus_button.center
        pygame.draw.line(
            screen, (255, 255, 255),
            (cx, cy - 10), (cx, cy + 10), 3
        )

        pixel_text(
            "CANDY: " + str(candy_percent) + "% OF MAP", 530, 3
        )
        pixel_text(
            "LEFT/RIGHT: ADJUST PERCENT", 615, 2, (170, 170, 170)
        )
        pixel_text(
            "UP/DOWN: DIFFICULTY PRESETS", 650, 2, (170, 170, 170)
        )
        pixel_text("ENTER OR CLICK PRESS START", 710, 2)
        pixel_text("ESC: QUIT", 755, 2, (170, 170, 170))

        pygame.display.flip()
        clock.tick(FPS)


def visible_cells(grid, player):
    position = (player.x, player.y)
    visible = [position]
    dx, dy = DIRS[player.facing]

    for _ in range(2):
        x, y = position

        if grid[y][x].walls[player.facing]:
            break

        position = (x + dx, y + dy)
        if not (
            0 <= position[0] < GRID_SIZE
            and 0 <= position[1] < GRID_SIZE
        ):
            break

        visible.append(position)

    return visible


def warning_alpha(grid, player_position, boss_position):
    # Count actual maze steps, including turns around walls.
    path = astar(grid, player_position, boss_position)

    if not path and player_position != boss_position:
        return 0

    distance = len(path)
    return min(170, (9 - distance) * 20) if distance <= 8 else 0


def draw_flashlight(grid, player):
    visible = visible_cells(grid, player)
    darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, 255))

    for x, y in visible:
        darkness.fill(
            (0, 0, 0, 0),
            (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        )

    screen.blit(darkness, (0, 0))

    for x, y in visible:
        left = x * CELL_SIZE + 2
        top = y * CELL_SIZE + 2
        right = (x + 1) * CELL_SIZE - 3
        bottom = (y + 1) * CELL_SIZE - 3

        corners = [
            (left, top), (right, top),
            (right, bottom), (left, bottom)
        ]

        for direction, wall in enumerate(grid[y][x].walls):
            if wall:
                color = (
                    COLOR_CANDY
                    if direction == player.facing
                    else COLOR_WALL
                )

                pygame.draw.line(
                    screen, color,
                    corners[direction],
                    corners[(direction + 1) % 4], 3
                )


def main():
    font = pygame.font.Font(None, 24)
    title_font = pygame.font.Font(None, 48)
    restart_button = pygame.Rect(205, 430, 180, 45)
    quit_button = pygame.Rect(415, 430, 180, 45)
    running = True
    debug = False
    candy_percent = 15

    while running:
        candy_percent = start_menu(candy_percent)
        if candy_percent is None:
            break

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
                        total = spawn_items(grid, candy_percent)

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
                        time_limit = max(
                            300, total * 2 + hazards * 3
                        )
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
                        position[1] - old_position[1]
                    )
                    predictor.record(DIRS.index(move))

                if position == boss.position:
                    result = "You Lose - caught by the boss!"

                else:
                    for ghost in ghosts:
                        touching = ghost.position == position
                        ghost.update(
                            grid, position, predictor, now
                        )
                        if (
                            touching or ghost.position == position
                        ) and now >= immunity_until:
                            player.stun_timer = 120
                            immunity_until = now + 5000

                    if now - started >= 10000:
                        boss.update(
                            grid, position, predictor, now
                        )

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

            if generating:
                screen.fill((0, 0, 0))
                pixel_text("BUILDING MAZE", 360, 4)
                visited = sum(
                    cell.visited
                    for row in grid for cell in row
                )
                pygame.draw.rect(
                    screen, (100, 100, 100),
                    (150, 440, 500, 12), 1
                )
                pygame.draw.rect(
                    screen, (255, 255, 255),
                    (
                        152, 442,
                        int(496 * visited / (GRID_SIZE ** 2)), 8
                    )
                )

            else:
                for row in grid:
                    for cell in row:
                        cell.draw(screen)

                for position, color in [
                    ((0, 0), COLOR_START),
                    (boss.position, COLOR_GOAL)
                ]:
                    cx, cy = center(position)
                    pygame.draw.rect(
                        screen, color,
                        (cx - 13, cy - 13, 26, 26), 2
                    )

                if debug:
                    for position in boss.candidates:
                        pygame.draw.circle(
                            screen, COLOR_CANDY,
                            center(position), 12, 2
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
                                False, points, 2
                            )

                for ghost in ghosts:
                    pygame.draw.circle(
                        screen, COLOR_SPIDER,
                        center(ghost.position), 10
                    )
                    if debug:
                        x, y = center(ghost.position)
                        screen.blit(
                            font.render(
                                ghost.state, True, (255, 255, 255)
                            ),
                            (
                                max(0, min(WIDTH - 95, x - 28)),
                                max(0, y - 27)
                            )
                        )

                pygame.draw.circle(
                    screen, COLOR_TRAP,
                    center(boss.position), 14
                )
                player.draw(screen)

                draw_flashlight(grid, player)

            text = (
                f"Candy: {player.score}/{total} ({candy_percent}% map)   "
                f"Time: {remaining // 60}:{remaining % 60:02}"
            )
            screen.blit(
                font.render(
                    "Generating maze..." if generating else text,
                    True, COLOR_CANDY
                ),
                (10, HEIGHT + 5)
            )
            screen.blit(
                font.render(
                    "WASD/Arrows: move/turn | F1: debug | "
                    "R/Space: menu | Esc/Q: quit",
                    True, (230, 230, 230)
                ),
                (10, HEIGHT + 32)
            )

            if debug:
                history = " ".join(
                    NAMES[i] for i in predictor.history
                ) or "none"
                prediction = " ".join(
                    f"{name}:{p:.0%}"
                    for name, p in zip(
                        NAMES, predictor.probabilities()
                    )
                )
                screen.blit(
                    font.render(
                        f"Last: {history} | Next: {prediction}",
                        True, COLOR_SPIDER
                    ),
                    (10, HEIGHT + 59)
                )

            if not generating:
                alpha = warning_alpha(
                    grid, (player.x, player.y), boss.position
                )
                if alpha:
                    tint = pygame.Surface(
                        screen.get_size(), pygame.SRCALPHA
                    )
                    tint.fill((160, 0, 0, alpha))
                    screen.blit(tint, (0, 0))

            if result:
                pygame.draw.rect(
                    screen, COLOR_BG, (75, 315, 650, 185)
                )
                label = title_font.render(
                    result, True, COLOR_CANDY
                )
                screen.blit(
                    label,
                    label.get_rect(center=(WIDTH // 2, 370))
                )

                for rect, label in [
                    (restart_button, "Restart"),
                    (quit_button, "Quit")
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
