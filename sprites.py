import pygame
import random

from settings import *


# Player sprite
class Player(pygame.sprite.Sprite):
    SPEED = 7  # Speed constant
    containers = None  # List of all groups to add Player to

    def __init__(self, game):
        self.game = game
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = pygame.image.load("images/plane.png").convert_alpha()  # Plane image
        self.rect = self.image.get_rect(center=game.master.SCREENRECT.center)  # Plane rect object
        self.mask = pygame.mask.from_surface(self.image)
        self.lastmoved = 0

    # Moves the plane up or down
    def move(self, direction):
        self.rect.move_ip(0, direction * self.SPEED)  # Moves the rect object to new position
        self.rect.clamp_ip(self.game.master.SCREENRECT)  # Keeps plane within screen borders

        if direction == 0 or self.rect.top == 0 or self.rect.bottom == HEIGHT:
            self.lastmoved += 1
        else:
            self.lastmoved = 0


# Background sprite
class Background(pygame.sprite.Sprite):
    vel = -5  # Velocity constant
    containers = None  # List of all groups to add Background to

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.background_img = pygame.image.load("images/background.png").convert_alpha()  # Background image
        self.rect = self.background_img.get_rect(topleft=(0, 0))  # Background rect object
        self.rect.width *= 2

        self.image = pygame.Surface(self.rect.size)  # Surface object used for scrolling background
        self.image.blits(blit_sequence=((self.background_img, (0, 0)),  # Blit background image to surface twice, ...
                                        (self.background_img, (self.rect.centerx, 0))))  # ... side by side

    # Scrolls the background sideways to simulate movement
    def update(self):
        self.rect.centerx = (self.rect.centerx + self.vel) % (self.rect.width // 2)


# Bird sprite
class Bird(pygame.sprite.Sprite):
    vel = -10  # Velocity
    containers = None  # List of all groups to add Bird to

    # Attributes used by random_spawn method
    lastspawn = 0  # Keeps track of how long has passed since last bird was spawned

    def __init__(self, game, height):
        self.game = game
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.ticks_since_spawn = 0  # Stores how many game ticks have passed
        self.frame_count = 0  # Stores index of animation frame to be displayed
        self.frames = self.load_images()  # Array of all frames for the animation

        self.image = self.frames[0]  # Image initialised as first frame
        self.rect = self.frames[0].get_rect()  # Bird rect object
        startx = game.master.SCREENRECT.width + self.rect.width
        self.rect.center = (startx, height)

    # Animates and changes position of bird
    def update(self):
        self.rect.move_ip((self.vel, 0))  # Moves bird

        # Animates bird
        self.ticks_since_spawn += 1
        if self.ticks_since_spawn % 6 == 0:
            self.frame_count = (self.frame_count + 1) % 8
            self.image = self.frames[self.frame_count]

    # Resets Bird's attributes
    @classmethod
    def reset(cls):
        cls.vel = -10
        cls.maxtime = INITIAL_MAXTIME
        cls.probability = INITIAL_BIRD_PROBABILITY
        cls.spawnrate = INITIAL_SPAWNRATE

    # Returns array of the animation frames
    @staticmethod
    def load_images():
        imgs = []
        for i in range(1, 9):
            imgs.append(pygame.image.load(f"images/bird/bird{i}.png").convert_alpha())

        return imgs

    # Random chance of spawning bird at random height
    @classmethod
    def random_spawn(cls, game):
        if (random.random() <= (cls.probability / cls.spawnrate)) \
                or (cls.lastspawn >= cls.maxtime * FPS):
            cls.lastspawn = 0
            height = random.randint(40, HEIGHT - 40)
            return cls(game, height)

        return False


# Tests for collision between sprites in one group and sprites in another
def pixelperfect_collision(group1, group2, dokillgroup1, dokillgroup2):
    collided = False  # Variable used to store whether or not a collision has occurred
    collisions = pygame.sprite.groupcollide(group1, group2, False, False)  # Detect rect collisions

    if collisions:  # Checks for pixel perfect collision if a rect collision has occurred
        for sprite1 in collisions.keys():  # Loops through or collided sprites in group 1
            try:  # If instance has mask attribute, use that as the mask
                sprite1_mask = sprite1.mask
            except AttributeError:  # Otherwise, get mask from the image attribute
                sprite1_mask = pygame.mask.from_surface(sprite1.image)

            for sprite2 in collisions[sprite1]:  # Loops through all the sprites that sprite 1 collided with
                try:  # If instance has mask attribute, use that as the mask
                    sprite2_mask = sprite2.mask
                except AttributeError:  # Otherwise, get mask from the image attribute
                    sprite2_mask = pygame.mask.from_surface(sprite2.image)

                offset = (sprite2.rect.x - sprite1.rect.x, sprite2.rect.y - sprite1.rect.y)
                if sprite1_mask.overlap(sprite2_mask, offset):  # Check for pixel perfect collision
                    collided = True  # Collision has occurred; collided set to True
                    if dokillgroup1: sprite1.kill()
                    if dokillgroup2:
                        sprite2.kill()
                    else:
                        break

            if collided and not dokillgroup1: break

    return collided
