import pygame
import os
import time
import random

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
TILE_SIZE = 40
FPS = 30
EXPLOSION_RANGE = 3
BACKGROUND_COLOR = (34, 139, 34)
RED = (255, 0, 0)
LEVEL_COLOR = (255, 255, 255)
DOOR_SPAWN_CHANCE = 0.1  # 10% шанс спавна двери

# Инициализация экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bomberman")


def load_image(name):
    image = pygame.image.load(os.path.join("data", name)).convert_alpha()
    return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))


# Загрузка изображений
player_img = load_image("player.png")
wall_img = load_image("wall.png")
brick_img = load_image("brick.png")
bomb_img = load_image("bomb.png")
explosion_img = load_image("explosion.png")
monster_img = load_image("monster.png")
door_img = load_image("door.png")


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = door_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.active = False  # Начальное состояние - неактивна

    def update(self):
        if self.active:
            self.image.set_alpha(255)  # Полная видимость
        else:
            self.image.set_alpha(128)


class Game:
    def __init__(self):
        self.level = 0
        self.door_spawned = False
        self.player = None
        self.init_groups()

    def init_groups(self):
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.bricks = pygame.sprite.Group()
        self.monsters = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()

    def new_level(self):
        self.init_groups()
        self.door_spawned = False
        self.create_map()
        self.spawn_monsters(3 + self.level * 2)
        self.player = Player()
        self.all_sprites.add(self.player)
        self.level += 1

    def create_map(self):
        level = [
            "WWWWWWWWWWWWWWW",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "WWWWWWWWWWWWWWW",
        ]

        for y, row in enumerate(level):
            for x, tile in enumerate(row):
                pos = (x * TILE_SIZE, y * TILE_SIZE)
                if tile == "W":
                    wall = pygame.sprite.Sprite()
                    wall.image = wall_img
                    wall.rect = wall.image.get_rect(topleft=pos)
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif tile == " ":
                    if random.random() < 0.4 and (x, y) not in [(1, 1), (2, 1), (1, 2)]:
                        # Всегда спавним дверь, но делаем её неактивной сначала
                        if not self.door_spawned and random.random() < DOOR_SPAWN_CHANCE:
                            door = Door(*pos)
                            door.active = False  # Добавляем флаг активности
                            self.doors.add(door)
                            self.all_sprites.add(door)
                            self.door_spawned = True
                        else:
                            brick = pygame.sprite.Sprite()
                            brick.image = brick_img
                            brick.rect = brick.image.get_rect(topleft=pos)
                            self.bricks.add(brick)
                            self.all_sprites.add(brick)

    def spawn_monsters(self, count):
        for _ in range(count):
            while True:
                x = random.randint(1, 12) * TILE_SIZE
                y = random.randint(1, 8) * TILE_SIZE
                if not any(s.rect.collidepoint(x, y) for s in self.walls) and \
                        not any(s.rect.collidepoint(x, y) for s in self.bricks) and \
                        (x, y) not in [(1, 1), (2, 1), (1, 2)]:
                    monster = Monster(x, y)
                    self.monsters.add(monster)
                    self.all_sprites.add(monster)
                    break

    def all_monsters_dead(self):
        return len(self.monsters) == 0

    def update_door_status(self):
        for door in self.doors:
            door.active = self.all_monsters_dead()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect(topleft=(TILE_SIZE, TILE_SIZE))
        self.speed = 5
        self.alive = True

    def update(self, keys):
        if self.alive:
            old_rect = self.rect.copy()
            if keys[pygame.K_UP]: self.rect.y -= self.speed
            if keys[pygame.K_DOWN]: self.rect.y += self.speed
            if keys[pygame.K_LEFT]: self.rect.x -= self.speed
            if keys[pygame.K_RIGHT]: self.rect.x += self.speed

            if pygame.sprite.spritecollideany(self, game.walls) or pygame.sprite.spritecollideany(self, game.bricks):
                self.rect = old_rect


