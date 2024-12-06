import pygame
import sys
import time
import os
import random

# Инициализация Pygame
pygame.init()

pygame.mixer.init()
rain_sound = pygame.mixer.Sound("rain_sound.wav")
thunder_sound = pygame.mixer.Sound("thunder_sound.wav")
snow_sound = pygame.mixer.Sound("wind_sound.wav")

player_step_sound = pygame.mixer.Sound("PlayerFootstep.wav")
enemy_step_sound = pygame.mixer.Sound("enemyFootstep.wav")

jump_sound = pygame.mixer.Sound("jump.wav")
collectible_sound = pygame.mixer.Sound("collectible.wav")

# Параметры окна
WIDTH, HEIGHT = 1200, 800
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Создаем окно игры
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Платформер с анимацией и камерой")

# Глобальные переменные
GRAVITY = 0.8
PLAYER_SPEED = 5
PLAYER_JUMP = 20
ENEMY_SPEED = 3
INITIAL_LIVES = 3

FONT = pygame.font.SysFont("Arial",24)
SAVE_FILE = "savefile.txt"


class Particle(pygame.sprite.Sprite):
    def __init__(self,x,y,speed,size,color):
        super().__init__()
        self.image = pygame.Surface((size,size))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.speed = speed
        self.size = size
    def update(self):
        self.rect.y += self.speed
        if self.rect.y > pygame.display.get_surface().get_height():
            self.rect.y = -self.size
            self.rect.x = random.randint(0,
                            pygame.display.get_surface().get_width())
            
class Weather(pygame.sprite.Group):
    def __init__(self,weather_type="rain",particle_count = 100):
        super().__init__()
        self.weather_type = weather_type
        self.particles = []
        self.particle_count = particle_count
        

        if random.randint(1,100) > 95:
            thunder_sound.play()

        if self.weather_type == "rain":
            self.create_rain()

        if self.weather_type == "snow":
            self.create_snow()

    def create_rain(self):
        for _ in range(self.particle_count):
            x = random.randint(0,random.randint(0,
                            pygame.display.get_surface().get_width()))
            y = random.randint(0,random.randint(0,
                            pygame.display.get_surface().get_height()))
            speed = random.randint(5,10)
            color = (0,0,255)
            size = random.randint(2,5)
            particle = Particle(x,y,speed,size,color)
            self.add(particle)
    def create_snow(self):
        for _ in range(self.particle_count):
            x = random.randint(0,random.randint(0,
                            pygame.display.get_surface().get_width()))
            y = random.randint(0,random.randint(0,
                            pygame.display.get_surface().get_height()))
            speed = random.randint(1,4)
            color = (255,255,255)
            size = random.randint(3,7)
            particle = Particle(x,y,speed,size,color)
            self.add(particle)
    def update(self):
        for particle in self.sprites():
            particle.update()

class WeatherManager:
    def __init__(self,change_interval = 10):
        self.current_weather = Weather(weather_type="rain")
        self.change_interval = change_interval
        self.last_change_time = time.time()

        self.current_sound = rain_sound
        self.play_sound()

    def update_weather(self):
        current_time = time.time()

        if current_time - self.last_change_time >= self.change_interval:
            self.last_change_time = current_time

            if self.current_weather.weather_type == "rain":
                self.current_weather = Weather(weather_type="snow")
                self.switch_sound(snow_sound)
            else:
                self.current_weather = Weather(weather_type="rain")
                self.switch_sound(rain_sound)
    def play_sound(self):
        self.current_sound.play(loops= -1)
    
    def switch_sound(self,new_sound):
        self.current_sound.stop()
        self.current_sound = new_sound
        self.play_sound()
    def draw(self,screen):
        self.current_weather.update()
        self.current_weather.draw(screen)



# Класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_right = [
            pygame.image.load(f'player-anim-{i}.png').convert_alpha()
            for i in range(1, 12)
        ]
        self.image_left = [
            pygame.transform.flip(frame, True, False) for frame in self.image_right
        ]
        self.current_image = 0
        self.image = self.image_right[self.current_image]
        self.rect = self.image.get_rect()
        self.rect.center = (400, 300)
        self.vel_y = 0  # Вертикальная скорость
        self.direction = 'right'
        self.score = 0
        self.lives = INITIAL_LIVES
        self.animation_time = 100
        self.last_update = pygame.time.get_ticks()
        self.step_sound_timer = 0
        # self.power = 100

    def update(self, platforms):
        # Обработка нажатий клавиш
        keys = pygame.key.get_pressed()


        moving = False
        if keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
            self.direction = 'left'
            
        if keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED
            self.direction = 'right'
            moving = True
        # Прыжок
        
        if keys[pygame.K_SPACE] and self.on_ground(platforms):
            self.vel_y = -PLAYER_JUMP
            jump_sound.play()
        if moving:
            self.animate()
            self.play_step_sound()
        # Применение гравитации
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # Ограничение выхода за экран
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

        # Проверка на платформы
        self.collide_with_platforms(platforms)

    def play_step_sound(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.step_sound_timer >= 200:
            player_step_sound.play()
            self.step_sound_timer = current_time
    
    def animate(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= self.animation_time:
            self.last_update = current_time
            self.current_image = (self.current_image + 1) % len(self.image_right)
            if self.direction == "right":
                self.image = self.image_right[self.current_image]
            else:
                self.image = self.image_left[self.current_image]

    def on_ground(self, platforms):
        self.rect.y += 1
        on_ground = pygame.sprite.spritecollideany(self, platforms)
        self.rect.y -= 1
        return on_ground

    def collide_with_platforms(self, platforms):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits:
            if self.vel_y > 0:  # Падение вниз
                self.rect.bottom = hits[0].rect.top
                self.vel_y = 0

# Класс платформы
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y,image):
        super().__init__()
        self.image_copy = pygame.image.load(image).convert_alpha()
        self.image = self.image_copy

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y,image):
        super().__init__()
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Level:
    def __init__(self):
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.create_level()
        self.time_limit = 30
        self.start_time = time.time()

    def create_level(self):
        """Создание платформ для уровня"""
        raise NotImplementedError("Метод должен быть переопределен")

    def reset_player_position(self, player):
        player.rect.x = 110
        player.rect.y = 300
    def time_remaining(self):
        elapsed = time.time() - self.start_time
        return max(0,self.time_limit - int(elapsed))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y,platform):
        super().__init__()
        self.images = [pygame.image.load("goblin1.png").convert_alpha(),
        pygame.image.load("goblin2.png").convert_alpha()
        ]

        self.current_image = 0
        self.image = self.images [self.current_image]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = ENEMY_SPEED
        self.direction = 1
        self.animation_time = 200
        self.last_update = pygame.time.get_ticks()
        self.platform = platform

        self.step_sound_timer = 0

    def update(self,platforms):
        self.rect.x += self.speed * self.direction

        if (self.rect.left <= self.platform.rect.left or
            self.rect.right >= self.platform.rect.right):
            self.direction *= -1

        hits = pygame.sprite.spritecollide(self,platforms,False)
        if hits or self.rect.left < 0 or self.rect.right > WIDTH:
            self.direction *= -1

        self.play_step_sound()
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= self.animation_time:
            self.last_update = current_time
            self.current_image = (self.current_image + 1) % len(self.images)
            self.image = self.images[self.current_image]
        if self.direction != 1:
            self.image = pygame.image.load("goblin1.png").convert_alpha()
        else:
            self.image = pygame.transform.flip(
                pygame.image.load("goblin1.png").convert_alpha(),
                True,False)

    def play_step_sound(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.step_sound_timer >= 200:
            enemy_step_sound.play()
            self.step_sound_timer = current_time
            
def save_progress(level_index,player_score) :
    with open(SAVE_FILE,"w") as file:
        file.write(f"{level_index},{player_score}")

def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE,"r") as file:
            level_index,player_score = map(int,file.readline().split(','))
            return level_index,player_score
    return 0,0

class Level1(Level):
    
    def create_level(self):

        ground = Platform(0, HEIGHT - 40,"goodly-2x 1.png")  # Основная платформа
        platform1 = Platform(300, 600,"generic_platformer_tiles 2.png" )
        platform2 = Platform(600, 400,"generic_platformer_tiles 2.png" )
        platform3 = Platform(900, 300,"generic_platformer_tiles 1.png")

        self.platforms.add(ground, platform1, platform2, platform3)

        enemy1 = Enemy(400, 548, platform1)
        enemy2 = Enemy(600, 400, platform2)
        self.enemies.add(enemy1, enemy2)

        collectible1 = Collectible(350,570,"collectible1.png")
        collectible2 = Collectible(750,370,"collectible2.png")
        self.collectibles.add(collectible1,collectible2)


class Level2(Level):
    def create_level(self):
        ground = Platform(0, HEIGHT - 40,"goodly-2x 2.png")  # Основная платформа
        platform1 = Platform(300, 650,"generic_platformer_tiles 2.png" )
        platform2 = Platform(700, 450,"generic_platformer_tiles 2.png" )
        platform3 = Platform(1000, 250,"generic_platformer_tiles 1.png")
        platform4 = Platform(1200, 500,"generic_platformer_tiles 1.png")

        self.platforms.add(ground, platform1, platform2, platform3)


        enemy1 = Enemy(300, 600, platform1)
        enemy2 = Enemy(600, 400, platform2)
        self.enemies.add(enemy1, enemy2)


        collectible1 = Collectible(350,620,"collectible3.png")
        collectible2 = Collectible(750,420,"collectible1.png")
        self.collectibles.add(collectible1,collectible2)

class Level3(Level):
    def create_level(self):
        ground = Platform(0, HEIGHT - 40,"goodly-2x 3.png")  # Основная платформа
        platform1 = Platform(300, 650,"generic_platformer_tiles 2.png" )
        platform2 = Platform(700, 450,"generic_platformer_tiles 2.png" )
        platform3 = Platform(1000, 250,"generic_platformer_tiles 1.png")
        platform4 = Platform(1200, 500,"generic_platformer_tiles 1.png")

        self.platforms.add(ground, platform1, platform2, platform3)


        enemy1 = Enemy(300, 600, platform1)
        enemy2 = Enemy(600, 400, platform2)
        self.enemies.add(enemy1, enemy2)

        collectible1 = Collectible(350,620,"collectible2.png")
        collectible2 = Collectible(750,420,"collectible3.png")
        self.collectibles.add(collectible1,collectible2)

