import pygame, sys, math, random, time
from pygame.locals import *
from pyglet import clock

pygame.init()
pygame.mixer.init()

vec = pygame.math.Vector2  # 2D movement physics
FRIC = -0.1

WIDTH = 1024
HEIGHT = 768
SIZE = (WIDTH, HEIGHT)
FPS = 60
FramePerSec = pygame.time.Clock()
score = open("score.txt","a")

BLACK = (0, 0, 0)
BROWN = (165, 60, 60)
GRAY = (127, 127, 127)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 100, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption("Invaders v.0.1")
background = pygame.image.load("sprites/Background_resized.png")
crosshair = pygame.image.load("sprites/Crosshair_resized.png")
pygame.mouse.set_visible(False)
crosshair_rect = crosshair.get_rect()
death_sound = pygame.mixer.Sound("sounds/explosion.wav")
death_sound.set_volume(0.1)
shot_sound = pygame.mixer.Sound("sounds/laser.wav")
shot_sound.set_volume(0.1)
pygame.mixer.music.load("sounds/music.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.1)

class Player(pygame.sprite.Sprite):
    def __init__(
            self,
            vel=vec(0, 0),
            acc=vec(0, 0),
            speed=0.15,
            score=10,
            life=10,
            last_hit_time=0,
            cooldown=1000,
            last_shot_time=0,
            shoot_cooldown=1000,
            mouse_pos=pygame.mouse.get_pos()
            ):
        super().__init__()
        self.image = pygame.image.load("sprites/Ship_resized.png")
        self.rect = self.image.get_rect()
        self.pos = vec((WIDTH / 2, HEIGHT / 2))  # initial spawn position
        self.vel = vel  # initial velocity
        self.acc = acc  # acceleration
        self.speed = speed
        self.score = score
        self.life = life
        self.last_hit_time = last_hit_time  # Track the last time the player was hit
        self.cooldown = cooldown  # 500 ms cooldown for hits
        self.last_shot_time = last_shot_time  # Track the last time the player shot
        self.shoot_cooldown = shoot_cooldown  # 200 ms cooldown between shots
        self.radius = self.rect.height / 2  # Use half of height for radius (or any other measurement)
        self.bullets = pygame.sprite.Group()
        self.mouse_pos = mouse_pos
    def move_to_cursor(self):
        mouse_pos = pygame.mouse.get_pos()  # Get the mouse cursor position
        direction = vec(mouse_pos[0] - self.pos.x, mouse_pos[1] - self.pos.y)  # Calculate the direction to the cursor
        distance = direction.length()  # Get the distance and normalize the direction vector
        if distance != 0:
            direction.normalize_ip()  # Normalize the vector
            self.acc = direction * self.speed  # Move the player to the cursor
    def move_back(self):
        mouse_pos = pygame.mouse.get_pos()  # Get the mouse cursor position
        direction = vec(mouse_pos[0] - self.pos.x, mouse_pos[1] - self.pos.y)  # Calculate the direction to the cursor
        distance = direction.length()  # Get the distance and normalize the direction vector
        if distance != 0:
            direction.normalize_ip()
            self.acc = direction.rotate(180) * self.speed
    def move_left(self):
        mouse_pos = pygame.mouse.get_pos()  # Get the mouse cursor position
        direction = vec(mouse_pos[0] - self.pos.x, mouse_pos[1] - self.pos.y)  # Calculate the direction to the cursor
        distance = direction.length()  # Get the distance and normalize the direction vector
        if distance != 0:
            direction.normalize_ip()
            self.acc = direction.rotate(270) * self.speed
    def move_right(self):
        mouse_pos = pygame.mouse.get_pos()  # Get the mouse cursor position
        direction = vec(mouse_pos[0] - self.pos.x, mouse_pos[1] - self.pos.y)  # Calculate the direction to the cursor
        distance = direction.length()  # Get the distance and normalize the direction vector
        if distance != 0:
            direction.normalize_ip()
            self.acc = direction.rotate(90) * self.speed
    def slow_down(self):
        if self.vel.length() > 0:  # only when moving
            self.vel += self.acc  # add acceleration to velocity
            self.vel *= (1 + FRIC)
        else: self.vel = vec(0, 0)
    def can_be_hit(self):
        return pygame.time.get_ticks() - self.last_hit_time > self.cooldown
    def shoot(self):
        mouse_pos = pygame.mouse.get_pos()
        angle = math.atan2(mouse_pos[1] - self.pos.y, mouse_pos[0] - self.pos.x)
        bullet = Bullet(self.pos.x, self.pos.y, angle)
        self.bullets.add(bullet)  # Add the bullet to the bullets group
        shot_sound.play()
    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot_time > self.shoot_cooldown
    def get_distance(self, other):
        return self.pos.distance_to(other.pos)
    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_w]: self.move_to_cursor()
        elif pressed_keys[K_s]: self.move_back()
        elif pressed_keys[K_a]: self.move_left()
        elif pressed_keys[K_d]: self.move_right()
        else: self.acc = vec(0, 0)
        self.slow_down()
        self.vel += self.acc  # Add acceleration to velocity
        self.pos += self.vel  # Update position
        if self.pos.x > WIDTH: self.pos.x = 0
        if self.pos.x < 0: self.pos.x = WIDTH
        if self.pos.y > HEIGHT: self.pos.y = 0
        if self.pos.y < 0: self.pos.y = HEIGHT
        self.bullets.update()
        mouse_pos = pygame.mouse.get_pos()  # for rotating player image to cursor
        angle = 270 - math.atan2(mouse_pos[1] - self.pos.y, mouse_pos[0] - self.pos.x) * 180 / math.pi
        rotated_image = pygame.transform.rotate(self.image, angle)
        rotated_rect = rotated_image.get_rect(center=self.pos)
        screen.blit(rotated_image, rotated_rect)
        for bullet in self.bullets:
            screen.blit(bullet.image, bullet.rect)

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, size=2):  # Add a default size parameter
        super().__init__()
        self.size = size  # Set the size of the asteroid
        if self.size == 2: self.image = pygame.image.load("sprites/Asteroid.png")
        elif self.size == 1: self.image = pygame.image.load("sprites/Asteroid_medium.png")
        elif self.size == 0: self.image = pygame.image.load("sprites/Asteroid_resized.png")
        self.original_image = self.image  # Keep a reference to the original image for rotation
        self.rect = self.image.get_rect()
        self.pos = vec(random.randint(self.rect.width, WIDTH - self.rect.width),
                       random.randint(self.rect.height, HEIGHT - self.rect.height))  # Random spawn position
        angle = random.uniform(0, 2 * math.pi)  # Generate a random angle (between 0 and 2π radians)
        self.vel = vec(math.cos(angle), math.sin(angle))  # (cos(angle), sin(angle)) gives direction
        self.vel *= random.uniform(1, 2)
        self.acc = vec(0, 0)
        self.radius = self.rect.height / 2  # Use half of the height (or width) for the radius
        self.moving = True
        self.rotation_angle = 0  # Start at 0 degrees rotation
    def slow_down(self):
        if self.vel.length() > 0:  # Only when moving
            self.vel += self.acc  # Add acceleration to velocity
            self.vel *= (1 + FRIC)
        else:
            self.vel = vec(0, 0)
    def break_up(self, asteroid_group):
        death_sound.play()
        if self.size > 0:
            for _ in range(2):  # Create two new smaller asteroids
                new_asteroid = Asteroid(self.size - 1)  # Pass the new size
                new_asteroid.pos = self.pos.copy()  # Start at the same position as the original
                angle = random.uniform(0, 2 * math.pi)  # Random direction
                new_asteroid.vel = vec(math.cos(angle), math.sin(angle)) * random.uniform(1, 2)
                asteroid_group.add(new_asteroid)
        self.kill()  # Remove the original asteroid
    def get_distance(self, other): return self.pos.distance_to(other.pos)
    def update(self):
        self.vel += self.acc  # Add acceleration to velocity
        self.pos += self.vel  # Update position
        self.rect.center = self.pos  # Update rect position
        if self.pos.x > WIDTH: self.pos.x = 0
        if self.pos.x < 0: self.pos.x = WIDTH
        if self.pos.y > HEIGHT: self.pos.y = 0
        if self.pos.y < 0: self.pos.y = HEIGHT
        self.rotation_angle += 1  # Increment the rotation angle
        if self.rotation_angle >= 360: self.rotation_angle = 0  # Reset if it exceeds 360 degrees
        rotated_image = pygame.transform.rotate(self.image, self.rotation_angle)
        rotated_rect = rotated_image.get_rect(center=self.pos)  # Keep the center in the same position
        screen.blit(rotated_image, rotated_rect)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.image.load("sprites/Bullet.png")
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)  # Set bullet's starting position
        self.vel = vec(math.cos(angle), math.sin(angle))  # Set bullet's velocity based on the angle
        self.vel *= 15  # Bullet speed multiplier
        self.radius = self.rect.height / 2  # Use half of height for radius
    def update(self):
        self.pos += self.vel  # Update position based on velocity
        self.rect.center = self.pos  # Update rect position to match the bullet position
        if self.rect.left < 0 or self.rect.right > WIDTH or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.kill()  # Remove the bullet from all sprite groups

