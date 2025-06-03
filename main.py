import pygame
import os

PATH = os.path.abspath(__file__ + '/..')
IMAGE_DIR = os.path.join(PATH, "sprites")

SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1000

BLOCK_HEIGHT = 50
BLOCK_WIDTH = 50

GRAVITY_SPEED = 10

pygame.init()

bg_image = pygame.transform.scale(pygame.image.load(os.path.join(IMAGE_DIR, 'bg.png')), (SCREEN_WIDTH, SCREEN_HEIGHT))

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

class Sprite(pygame.Rect):
    __list_sprites = []

    def __init__(self, x: int, y: int, width: int, height: int, image_name:str,speed_x: int | float = 0):
        super().__init__(x,y,width,height)
        self.__image_name = image_name

        self._speed_x = speed_x

        
        self.__load_image()
        self.__list_sprites.append(self)
    
    @property
    def bottom_y(self):
        return self.y + self.height
    
    @property
    def center_y(self):
        return self.y + self.height / 2

    @property
    def right_x(self):
        return self.x + self.width

    def __load_image(self):
        not_transformed_image = pygame.image.load(os.path.join(IMAGE_DIR, self.__image_name))
        scaled_image = pygame.transform.scale(not_transformed_image, (self.width, self.height))

        self.__image = scaled_image
        self.__flipped_image = pygame.transform.flip(scaled_image, True, False)
        self._facing_right = True         

    def _draw(self):
        image = self.__image if self._facing_right else self.__flipped_image
        screen.blit(image, (self.x, self.y))
    
    def _remove(self):
        if self in self.__list_sprites:
            self.__list_sprites.remove(self)
    
    def _move(self):
        raise NotImplementedError()
    
    def change_direction(self):
        self._speed_x = -self._speed_x
        self.__image = pygame.transform.flip(self.__image, True, False)
    
    def _process(self):
        self._draw()
        self._move()

    @classmethod
    def process_sprites(cls):
        for object in cls.__list_sprites:
            object._process()

class Block(Sprite):
    __list_blocks = []

    def __init__(self, x: int, y: int, image_name:str):
        super().__init__(x,y,BLOCK_WIDTH,BLOCK_HEIGHT,image_name)
        self.__list_blocks.append(self)

    def _move(self):
        pass

    @classmethod
    def create_by_map(cls,map_object:list[list[int]]):
        x = 0
        y = 0
        step = 50
        for row in map_object:
            for cell in row:
                if cell == 1:
                    cls(x,y,'block.png')

                x += step
            x = 0
            y += step

    @classmethod
    def get_list_blocks(cls) -> list['Block']:
        return cls.__list_blocks

class Entity(Sprite):
    def __init__(self, x, y, width, height, image_name, speed=0):
        super().__init__(x, y, width, height, image_name, speed)
        self._start_x = x
        self._start_y = y

        self._jump_counter = 0
    
    def _is_on_floor(self):
        for block in Block.get_list_blocks():
            if self.bottom == block.top and self.right > block.left and self.left < block.right:
                return True
        return False

    def _collide_top(self):
        for block in Block.get_list_blocks():
            if self.top == block.bottom and self.right > block.left and self.left < block.right:
                return True
        return False

    def _collide_left(self):
        for block in Block.get_list_blocks():
            if self.left == block.right and self.bottom > block.top and self.top < block.bottom:
                return True
        return False

    def _collide_right(self):
        for block in Block.get_list_blocks():
            if self.right == block.left and self.bottom > block.top and self.top < block.bottom:
                return True
        return False
    
    def _process(self):
        self._fell()
        self._gravity()
        self._jump_process()
        super()._process()

    def _gravity(self):
        if not self._is_on_floor() and not self.__jump_in_process:
            self.y += GRAVITY_SPEED
    
    def _fell(self):
        if self.y > SCREEN_HEIGHT:
            self.y = self._start_y
            self.x = self._start_x


    def _jump_process(self):
        if self._collide_top():
            self._jump_counter = 0
        if self._jump_counter > 0:
            self.y -= GRAVITY_SPEED
            self._jump_counter -= 1

    @property
    def __jump_in_process(self):
        return self._jump_counter > 0