# Класс камеры
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + WIDTH // 2
        y = -target.rect.centery + HEIGHT // 2

        # Ограничение камеры в пределах уровня
        x = min(0, x)  # Левый край
        y = min(0, y)  # Верхний край
        x = max(-(self.width - WIDTH), x)  # Правый край
        y = max(-(self.height - HEIGHT), y)  # Нижний край

        self.camera = pygame.Rect(x, y, self.width, self.height)

def draw_ui(player,level_index):
    score_text = FONT.render(f"Score: {player.score}",True,GREEN)
    lives_text = FONT.render(f"Lives: {player.lives}",True,GREEN)
    level_text = FONT.render(f"Level: {level_index + 1}",True,GREEN)

    screen.blit(score_text,(10,100))
    screen.blit(lives_text,(10,40))
    screen.blit(level_text,(10,70))

def draw_pause_menu():
    pause_text = FONT.render("PAUSED - Press 'p' to Resume",True,GREEN)
    screen.blit(pause_text,(WIDTH // 2 - pause_text.get_width() // 2,HEIGHT // 2))

def draw_main_menu():
    screen.fill(WHITE)
    title_text = FONT.render("Платформер с анимацией и каммерой",True,BLUE)
    start_text = FONT.render("Нажмите Q для начала игры",True,GREEN)
    screen.blit(title_text,(WIDTH // 2 - title_text.get_width() // 2 , HEIGHT // 2 - 40))
    screen.blit(start_text,(WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
def draw_game_over_menu():
    screen.fill(WHITE)
    game_over_text = FONT.render("Игра окончена",True,RED)
    retry_text = FONT.render("Нажмите R для рестрата",True,GREEN)
    screen.blit(game_over_text,(WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 40))
    screen.blit(retry_text,(WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2))

# Основная игровая функция
def main():
    state = "main_menu"
    # weather = Weather(weather_type="rain")#snow
    weathermanager = WeatherManager(change_interval=3)


    # Создание игрока
    player = Player()

    # Группы спрайтов
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)

    # Создаем уровни
    levels = [Level1(), Level2(), Level3()]
    current_level_index,player.score = load_progress()
    current_level = levels[current_level_index]

    all_sprites.add(current_level.platforms,current_level.enemies,current_level.collectibles)

    

    # Основной игровой цикл
    clock = pygame.time.Clock()
    running = True
    paused = False
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_progress(current_level_index,player.score)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and state == "game":
                    paused = not paused
                elif event.key == pygame.K_q and state == "main_menu":
                    state = "game"
                elif event.key == pygame.K_r and state == "game_over":
                    state = "main_menu"
                    player.lives = INITIAL_LIVES
                    current_level_index = 0
                    player.score = 0
                    current_level = levels[current_level_index]
                    player.rect.center = (400,300)
                    all_sprites.empty()
                    all_sprites.add(player, current_level.platforms, current_level.enemies, current_level.collectibles)
                    
        if state == "main_menu":
            draw_main_menu()
        elif state == "game_over":
            draw_game_over_menu()

        # Обновление игрока и уровня
        elif state == "game" and not paused:
            all_sprites.update(current_level.platforms)
            current_level.enemies.update(current_level.platforms)


            collectible_hit = pygame.sprite.spritecollide(player,current_level.collectibles,True)
            player.score += len(collectible_hit)

            if pygame.sprite.spritecollideany(player,current_level.enemies):
                player.lives -= 1
                if player.lives > 0:
                    current_level.reset_player_position(player)
                else:
                    state = "game_over"
            time_left = current_level.time_remaining()
            if time_left <= 0:
                state = "game_over"

            # Проверка на переход на следующий уровень
            if player.rect.right >= WIDTH - 10:  # Если игрок достигает правого края
                current_level_index += 1
                if current_level_index >= len(levels):
                    print("Игра пройдена!")
                    pygame.quit()
                    sys.exit()
                
                all_sprites.empty()
                all_sprites.add(player)
                current_level = levels[current_level_index]
                current_level.reset_player_position(player)
                all_sprites.add(current_level.platforms)
                all_sprites.add(current_level.enemies)
                save_progress(current_level_index,player.score)

                
            # Отрисовка
            screen.fill(WHITE)
            all_sprites.draw(screen)
            draw_ui(player,current_level_index)
            font = pygame.font.Font(None,36)
            timer_text = font.render(f"Осталось времени: {time_left}",True,RED) 
            screen.blit(timer_text,(10,10))

            if paused:
                draw_pause_menu()
                
            # weather.update()
            # weather.draw(screen)

            weathermanager.update_weather()
            weathermanager.draw(screen)

        

        pygame.display.flip()

        # Ограничение FPS
        clock.tick(FPS)

# Запуск игры
if __name__ == "__main__":
    main()