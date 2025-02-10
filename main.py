import pygame
import os

# Инициализация Pygame
pygame.init()

# Настройки окна
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60

# 16x16
def load_image(name, color_key=None):# 16x16
    fullname = os.path.join("data", name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


# Класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image("player.png")
        self.rect = self.image.get_rect()
        self.rect.center = (0, 0)
        self.speed = 3
        self.frames = []
        self.cur_frame = 0
        self.timer = 3 * FPS

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(self.rect.x, self.rect.y, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))


    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.cut_sheet(self.image, 7, 3)
            self.rect.x -= self.speed
            self.timer -= 1

            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            if self.timer <= 0:
                self.image = self.frames[self.cur_frame]
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

# Класс бомбы
class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image("bomb.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.timer = 3 * FPS  # 3 секунды
        self.frames = []
        self.cur_frame = 0
        self.cut_sheet(self.image, 3, 1)


    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(self.rect.x, self.rect.y, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.timer -= 1
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        if self.timer <= 0:
            self.image = self.frames[self.cur_frame]
        if self.timer <= 0:

            self.explode()

    def explode(self):
        # Создание взрыва
        explosion = Explosion(self.rect.centerx, self.rect.centery)
        all_sprites.add(explosion)
        self.kill()


# Класс взрыва
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image("explosion.png")
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.timer = 0.5 * FPS  # 0.5 секунды

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_image("wall.png")
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
walls = pygame.sprite.Group()


all_sprites = pygame.sprite.Group()

# Основной код игры
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bomberman")
clock = pygame.time.Clock()

# Группы спрайтов
bombs = pygame.sprite.Group()

# Создание игрока
player = Player()
all_sprites.add(player)

# Основной цикл игры
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Создание бомбы
                bomb = Bomb(player.rect.centerx, player.rect.centery)
                all_sprites.add(bomb)
                bombs.add(bomb)

    # Обновление спрайтов
    all_sprites.update()

    # Отрисовка
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
RED = (255, 0, 0)