class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = bomb_img
        grid_x = (x // TILE_SIZE) * TILE_SIZE
        grid_y = (y // TILE_SIZE) * TILE_SIZE
        self.rect = self.image.get_rect(topleft=(grid_x, grid_y))
        self.timer = 3
        self.range = EXPLOSION_RANGE
        game.all_sprites.add(self)
        game.bombs.add(self)

    def update(self):
        self.timer -= 1 / FPS
        if self.timer <= 0:
            self.explode()

    def explode(self):
        ExplosionCenter(self.rect.x, self.rect.y)

        for direction in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            brick_destroyed = False
            for i in range(1, self.range + 1):
                x = self.rect.x + direction[0] * i * TILE_SIZE
                y = self.rect.y + direction[1] * i * TILE_SIZE

                if any(wall.rect.collidepoint(x, y) for wall in game.walls):
                    break

                for brick in game.bricks:
                    if brick.rect.collidepoint(x, y):
                        brick.kill()
                        ExplosionPart(x, y, direction)
                        brick_destroyed = True
                        break

                if brick_destroyed:
                    break

                if i == self.range:
                    ExplosionEnd(x, y, direction)
                else:
                    ExplosionPart(x, y, direction)

        self.kill()


class ExplosionCenter(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = explosion_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.timer = 0.8
        game.all_sprites.add(self)
        game.explosions.add(self)

    def update(self):
        self.timer -= 1 / FPS
        if self.timer <= 0:
            self.kill()


class ExplosionPart(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.transform.rotate(explosion_img, 90 if direction[0] else 0)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.timer = 0.8
        game.all_sprites.add(self)
        game.explosions.add(self)

    def update(self):
        self.timer -= 1 / FPS
        if self.timer <= 0:
            self.kill()


class ExplosionEnd(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        angle = 0
        if direction == (0, -1):
            angle = 0
        elif direction == (0, 1):
            angle = 180
        elif direction == (-1, 0):
            angle = 90
        elif direction == (1, 0):
            angle = 270

        self.image = pygame.transform.rotate(explosion_img, angle)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.timer = 0.8
        game.all_sprites.add(self)
        game.explosions.add(self)

    def update(self):
        self.timer -= 1 / FPS
        if self.timer <= 0:
            self.kill()


class Monster(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = monster_img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
        self.direction = random.choice(["up", "down", "left", "right"])
        self.change_dir_timer = 0

    def update(self):
        self.change_dir_timer += 1 / FPS
        if self.change_dir_timer > 2:
            self.direction = random.choice(["up", "down", "left", "right"])
            self.change_dir_timer = 0

        old_pos = self.rect.copy()
        if self.direction == "up": self.rect.y -= self.speed
        if self.direction == "down": self.rect.y += self.speed
        if self.direction == "left": self.rect.x -= self.speed
        if self.direction == "right": self.rect.x += self.speed

        # Проверка столкновений со стенами, кирпичами и бомбами
        if (pygame.sprite.spritecollideany(self, game.walls) or
            pygame.sprite.spritecollideany(self, game.bricks) or
            pygame.sprite.spritecollideany(self, game.bombs)):
            self.rect = old_pos
            self.direction = random.choice(["up", "down", "left", "right"])


# Инициализация игры
game = Game()
game.new_level()

# Основной цикл
clock = pygame.time.Clock()
running = True

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            grid_x = (game.player.rect.centerx // TILE_SIZE) * TILE_SIZE
            grid_y = (game.player.rect.centery // TILE_SIZE) * TILE_SIZE
            if not any(bomb.rect.topleft == (grid_x, grid_y) for bomb in game.bombs):
                Bomb(grid_x, grid_y)

    # Обновление спрайтов
    keys = pygame.key.get_pressed()
    game.player.update(keys)
    game.bombs.update()
    game.monsters.update()
    game.explosions.update()

    # Проверка столкновений
    if pygame.sprite.spritecollideany(game.player, game.monsters) or \
            pygame.sprite.spritecollideany(game.player, game.explosions):
        game.player.alive = False



    # Удаление мертвых монстров
    pygame.sprite.groupcollide(game.monsters, game.explosions, True, False)

    # Отрисовка
    screen.fill(BACKGROUND_COLOR)
    game.all_sprites.draw(screen)

    # Отображение уровня
    font = pygame.font.Font(None, 36)
    level_text = font.render(f'Level: {game.level}', True, LEVEL_COLOR)
    screen.blit(level_text, (10, 10))

    if not game.player.alive:
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', True, RED)
        screen.blit(text, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 50))
        pygame.display.flip()
        time.sleep(2)
        running = False


    game.update_door_status()
    if pygame.sprite.spritecollideany(game.player, game.doors):
        for door in game.doors:
            if door.active:
                game.new_level()
                break

    pygame.display.flip()