class Bullet(Entity):
    _list_bullets = []
    
    def __init__(self, x, y, width, height, image_name, speed=0, right=True):
        speed = speed if right else -speed
        super().__init__(x, y, width, height, image_name, speed)
        Bullet._list_bullets.append(self)

    def _move(self):
        steps = int(abs(self._speed_x))
        step_dir = 1 if self._speed_x > 0 else -1
        for _ in range(steps):
            self.x += step_dir
            if self._collide_left() or self._collide_right():
                self._remove()
                break
            
            for enemy in enemies:
                if self.colliderect(enemy):
                    self._remove()
                    break
            
            if self.x > SCREEN_WIDTH:
                self._remove()
                break

    
    def _process(self):
        Sprite._process(self)
    
    
class Dude(Entity):
    def __init__(self, x, y, width, height, image_name, speed=0):
        super().__init__(x, y, width, height, image_name, speed)
        self.__jump_base_counter = 20
        self.__shoot_cooldown = 0
        self.bullets = []
    
    def _move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and not self._collide_left():
            self._facing_right = False
            self.x -= self._speed_x
        if keys[pygame.K_RIGHT] and not self._collide_right():
            self._facing_right = True
            self.x += self._speed_x
        if keys[pygame.K_UP] and self._is_on_floor():
            self._jump_counter = self.__jump_base_counter
        
    def _shoot(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN] and not self.__shoot_cooldown > 0:
            bullet = Bullet(self.x + (self.width / 1.4) if self._facing_right else self.x - 3, self.y + (self.height/2) + 1, 20, 10, 'bullet.png', 10, self._facing_right)
            bullet._move()
            self.bullets.append(bullet)
            self.__shoot_cooldown = 10
    
    def _restart(self):
        self.x = self._start_x
        self.y = self._start_y
        for enemy in enemies:
            Sprite._Sprite__list_sprites.remove(enemy)
        enemies.clear()
        enemies.extend(create_base_enemies())
                
    
    def _process(self):
        if self.__shoot_cooldown > 0:
            self.__shoot_cooldown -= 1
        self._shoot()
        
        for enemy in enemies:
            if self.colliderect(enemy):
                self._restart()
        
        if self.y > SCREEN_HEIGHT:
            self._restart()
        return super()._process()
    
class Enemy(Entity):
    def __init__(self, x, y, width, height, image_name, speed=0):
        super().__init__(x, y, width, height, image_name, speed)
        self._base_speed = speed
        self._direction = 1

    def change_direction(self):
        self._direction *= -1
        self._facing_right = not self._facing_right
    
    def _next_is_floor(self):
        foot_x = self.centerx + self._direction * self._base_speed
        foot_y = self.bottom + 1

        for block in Block.get_list_blocks():
            if block.collidepoint(foot_x, foot_y):
                return True
        return False
    
    def _death(self):
        for bullet in dude.bullets:
            if self.colliderect(bullet):
                self._remove()
                bullet._remove()
                dude.bullets.remove(bullet)
                enemies.remove(self)
                break

    
    def _move(self):

        if self._collide_left() or self._collide_right() or not self._next_is_floor():
            self.change_direction()
            
            if self._collide_left():
                self.x += self._base_speed
            
            if self._collide_right():
                self.x -= self._base_speed
        
        else:
            self.x += self._direction * self._base_speed
    
    def _process(self):
        self._death()
        return super()._process()
    
map_matrix = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,1],
    [1,1,1,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,1,1,1,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1],
    [1,0,1,1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1],
    [1,1,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,1,1],
    [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1,0,0,0,1,0,0,0,0,1,1,1,1,0,1,1,1,1,1,1]
]


Block.create_by_map(map_matrix)
dude = Dude(50,70,50,70,'dude2.png', speed=5)
def create_base_enemies():
    return [
        Enemy(630, 880, 70, 70, 'enemy.png', speed=5),
        Enemy(1345, 130, 70, 70, 'enemy.png', speed=5),
        Enemy(1370, 330, 70, 70, 'enemy.png', speed=5),
        Enemy(1765, 130, 70, 70, 'enemy.png', speed=5),
        Enemy(395, 380, 70, 70, 'enemy.png', speed=5)
    ]

enemies = create_base_enemies()

def start_game():
    game_run = True
    timer = pygame.time.Clock()
    while game_run:
        # screen.fill((37, 64, 138))
        screen.blit(bg_image, (0,0))
        Sprite.process_sprites()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_run = False

        pygame.display.flip()
        timer.tick(60)
        if not enemies and dude.x > SCREEN_WIDTH:
            game_run = False

start_game()