P1 = Player()
all_sprites = pygame.sprite.Group()  # sprite group for collision detection etc
all_sprites.add(P1)  # add player to group to check collision with other objects
asteroids = pygame.sprite.Group()
last_spawn_time = pygame.time.get_ticks()
spawn_interval = 2000  # time interval (milliseconds) to spawn new asteroids

def ast_gen():
    global last_spawn_time
    if pygame.time.get_ticks() - last_spawn_time > spawn_interval:
        if len(asteroids) < 15:  # Ensure no more than 15 asteroids
            ast = Asteroid()  # Create a new asteroid
            asteroids.add(ast)  # Add to asteroids group
            all_sprites.add(ast)  # Add to all sprites group
            last_spawn_time = pygame.time.get_ticks()  # Reset spawn timer

def game_over():
    pygame.display.set_caption(f"Game Over! Your Score: {str(P1.score)}")
    user_input = ""
    cursor_pos = 0  # Variable to track the cursor position
    done = False
    FONT = pygame.font.Font(None, 40)
    for entity in all_sprites:
        entity.kill()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if len(user_input) > 0 and cursor_pos > 0:
                        user_input = user_input[:cursor_pos - 1] + user_input[cursor_pos:]
                        cursor_pos -= 1
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    user_input = user_input.strip().lower().capitalize()
                    try:
                        score.flush()
                        score.seek(0)
                        score.write(f"Name:{user_input},{str(P1.score)} Points\n---\n")
                    except Exception as e: print(f"Error: {e}")
                    time.sleep(0.5)
                    pygame.quit()
                    sys.exit()
                else:
                    user_input = user_input[:cursor_pos] + event.unicode + user_input[cursor_pos:]
                    cursor_pos += 1
        screen.fill(BLACK)
        text = FONT.render(f"Game Over!\nEnter Name: {user_input}\nScore: {str(P1.score)}", True, GREEN)
        screen.blit(text, (20, 20))
        pygame.mouse.set_visible(True)
        pygame.display.flip()
        clock.tick(FramePerSec)

