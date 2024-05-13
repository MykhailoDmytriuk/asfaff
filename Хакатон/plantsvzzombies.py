import random
import pygame
from pygame.locals import *
pygame.init()

window_width = 1200
window_height = 600
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Plants vs. Zombies")

image = pygame.image.load("Background_0.jpg")
chooser_background = pygame.image.load("ChooserBackground.png").convert()
sunflower_card = pygame.image.load("card_sunflower.png").convert_alpha()
explode_image = pygame.image.load("PeaNormalExplode_0.png").convert_alpha()
peashooter_card = pygame.image.load("card_peashooter.png").convert_alpha()
sunflower_card = pygame.transform.scale(sunflower_card, (55, 75))
peashooter_card = pygame.transform.scale(peashooter_card, (55, 75))
pygame.mixer.music.load("Grasswalk.mp3")
pygame.mixer.music.play(-1)

sunflower_images = [pygame.image.load(f"SunFlower_{i}.png").convert_alpha() for i in range(18)]
peashooter_images = [pygame.image.load(f"Peashooter_{i}.png").convert_alpha() for i in range(13)]
sun_images = [pygame.image.load(f"Sun_{i}.png") for i in range(22)]
zombie_images = [pygame.image.load(f"Zombie_{i}.png").convert_alpha() for i in range(22)]
zombie_images = [pygame.transform.scale(zombie, (zombie.get_width() // 2, zombie.get_height() // 2)) for zombie in zombie_images]
bullet_image = pygame.image.load("PeaNormal_0.png").convert_alpha()

plant_positions = []
card_positions = {
    (85, 15): 'sunflower',
    (145, 15): 'peashooter'
}

top_left_x, top_left_y = 260, 100  
bottom_right_x, bottom_right_y = 1006, 556 

grid_rows = 5  
grid_columns = 9  
cell_width = (bottom_right_x - top_left_x) // grid_columns
cell_height = (bottom_right_y - top_left_y) // grid_rows
plants_grid = [[None for _ in range(grid_columns)] for _ in range(grid_rows)]

last_bullet_time_peashooter = {}
bullets_to_remove = []
zombie_hit_count = {}

class Bullet:
    def __init__(self, x, y, direction_x, direction_y):
        self.x = x
        self.y = y
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.speed = 5  
        self.exploded = False  

    def update(self):
        self.x += self.direction_x * self.speed
        self.y += self.direction_y * self.speed

    def explode(self):
        self.exploded = True

    def draw(self, surface):
        if not self.exploded:
            surface.blit(bullet_image, (self.x, self.y))

class Sun:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0

    def update(self):
        pass  

    def draw(self, surface):
        surface.blit(sun_images[self.frame], (self.x, self.y))

sun_list = []  
last_sun_time = pygame.time.get_ticks()  

def decrease_sun_count(amount):
    global sun_count
    sun_count -= amount

def increase_sun_count(amount):
    global sun_count
    sun_count += amount

def generate_sun():
    random_x = random.randint(100, 1100)
    random_y = random.randint(100, 500)
    return Sun(random_x, random_y)

def convert_mouse_pos_to_grid(mx, my):
    x = (mx - top_left_x) // cell_width
    y = (my - top_left_y) // cell_height
    if 0 <= x < grid_columns and 0 <= y < grid_rows:
        return x, y
    else:
        return None, None  

def place_plant(plants_grid, x, y, selected_plant):
    if x is not None and y is not None:
        if plants_grid[y][x] is None:
            plants_grid[y][x] = selected_plant
            return True
    return False

def select_plant(mouse_pos):
    for card_pos, plant in card_positions.items():
        card_rect = pygame.Rect(card_pos[0], card_pos[1], sunflower_card.get_width(), sunflower_card.get_height())
        if card_rect.collidepoint(mouse_pos):
            return plant
    return None

class Zombie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 0.5

    def move(self):
        self.x -= self.step_size * self.speed  # Изменяем позицию по оси X


running = True
selected_plant = None
current_frame_sunflower = 0
current_frame_peashooter = 0
current_frame_zombie = 0
current_frame_zombie_attack = 0
zombie_eat_start_time = {}
sun_count = 1000
clock = pygame.time.Clock()  

zombies = []  
bullets = []  
peashooter_bullet_interval = 1400  
last_spawn_time = pygame.time.get_ticks()  

bullet_collision_width = 10
bullet_collision_height = 10

zombie_collision_width = 40
zombie_collision_height = 40

spawn_positions = [
    (1000, 70), 
    (1000, 170),  
    (1000, 200),  
    (1000, 300),  
    (1000, 400)   
]

plant_costs = {
    'sunflower': 50,
    'peashooter': 100
}

while running:
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for sun in sun_list:
                if pygame.Rect(sun.x, sun.y, sun_images[0].get_width(), sun_images[0].get_height()).collidepoint(mouse_pos):
                    increase_sun_count(25)  
                    sun_list.remove(sun)  
            if selected_plant is None:
                selected_plant = select_plant(mouse_pos)
            else:
                grid_pos = convert_mouse_pos_to_grid(*mouse_pos)
                if sun_count >= plant_costs[selected_plant]:  
                    if place_plant(plants_grid, *grid_pos, selected_plant):
                        plant_positions.append((top_left_x + grid_pos[0] * cell_width, top_left_y + grid_pos[1] * cell_height, selected_plant))
                        decrease_sun_count(plant_costs[selected_plant])  
                        selected_plant = None

    # Проверка столкновения пули с зомби и их удаление
    for bullet in bullets[:]:
        bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet_collision_width, bullet_collision_height)
        for zombie in zombies[:]:
            if isinstance(zombie, list):
                zombie_rect = pygame.Rect(zombie[0], zombie[1], zombie_collision_width, zombie_collision_height)
            else:
                zombie_rect = pygame.Rect(zombie.x, zombie.y, zombie_collision_width, zombie_collision_height)
            if bullet_rect.colliderect(zombie_rect):
                bullets.remove(bullet)  # Удаляем пулю из списка
                zombies.remove(zombie)  # Удаляем зомби из списка
                break  # Прерываем цикл для этой пули, чтобы она не попала в других зомби


    for zombie in list(zombie_hit_count.keys()):
        if zombie_hit_count[zombie] >= 2:
            zombies.remove(zombie)  
            del zombie_hit_count[zombie]  

    for plant_pos in plant_positions:
        x, y, plant_type = plant_pos
        if plant_type == 'sunflower':
            if current_time - last_sun_time > 5000:  
                sun_list.append(Sun(x + random.randint(-50, 50), y + random.randint(-50, 50)))  
                last_sun_time = current_time 

    current_frame_sunflower = (current_frame_sunflower + 1) % len(sunflower_images)
    current_frame_peashooter = (current_frame_peashooter + 1) % len(peashooter_images)
    current_frame_zombie = (current_frame_zombie + 1) % len(zombie_images)
    for sun in sun_list:
        sun.frame = (sun.frame + 1) % len(sun_images)

    window.fill((255, 255, 255))
    window.blit(image, (0, 0))
    window.blit(chooser_background, (10, 10))
    window.blit(sunflower_card, (85, 15))
    window.blit(peashooter_card, (145, 15))

    for sun in sun_list:
        sun.draw(window)

    if current_time - last_sun_time > 6000:  
        sun_list.append(generate_sun())  
        last_sun_time = current_time  

    for bullet in bullets:
        bullet.update()

    for bullet in bullets[:]:
        bullet_center = (bullet.x + bullet_image.get_width() // 2, bullet.y + bullet_image.get_height())  
        bullet_radius = bullet_image.get_width() // 2  
        for zombie in zombies[:]:
            zombie_center = (zombie[0] + zombie_collision_width // 2, zombie[1] + zombie_collision_height // 2)  
            zombie_radius = zombie_collision_width // 2  
            distance = ((bullet_center[0] - zombie_center[0]) ** 2 + (bullet_center[1] - zombie_center[1]) ** 2) ** 0.5  
            if distance < bullet_radius + zombie_radius:  
                bullet.explode()  
                bullets_to_remove.append(bullet)  
                zombie_hit_count[tuple(zombie)] = zombie_hit_count.get(tuple(zombie), 0) + 1  
                break

    if current_time - last_spawn_time > 5000:  
        spawn_pos = random.choice(spawn_positions)  
        zombies.append([spawn_pos[0], spawn_pos[1]])  
        last_spawn_time = current_time  

    for plant_pos in plant_positions:
        x, y, plant_type = plant_pos
        if plant_type == 'sunflower':
            for zombie in zombies:
                zombie_rect = pygame.Rect(zombie[0], zombie[1], zombie_collision_width, zombie_collision_height)
                plant_rect = pygame.Rect(x, y, cell_width, cell_height)
                if zombie_rect.colliderect(plant_rect):
                    break
            else:
                for zombie in zombies:
                    zombie[0] -= 1
        elif plant_type == 'peashooter':
            for zombie in zombies:
                zombie_rect = pygame.Rect(zombie[0], zombie[1], zombie_collision_width, zombie_collision_height)
                plant_rect = pygame.Rect(x, y, cell_width, cell_height)
                if zombie_rect.colliderect(plant_rect):
                # Revert zombie to normal
                    window.blit(zombie_images[current_frame_zombie], (zombie[0], zombie[1]))
                    break
                else:
                # Move zombie
                    zombie[0] -= 1

# Move peashooters
    for plant_pos in plant_positions:
        x, y, plant_type = plant_pos
        if plant_type == 'peashooter':
            if current_time - last_bullet_time_peashooter.get((x, y), 0) > peashooter_bullet_interval:
                bullets.append(Bullet(x + 50, y, 1, 0))
                last_bullet_time_peashooter[(x, y)] = current_time

# Move zombies
    for zombie in zombies:
        zombie[0] -= 1



    for bullet in bullets_to_remove:
        if bullet in bullets:  # Check if the bullet is in the bullets list
            bullets.remove(bullet)  # Remove the bullet
        if bullet in zombies:  # Check if the bullet is a zombie
            zombies.remove(bullet)  # Remove the zombie hit by the bullet
    bullets_to_remove.clear()


    for bullet in bullets:
        bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet_collision_width, bullet_collision_height)
        for zombie in zombies:
            if isinstance(zombie, list):
                zombie_rect = pygame.Rect(zombie[0], zombie[1], zombie_collision_width, zombie_collision_height)
            else:
                zombie_rect = pygame.Rect(zombie.x, zombie.y, zombie_collision_width, zombie_collision_height)
                if bullet_rect.colliderect(zombie_rect):
                    bullets.remove(bullet)
                    zombies.remove(zombie)
                    break

    for pos in plant_positions:
        if pos[2] == 'sunflower':
            window.blit(sunflower_images[current_frame_sunflower], (pos[0], pos[1]))
        elif pos[2] == 'peashooter':
            window.blit(peashooter_images[current_frame_peashooter], (pos[0], pos[1]))

    for zombie in zombies:
        window.blit(zombie_images[current_frame_zombie], (zombie[0], zombie[1]))

    for bullet in bullets:
        bullet.draw(window)

    font = pygame.font.Font('SeriesOrbit.TTF', 20)
    text = font.render(f"{sun_count}", 1, (10, 10, 10))
    window.blit(text, (35, 73))

    pygame.display.update()

    clock.tick(22)  

pygame.quit()