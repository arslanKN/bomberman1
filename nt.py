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
DOOR_SPAWN_CHANCE = 0.1
ANIMATION_SPEED = 0.2  # Скорость смены кадров анимации
game = None


def load_animation(folder, prefix, count):
    images = []
    for i in range(1, count + 1):
        image = pygame.image.load(f"data/{prefix}{i}.png").convert_alpha()
        images.append(pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE)))
    return images


# Загрузка анимаций
player_animations = {
    'down': load_animation('player', 'down_', 3),
    'up': load_animation('player', 'up_', 3),
    'left': load_animation('player', 'left_', 3),
    'right': load_animation('player', 'right_', 3),
    'idle': load_animation('player', 'idle_', 2)
}

monster_animations = {
    'move': load_animation('monster', 'move_', 4),
    'idle': load_animation('monster', 'idle_', 2)
}

explosion_animation = load_animation('explosion', 'explosion_', 5)
door_animation = load_animation('door', 'door_', 2)

# Загрузка статичных изображений
wall_img = pygame.transform.scale(pygame.image.load("data/wall.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
brick_img = pygame.transform.scale(pygame.image.load("data/brick.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
bomb_img = pygame.transform.scale(pygame.image.load("data/bomb.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
door_img = pygame.transform.scale(pygame.image.load("data/door.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))
explosion_img = pygame.transform.scale(pygame.image.load("data/explosion.png").convert_alpha(), (TILE_SIZE, TILE_SIZE))


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = door_img
        self.rect = self.image.get_rect(topleft=(x, y))


class Game:
    def __init__(self):
        self.level = 1
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
        self.spawn_monsters(3 + self.level)
        self.player = Player()
        self.all_sprites.add(self.player)
        self.level += 1

    def create_map(self):
        level = [
            "WWWWWWWWWWWWWW",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "W W W W W W W W",
            "W             W",
            "WWWWWWWWWWWWWW",
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
                        if not self.door_spawned and random.random() < DOOR_SPAWN_CHANCE:
                            door = Door(*pos)
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
                        not any(s.rect.collidepoint(x, y) for s in self.bricks):
                    monster = Monster(x, y)
                    self.monsters.add(monster)
                    self.all_sprites.add(monster)
                    break


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, animations, initial_state='idle'):
        super().__init__()
        self.animations = animations
        self.state = initial_state
        self.frame_index = 0
        self.animation_speed = ANIMATION_SPEED
        self.image = self.animations[self.state][self.frame_index]
        self.rect = self.image.get_rect()

    def animate(self, state=None):
        if state and state != self.state:
            self.state = state
            self.frame_index = 0

        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.animations[self.state]):
            self.frame_index = 0

        self.image = self.animations[self.state][int(self.frame_index)]


class Player(AnimatedSprite):
    def __init__(self):
        super().__init__(player_animations)
        self.rect.topleft = (TILE_SIZE, TILE_SIZE)
        self.speed = 5
        self.alive = True
        self.direction = 'down'
        self.last_direction = 'down'
        self.moving = False

    def update(self, keys):
        if self.alive:
            old_rect = self.rect.copy()
            self.moving = False
            new_direction = self.last_direction

            if keys[pygame.K_UP]:
                self.rect.y -= self.speed
                new_direction = 'up'
                self.moving = True
            if keys[pygame.K_DOWN]:
                self.rect.y += self.speed
                new_direction = 'down'
                self.moving = True
            if keys[pygame.K_LEFT]:
                self.rect.x -= self.speed
                new_direction = 'left'
                self.moving = True
            if keys[pygame.K_RIGHT]:
                self.rect.x += self.speed
                new_direction = 'right'
                self.moving = True

            if pygame.sprite.spritecollideany(self, game.walls) or pygame.sprite.spritecollideany(self, game.bricks):
                self.rect = old_rect
                self.moving = False

            if new_direction != self.direction:
                self.direction = new_direction
                self.last_direction = new_direction

            # Обновление анимации
            state = self.direction if self.moving else 'idle'
            self.animate(state)


class Monster(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(monster_animations)
        self.rect.topleft = (x, y)
        self.speed = 2
        self.direction = random.choice(["up", "down", "left", "right"])
        self.change_dir_timer = 0
        self.moving = False

    def update(self):
        self.change_dir_timer += 1 / FPS
        if self.change_dir_timer > 2:
            self.direction = random.choice(["up", "down", "left", "right"])
            self.change_dir_timer = 0

        old_pos = self.rect.copy()
        self.moving = True

        if self.direction == "up": self.rect.y -= self.speed
        if self.direction == "down": self.rect.y += self.speed
        if self.direction == "left": self.rect.x -= self.speed
        if self.direction == "right": self.rect.x += self.speed

        if pygame.sprite.spritecollideany(self, game.walls) or pygame.sprite.spritecollideany(self, game.bricks):
            self.rect = old_pos
            self.direction = random.choice(["up", "down", "left", "right"])
            self.moving = False

        # Обновление анимации
        state = 'move' if self.moving else 'idle'
        self.animate(state)


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


class ExplosionCenter(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__({'explode': explosion_animation}, 'explode')
        self.rect.topleft = (x, y)
        self.timer = 0.8
        game.all_sprites.add(self)
        game.explosions.add(self)

    def update(self):
        super().animate()
        self.timer -= 1 / FPS
        if self.timer <= 0:
            self.kill()


class ExplosionPart(AnimatedSprite):
    def __init__(self, x, y, direction):
        super().__init__({'explode': explosion_animation}, 'explode')
        self.image = pygame.transform.rotate(self.image, 90 if direction[0] else 0)
        self.rect.topleft = (x, y)
        self.timer = 0.8
        game.all_sprites.add(self)
        game.explosions.add(self)

    def update(self):
        super().update()
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


# Инициализация игры
if __name__ == "__main__":
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

        if pygame.sprite.spritecollideany(game.player, game.doors):
            game.new_level()
            continue
            # Проверка столкновений
        if pygame.sprite.spritecollideany(game.player, game.monsters) or \
                pygame.sprite.spritecollideany(game.player, game.explosions):
            game.player.alive = False

        # Проверка перехода на новый уровень
        if pygame.sprite.spritecollideany(game.player, game.doors):
            game.new_level()

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

        pygame.display.flip()

    pygame.quit()