while True:  # game loop
    screen.blit(background, (0, 0))
    crosshair_rect.center = pygame.mouse.get_pos()  # update position
    screen.blit(crosshair, crosshair_rect)  # draw the cursor
    f = pygame.font.SysFont("Verdana", 20)
    g = f.render(str(P1.score), True, YELLOW)
    h = f.render((str(P1.life)), True, RED)
    screen.blit(g, (WIDTH / 2, 10))  # score
    screen.blit(h, (WIDTH / 2, HEIGHT - 30))  # player health
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or P1.life <= 0:
            pygame.display.flip()
            game_over()
        if pygame.mouse.get_pressed()[0]:
            if P1.can_shoot():
                P1.shoot()
                P1.last_shot_time = pygame.time.get_ticks()
    ast_gen()
    for entity in all_sprites:
        entity.update()
    for asteroid in asteroids:
        dist = P1.get_distance(asteroid)
        if dist < P1.radius + asteroid.radius and P1.can_be_hit():
            P1.last_hit_time = pygame.time.get_ticks()
            P1.life -= 1
            print("Hull Breach!\n-1HP!")
            asteroid.vel *= 0.5  # Slow down asteroid on collision
            asteroid.break_up(asteroids)
            break
        screen.blit(asteroid.image, asteroid.rect)
        asteroid.update()  # Update asteroid (this handles movement, etc.)
    for bullet in P1.bullets:
        for asteroid in asteroids:
            dist = bullet.pos.distance_to(asteroid.pos)
            if dist < bullet.radius + asteroid.radius:
                bullet.kill()
                asteroid.break_up(asteroids)
                P1.score += 1
                print("Asteroid hit!\n+ 1 Point")
                break

    crosshair_rect.center = pygame.mouse.get_pos()  # Update the position of the crosshair
    screen.blit(crosshair, crosshair_rect)  # Draw the crosshair
    pygame.display.update()  # Refresh screen
    FramePerSec.tick(FPS)  # Maintain FPS