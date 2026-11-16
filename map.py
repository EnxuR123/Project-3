import pygame
import random

# Initialize Pygame
pygame.init()

# --- CONFIGURATION CONSTANTS ---
WIDTH, HEIGHT = 800, 800
FPS = 60
GRID_SIZE = 25  # Increased size for a better maze experience (25x25 grid)
CELL_SIZE = WIDTH // GRID_SIZE

# Colors
COLOR_BG = (22, 22, 29)         # Dark slate blue
COLOR_WALL = (145, 150, 163)     # Muted silver gray
COLOR_START = (39, 174, 96)      # Soft green
COLOR_GOAL = (192, 57, 43)       # Soft red
COLOR_PLAYER = (52, 152, 219)    # Bright blue
COLOR_VISITED = (44, 62, 80)     # Dark accent for carved rooms during generation
COLOR_CURRENT = (241, 196, 15)   # Gold marker for the generation head


# Item Colors
COLOR_CANDY = (241, 196, 15)    # Reward A: Candy
COLOR_POTION = (46, 204, 113)   # Reward B: Potion
COLOR_SPIDER = (155, 89, 182)   # Hazard A: Spider
COLOR_TRAP = (231, 76, 60)      # Hazard B: Trap

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Candy Heist")
clock = pygame.time.Clock()

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Walls ordered: [Top, Right, Bottom, Left]
        self.walls = [True, True, True, True]
        self.visited = False
        self.item = None

    def draw(self, surface, is_generating=False):
        """Draws the background cell area and its walls."""
        x_pix = self.x * CELL_SIZE
        y_pix = self.y * CELL_SIZE

        # Draw backgrounds during the live generation phase
        if is_generating and self.visited:
            pygame.draw.rect(surface, COLOR_VISITED, (x_pix, y_pix, CELL_SIZE, CELL_SIZE))

        # Render walls as distinct lines
        if self.walls[0]: # Top
            pygame.draw.line(surface, COLOR_WALL, (x_pix, y_pix), (x_pix + CELL_SIZE, y_pix), 2)
        if self.walls[1]: # Right
            pygame.draw.line(surface, COLOR_WALL, (x_pix + CELL_SIZE, y_pix), (x_pix + CELL_SIZE, y_pix + CELL_SIZE), 2)
        if self.walls[2]: # Bottom
            pygame.draw.line(surface, COLOR_WALL, (x_pix + CELL_SIZE, y_pix + CELL_SIZE), (x_pix, y_pix + CELL_SIZE), 2)
        if self.walls[3]: # Left
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
                    # Adjust movement cooldown frames based on status effects
                    if self.speed_boost_timer > 0:
                        self.move_delay = 5   # Very fast
                    elif self.slow_timer > 0:
                        self.move_delay = 22  # Slow
                    else:
                        self.move_delay = 10  # Normal speed
    
                    # Check item collection
                    new_cell = grid[self.y][self.x]
                    if new_cell.item == "candy":
                        self.score += 1
                        new_cell.item = None
                    elif new_cell.item == "potion":
                        self.speed_boost_timer = 300  # 5 seconds boost
                        new_cell.item = None
                    elif new_cell.item == "spider":
                        self.stun_timer = 120  # 2 seconds stun
                        new_cell.item = None
                    elif new_cell.item == "trap":
                        self.slow_timer = 240  # 4 seconds slow
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
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)] # Top, Right, Bottom, Left
    
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

    if dx == -1: # Next is right
        current.walls[1] = False
        next_cell.walls[3] = False
    elif dx == 1: # Next is left
        current.walls[3] = False
        next_cell.walls[1] = False
        
    if dy == -1: # Next is down
        current.walls[2] = False
        next_cell.walls[0] = False
    elif dy == 1: # Next is up
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
                grid[y][x].item = "candy"      # Reward A
            elif rand < 0.20:
                grid[y][x].item = "potion"     # Reward B
            elif rand < 0.25:
                grid[y][x].item = "spider"     # Hazard A
            elif rand < 0.30:
                grid[y][x].item = "trap"       # Hazard B

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

        # --- EVENT MANAGER SYSTEM ---
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

        # --- DRAWING SYSTEM ---
        # 1. Base Grid Layer
        for row in grid:
            for cell in row:
                cell.draw(screen, is_generating=generating)

        # 2. Draw Start and End Markers (When generation finishes)
        if not generating:
            pygame.draw.rect(screen, COLOR_START, (2, 2, CELL_SIZE - 2, CELL_SIZE - 2))
            pygame.draw.rect(screen, COLOR_GOAL, ((GRID_SIZE - 1) * CELL_SIZE + 2, (GRID_SIZE - 1) * CELL_SIZE + 2, CELL_SIZE - 2, CELL_SIZE - 2))
            # Draw the playable element overlay
            player.draw(screen)
        else:
            # Draw visual tracking box over the current algorithm generation head
            pygame.draw.rect(screen, COLOR_CURRENT, (current.x * CELL_SIZE + 3, current.y * CELL_SIZE + 3, CELL_SIZE - 6, CELL_SIZE - 6))

        pygame.display.flip()
        
        # Speed multiplier setup: run faster during generation to reduce wait time
        clock.tick(120 if generating else FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
