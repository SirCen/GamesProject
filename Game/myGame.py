# imports
try:
    import simplegui
except ImportError:
    import SimpleGUICS2Pygame.simpleguics2pygame as simplegui

try:
    from PIL import Image
    import pathlib
    from os import getcwd
except ImportError or NotImplementedError:
    pass

import math
import time
from random import randint, choice, uniform
from collections import deque


# vector class used from the lectures, this class has all the methods used for the vectors of the objects.
class Vector:

    # Initialiser
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    # Returns a string representation of the vector
    def __str__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"

    # Tests the equality of this vector and another
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # Tests the inequality of this vector and another
    def __ne__(self, other):
        return not self.__eq__(other)

        # Returns a tuple with the point corresponding to the vector

    def getP(self):
        return (self.x, self.y)

    # Returns a copy of the vector
    def copy(self):
        return Vector(self.x, self.y)

    # Adds another vector to this vector
    def add(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __add__(self, other):
        return self.copy().add(other);

    # Negates the vector (makes it point in the opposite direction)
    def negate(self):
        return self.multiply(-1)

    def __neg__(self):
        return self.copy().negate()

    # Subtracts another vector from this vector
    def subtract(self, other):
        return self.add(-other)

    def __sub__(self, other):
        return self.copy().subtract(other)

    # Multiplies the vector by a scalar
    def multiply(self, k):
        self.x *= k
        self.y *= k
        return self

    def __mul__(self, k):
        return self.copy().multiply(k)

    def __rmul__(self, k):
        return self.copy().multiply(k)

    # Divides the vector by a scalar
    def divide(self, k):
        return self.multiply(1 / k)

    def __truediv__(self, k):
        return self.copy().divide(k)

    # Normalizes the vector
    def normalize(self):
        return self.divide(self.length())

    # Returns a normalized version of the vector
    def getNormalized(self):
        return self.copy().normalize()

    # Returns the dot product of this vector with another one
    def dot(self, other):
        return self.x * other.x + self.y * other.y

    # Returns the length of the vector
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    # Returns the squared length of the vector
    def lengthSquared(self):
        return self.x ** 2 + self.y ** 2

    # Reflect this vector on a normal
    def reflect(self, normal):
        n = normal.copy()
        n.multiply(2 * self.dot(normal))
        self.subtract(n)
        return self

    # Returns the angle between this vector and another one
    # You will need to use the arccosine function:
    # acos in the math library
    def angle(self, other):
        return math.acos(self.dot(other) / (self.length() * other.length()))

    # Rotates the vector to be 90 degrees anticlockwise
    def rotAnti(self):
        aux = self.copy()
        self.x = -aux.y
        self.y = aux.x
        return self


# class from lecture slides used in collisions between objects to dectect if the objects are in the same postions
class UPair:
    def __init__(self, fst, snd):
        self.fst = fst
        self.snd = snd

    def __hash__(self):
        return hash((min(hash(self.fst), hash(self.snd)),
                     max(hash(self.fst), hash(self.snd))))

    def __eq__(self, other):
        return ((self.fst == other.fst and self.snd == other.snd) or
                (self.fst == other.snd and self.snd == other.fst))

    def __ne__(self, other):
        return not self.__eq__(other)


# used to check whether a vector position is within the boundaries of the canvas
def inBounds(pos):
    return 1 < pos.x < game.width and 1 < pos.y < game.height


# stops the timers
def timerStop(timer):
    if timer.is_running():
        timer.stop()


# class for the animated background 
class Background:

    # initialises variables used within the class, 
    # the frame size is the size of 1 frame of the background relative to the canvas
    def __init__(self, img):
        self.counter = 0;
        self.img = img
        self.frameSize = (self.img.get_width(), self.img.get_height() / 4)
        self.theHeight = 0

    # updates the counter, taking into account the score
    # updates the height, the counter modded by how many frames it needs to move before moving
    def update(self):
        self.counter += 1.5
        self.theHeight = (self.img.get_height() - (self.frameSize[1] / 2)) - (self.counter % (self.frameSize[1] * 3))

    # updates the background to animate it
    def drawBack(self, canvas):
        self.update()
        canvas.draw_image(self.img, (self.frameSize[0] / 2, self.theHeight), (self.frameSize[0], self.frameSize[1]),
                          (game.width / 2, game.height / 2), (game.width, game.height))

    # draws the background on the canvas
    def doingDrawing(self, canvas):
        canvas.draw_image(self.img, (self.frameSize[0] / 2, self.theHeight), (self.frameSize[0], self.frameSize[1]),
                          (game.width / 2, game.height / 2), (game.width, game.height))


# class for the orientation of the objects
class Orientation:
    def __init__(self, pos1, pos2):
        # calculating change in x and y for trig function
        self.changeX = pos2.x - pos1.x
        self.changeY = pos2.y - pos1.y
        # atan2 returns an angle between pi and -pi depending on the quadrant
        self.angle = math.atan2(self.changeX, self.changeY)
        if (self.angle >= 0):
            self.orient = math.pi - (self.angle)
        else:
            self.orient = math.pi - ((2 * math.pi) + self.angle)


# class for the player
class Player:
    def __init__(self, imgStationary, imgMoving, imgBoosted):
        self.pos = Vector(game.width / 2, game.height / 7 * 5)
        self.vel = Vector()
        self.rad = 15
        self.health = 3
        self.points = 0
        self.timer = simplegui.create_timer(1000, self.addPoints)
        self.imgStationary = imgStationary
        self.imgMoving = imgMoving
        self.imgBoosted = imgBoosted
        self.img = imgStationary
        self.orientation = Orientation(Vector(0, 1), Vector(0, 0))
        self.shieldIsActive = False

    # adds 1 point to the score per second
    def addPoints(self):
        self.points += 1

    # used when the player is hit by an enemy
    # can be called multiple times to simulate more powerful enemy hits
    def hit(self):
        if not self.shieldIsActive:
            self.health -= 1

    # returns boolean on whether or not the player is still alive
    def isDead(self):
        return self.health < 1

    # draws player on the canvas
    # will replace with draw_image when sprites are finished
    def draw(self, canvas):
        canvas.draw_image(self.img, (self.img.get_width() / 2, self.img.get_height() / 2),
                          (self.img.get_width(), self.img.get_height()), (self.pos.x, self.pos.y),
                          (self.rad * 5, self.rad * 5), self.orientation.orient)

    # updates position of player and halves velocity to simulate friction
    def update(self):
        self.pos.add(self.vel)
        self.vel.multiply(0.5)
        if self.shieldIsActive:
            self.img = self.imgBoosted
        elif self.vel.length() <= 0.5:
            self.img = self.imgStationary
        else:
            self.img = self.imgMoving

    # updates orientation when clicks
    def orientUpdate(self, direction):
        self.orientation = Orientation(self.pos, direction)

    # class used for bullets fired by player


# can be adapted for bullets fired by enemies if you change the hit class
class Bullet:
    def __init__(self, direction):
        # passed into constructor depending on where mouse is clicked
        self.direction = direction.getNormalized()
        # initial player position used as origin of bullet
        self.pos1 = game.player.pos.copy()
        # gets velocity of bullet from player position to mouse position
        self.vel = direction.subtract(self.pos1).normalize().multiply(10)
        # other end of the bullet to pos1
        # points towards target
        self.pos2 = self.pos1.__add__(self.vel)
        # laser bullet image
        self.img = game.sprites["laser"]
        self.bulletSize = 20 + (game.bulletDmg * 6)

        self.orientation = Orientation(self.pos1, self.pos2)

    # checks if the bullet has hit the enemy and return boolean
    def hit(self, enemy):
        if self.pos1.__sub__(enemy.pos.copy()).length() < enemy.rad or self.pos2.__sub__(
                enemy.pos.copy()).length() < enemy.rad:
            enemy.hit()
            return True
        return False

    # draws bullet on canvas using pos1 and pos2
    def draw(self, canvas):
        canvas.draw_image(self.img, (self.img.get_width() / 2, self.img.get_height() / 2),
                          (self.img.get_width(), self.img.get_height()),
                          ((self.pos1.x + self.pos2.x) / 2, (self.pos1.y + self.pos2.y) / 2),
                          (self.bulletSize, self.bulletSize),
                          self.orientation.orient)

    # updates position of bullet based on velocity value
    def update(self):
        self.pos1.add(self.vel)
        self.pos2.add(self.vel)

    # returns boolean based on whether bullet is still on the screen or not
    def inBounds(self):
        return inBounds(self.pos1) and inBounds(self.pos2)


# base class for enemies
# plan to create subclasses that inherit this one with
# different stats for different enemies
class Enemy:
    def __init__(self, health, movement="tracking"):
        self.health = health
        self.movement = movement
        self.col = 'Fuchsia'
        self.rad = randint(20, 40)
        self.img = game.sprites["asteroid"]
        self.orient = uniform(0, 2 * math.pi)
        self.rotation = uniform(math.pi / 256, math.pi / 64)

        # enemies can either move from left to right, right to left, top to
        # bottom, bottom to top or track the player
        # movement of enemy is randomly chosen from list of movements and the
        # spawn position is randomly generated depending on where the enemy
        # will move
        # e.g. 'left' will spawn on left side at a random height and move
        # towards the right side of the screen
        # at the moment tracking enemies only spawn from the top and move
        # slightly slower
        # when sprites are finished can change non-tracking enemy images to
        # asteroids and tracking to other ships
        if self.movement == "left":
            self.pos = Vector(-(self.rad * 2) + 1, randint(0, game.height))
            self.vel = Vector(randint(1, 5), 0)
            game.nonTracking += 1
        elif self.movement == "right":
            self.pos = Vector(game.width + (self.rad * 2 - 1), randint(0, game.height))
            self.vel = Vector(randint(-5, -1), 0)
            game.nonTracking += 1
        elif self.movement == "up":
            self.pos = Vector(randint(0, game.width), -(self.rad * 2) + 1)
            self.vel = Vector(0, randint(1, 5))
            game.nonTracking += 1
        elif self.movement == "down":
            self.pos = Vector(randint(0, game.width), game.height + (self.rad * 2 - 1))
            self.vel = Vector(0, randint(-5, -1))
            game.nonTracking += 1
        else:
            __posChoices = [Vector(randint(0, game.width), -50),
                            Vector(randint(0, game.width), game.height + 50),
                            Vector(-50, randint(0, game.height)),
                            Vector(game.width + 50, randint(0, game.height))]
            self.pos = choice(__posChoices)
            # sets inital velocity to make the enemy go towards the player
            self.vel = game.player.pos.copy().subtract(self.pos).normalize()
            self.health = 4
            self.rad = 20
            self.img = game.sprites["alien"]
            self.orient = 0

    # can replace draw_circle with draw_image when sprites are finished
    def draw(self, canvas):
        canvas.draw_image(self.img, (self.img.get_width() / 2, self.img.get_height() / 2),
                          (self.img.get_width(), self.img.get_height()), (self.pos.x, self.pos.y),
                          (self.rad * 2, self.rad * 2), self.orient)

    # when enemy is hit by bullet
    # also checks if they are dead using isDead() and respawns/adds points
    # if it is dead
    def hit(self):
        self.health -= game.bulletDmg

        if self.isDead():
            self.destroy()
            game.player.points += 10

            if game.level.level < 10:
                __upperBound = 600 - (game.level.level * 10)
            else:
                __upperBound = 500

            __rng = randint(0, __upperBound)

            # 1 in 10 chance at level 10 and above
            if __rng in range(0, 10):
                game.powerUps.append(HealthPowerUp(self.pos))
            # 1 in 15 chance at level 10 and above
            elif __rng in range(10, 35):
                game.powerUps.append(BulletPowerUp(self.pos))
            # 1 in 20 chance at level 10 and above
            elif __rng in range(35, 50):
                game.powerUps.append(ShieldPowerUp(self.pos))
            else:
                pass

    # used to detect if the enemy is dead if health is below 1.
    def isDead(self):
        return self.health < 1

    def destroy(self):
        # if the current enemy is non-tracking, the number of non-tracking
        # enemies is decreased (explained in interaction class)
        if self.movement != "tracking":
            game.nonTracking -= 1
        # adds an explosion animation at the position where the current
        # enemy died
        game.explosions.append(ExplosionAnimation(self.pos))
        # adds a new enemy using the interaction class to replace the
        # current one
        # interaction.addEnemy()
        # removes the current enemy from the list of enemies
        game.enemies.remove(self)

    def update(self):
        # if the movement of the current enemy in tracking, change the velocity
        # so that it moves towards the player
        if self.movement == "tracking":
            self.vel = game.player.pos.copy().subtract(self.pos).normalize() * 1.5
            orientation = Orientation(self.pos, game.player.pos)
            self.orient = orientation.orient
        else:
            self.orient = (self.orient + self.rotation) % (2 * math.pi)
        self.pos.add(self.vel)
        # check if the current enemy has collided with the player
        self.hitPlayer()
        # check whether the current enemy is on screen
        self.wrap()

    # method to check if two enemies collide, 
    # by detecting if the center of the objects comes within the distance of the radius and border.
    def collide(self, other):
        if self == other:
            return False
        else:
            return (self.pos - other.pos).length() <= (self.rad + 1) + (other.rad + 1)

    # reflects the velocity on a normal to the current vector the objects are travelling at.
    def bounce(self, normal):
        self.vel.reflect(normal)

    # if the current enemy hits the player, decrease the health of the player
    # and replace the current enemy
    def hitPlayer(self):
        if self.pos.__sub__(game.player.pos.copy()).length() < self.rad + game.player.rad:
            self.destroy()
            game.player.hit()

    # used to wrap enemies on the screen that are not tracking
    # does not use inBounds() function as only one vector needs to be checked
    # and it is different for each movement type
    def wrap(self):
        if self.pos.x - self.rad > game.width:
            self.pos = Vector(-self.rad, randint(0, game.height))
        if self.pos.x + self.rad < 0:
            self.pos = Vector(game.width + self.rad, randint(0, game.height))
        if self.pos.y - self.rad > game.height:
            self.pos = Vector(randint(0, game.width), -self.rad)
        if self.pos.y + self.rad < 0:
            self.pos = Vector(randint(0, game.width), game.height + self.rad)


# animation class for the explosion animation
class ExplosionAnimation:
    def __init__(self, pos, scale=0.6):
        self.image = game.sprites["explosion"]
        self.pos = pos
        self.scale = scale
        self.size = (900, 900)
        self.dims = (9, 9)
        self.window = (100, 100)
        self.center = (self.window[0] / 2, self.window[1] / 2)
        self.offset = (0, 0)
        self.current = [0, 0]
        self.duration = 1
        self.previousFrame = 1
        self.timer = simplegui.create_timer(100, self.nextFrame)
        self.timer.start()

    # changes the animation frame at a regular time interval
    def nextFrame(self):
        self.current[0] = (self.current[0] + 1) % self.dims[0]
        if self.current[0] == 0:
            self.current[1] = (self.current[1] + 1) % self.dims[1]

    # draws the image of the explosion.
    def draw(self, canvas):
        x = self.current[0] * self.window[0]
        y = self.current[1] * self.window[1]
        canvas.draw_image(self.image,
                          (self.center[0] + self.offset[0] + x, self.center[1] + self.offset[1] + y),
                          self.window, (self.pos.x, self.pos.y),
                          (self.window[0] * self.scale, self.window[1] * self.scale))


# parent class for all power-ups found in the game
class PowerUp:
    def __init__(self, pos, img):
        self.pos = pos
        self.img = img
        self.powerUpSize = 50

    # checks if the power-up has been collected by the player
    # if so, the effect is triggered and the power-up is removed from the array
    def collect(self):
        if self.pos.__sub__(game.player.pos.copy()).length() < self.powerUpSize:
            game.powerUps.remove(self)
            self.effect()

    def draw(self, canvas):
        canvas.draw_image(self.img, (self.img.get_width() / 2, self.img.get_height() / 2),
                          (self.img.get_width(), self.img.get_height()),
                          (self.pos.x, self.pos.y), (self.powerUpSize, self.powerUpSize))

    # this method is overriden in the child classes to implement an effect
    def effect(self):
        pass


# inherits from the PowerUp class
# gives the player an additional point of health
class HealthPowerUp(PowerUp):
    def __init__(self, pos):
        PowerUp.__init__(self, pos, game.sprites["healthPowerUp"])

    def effect(self):
        game.player.health += 1


# inherits from the PowerUp class
# makes the player invunerable for a brief period of time
class ShieldPowerUp(PowerUp):
    def __init__(self, pos):
        PowerUp.__init__(self, pos, game.sprites["shieldPowerUp"])
        self.timer = simplegui.create_timer(3000, self.timer_handler)

    # starts the timer for the power-up and adds it to the shield array
    def effect(self):
        self.timer.start()
        game.shieldPowerUps.append(self)

    # called when the timer reaches the trigger time
    # stops the timer and removes the entity from the shield array
    def timer_handler(self):
        timerStop(self.timer)
        game.shieldPowerUps.remove(self)


# inherits from the PowerUp class
# increases the strength of bullets fired by the player for a brief period of time
class BulletPowerUp(PowerUp):
    def __init__(self, pos):
        PowerUp.__init__(self, pos, game.sprites["bulletPowerUp"])
        self.timer = simplegui.create_timer(5000, self.timer_handler)

    # starts the timer for the power-up and adds it to the shield array
    def effect(self):
        self.timer.start()
        game.bulletPowerUps.append(self)

    # called when the timer reaches the trigger time
    # stops the timer and removes the entity from the shield array
    def timer_handler(self):
        timerStop(self.timer)
        game.bulletPowerUps.remove(self)


# handles all keyboard inputs from the user throughout the game
class Keyboard:
    def __init__(self):
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        self.restart = False

    # key down handler for in game actions
    def keyDown(self, key):
        if key == simplegui.KEY_MAP['w']:
            self.up = True
        if key == simplegui.KEY_MAP['a']:
            self.left = True
        if key == simplegui.KEY_MAP['s']:
            self.down = True
        if key == simplegui.KEY_MAP['d']:
            self.right = True
        if key == simplegui.KEY_MAP['1']:
            game.player.health = 0

    # key up handler for in game actions
    def keyUp(self, key):
        if key == simplegui.KEY_MAP['w']:
            self.up = False
        if key == simplegui.KEY_MAP['a']:
            self.left = False
        if key == simplegui.KEY_MAP['s']:
            self.down = False
        if key == simplegui.KEY_MAP['d']:
            self.right = False

    # key down handler for restarting the game
    def restartKeyDown(self, key):
        self.restart = True

    # disables the keyboard
    def disable(self, key):
        pass


# used to track mouse clicks within the game canvas
class Mouse:
    def __init__(self):
        self.pos = Vector()

    # click handler for in game
    def inGame(self, pos):
        game.bullets.append(Bullet(Vector(pos[0], pos[1])))
        game.player.orientUpdate(Vector(pos[0], pos[1]))

    # click handler for the help screen
    def helpScreen(self, pos):
        if 148 < pos[0] < 338 and 702 < pos[1] < 756:
            frame.set_draw_handler(game.startScreen)

    # click hanlder for the main menu
    def mainMenu(self, pos):
        if 125 < pos[0] < 350 and 615 < pos[1] < 680:
            frame.set_draw_handler(game.draw)
            frame.set_mouseclick_handler(self.inGame)
            game.level.gameStart()

        if 155 < pos[0] < 316 and 702 < pos[1] < 756:
            frame.set_draw_handler(game.helpScreen)
            frame.set_mouseclick_handler(self.helpScreen)


# contains the setup for levels as well as methods to start and restart the game
class Levels:
    def __init__(self, game):
        self.g = game
        self.level = 1
        self.numberOfEnemies = self.level * 2
        self.levelStart = True
        self.levelTimer = simplegui.create_timer(2500, self.showLevel)

    # method used in between levels when the level text is displayed on the screen
    def showLevel(self):
        self.levelStart = False
        self.spawnEnemies()
        self.level += 1
        self.numberOfEnemies = self.level * 2
        self.levelTimer.stop()

    # spawns the correct number of enemies for each level whilst controlling
    # the number of non-tracking enemies for balanced levels
    def spawnEnemies(self):
        while len(self.g.enemies) < self.numberOfEnemies:
            if self.g.nonTracking < self.numberOfEnemies / 2 * 3:
                self.g.enemies.append(Enemy(2, choice(self.g.enemyMovements)))
            else:
                self.g.enemies.append(Enemy(4))

    # used on the game over screen to check whether the game needs to restart
    def restart(self):
        self.gameStart()
        # changes draw handler to display game objects
        frame.set_draw_handler(game.startScreen)

    # used when a new game is started
    # sets various handlers to the correct in game handlers
    # resets the player position, health (if required) and points
    # resets all entity lists
    def gameStart(self):
        game.player = Player(game.sprites["playerStationary"], game.sprites["playerMoving"],
                             game.sprites["playerShieldBoost"])

        frame.set_keydown_handler(self.g.keyboard.keyDown)
        frame.set_keyup_handler(self.g.keyboard.keyUp)
        frame.set_mouseclick_handler(self.g.mouse.inGame)

        self.level = Levels(self.g).level
        self.numberOfEnemies = self.level * 2

        self.g.keyboard.restart = False

        self.g.player.pos = Player(game.sprites["playerStationary"], game.sprites["playerMoving"],
                                   game.sprites["playerShieldBoost"]).pos
        if self.g.player.health != Player(game.sprites["playerStationary"], game.sprites["playerMoving"],
                                          game.sprites["playerShieldBoost"]).health:
            self.g.player.health = Player(game.sprites["playerStationary"], game.sprites["playerMoving"],
                                          game.sprites["playerShieldBoost"]).health
        self.g.player.points = 0
        self.g.explosions = []
        self.g.bullets = []
        self.g.enemies = []
        self.g.powerUps = []
        self.g.shields = []
        self.g.nonTracking = 0
        self.g.player.timer.start()

    # template used to create and display all levels
    def baseLevel(self, canvas):
        __levelText = "Level " + str(self.level)
        if self.levelStart:
            if not self.levelTimer.is_running():
                self.levelTimer.start()
            canvas.draw_text(__levelText,
                             (game.width / 2 - (frame.get_canvas_textwidth(__levelText, 70) / 2), game.height / 2),
                             70, "White")

        self.g.update()

        if len(self.g.enemies) == 0 and len(self.g.explosions) == 0:
            self.levelStart = True


# handles interactions bewteen objects
class Interaction:
    def __init__(self, game):
        self.g = game

    # updates the player velocity depending on whether a key is pressed down
    # and whether the player is in bounds or not
    def playerKeyboardMove(self):
        if self.g.keyboard.right and inBounds(Vector(self.g.player.pos.x + self.g.player.rad, self.g.player.pos.y)):
            self.g.player.vel.add(Vector(1, 0))
        if self.g.keyboard.left and inBounds(Vector(self.g.player.pos.x - self.g.player.rad, self.g.player.pos.y)):
            self.g.player.vel.add(Vector(-1, 0))
        if self.g.keyboard.up and inBounds(Vector(self.g.player.pos.x, self.g.player.pos.y - self.g.player.rad)):
            self.g.player.vel.add(Vector(0, -1))
        if self.g.keyboard.down and inBounds(Vector(self.g.player.pos.x, self.g.player.pos.y + self.g.player.rad)):
            self.g.player.vel.add(Vector(0, 1))

    def update(self):
        # for every enemy in the list, update it's position and check whether
        # it has collided with any other enemies
        for enemy in self.g.enemies:
            enemy.update()
            for otherEnemy in self.g.enemies:
                if otherEnemy != enemy and inBounds(enemy.pos) and inBounds(otherEnemy.pos):
                    if enemy.collide(otherEnemy) and UPair(enemy, otherEnemy) not in self.g.inCollision:
                        self.g.inCollision.add(UPair(enemy, otherEnemy))
                        n = (enemy.pos - otherEnemy.pos).normalize()
                        enemy.bounce(n)
                    else:
                        self.g.inCollision.discard(UPair(enemy, otherEnemy))

        # for every bullet in the list, update the position of the bullet and...
        for bullet in self.g.bullets:
            bullet.update()
            # ...for every enemy in the list check whether the bullet has hit
            # the enemy
            for enemy in self.g.enemies:
                if bullet.hit(enemy):
                    if bullet in self.g.bullets:
                        self.g.bullets.remove(bullet)

        # updates every power-up on the screen
        for powerUp in self.g.powerUps:
            powerUp.collect()


# handles various games between objects
class Game:
    def __init__(self):
        # width and height of canvas
        self.width = 475
        self.height = 800

        self.sprites = {
            "startScreen":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICgxvXXuwkM/preview',
            "asteroid":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICguo_vgwsM/preview',
            "alien":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICg-raU7gkM/preview',
            "explosion":
                'http://www.cs.rhul.ac.uk/courses/CS1830/sprites/explosion-spritesheet.png',
            "laser":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICguo-f9AkM/preview',
            "playerMoving":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICg2uvL-wsM/preview',
            "playerStationary":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICg-pSStAkM/preview',
            "playerShieldBoost":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICgpsbFgwkM/preview',
            "background":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICguv7E-gsM/preview',
            "helpScreen":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICgxsCx3QgM/preview',
            "gameOverScreen":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICg-t6gwgoM/preview',
            "healthPowerUp":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICghv21rQsM/preview',
            "shieldPowerUp":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICghrKu_gsM/preview',
            "bulletPowerUp":
                'https://www.piskelapp.com/img/agxzfnBpc2tlbC1hcHByFwsSCkZyYW1lc2hlZXQYgICgxq7A7QoM/preview'
        }

        # attempts to load offline versions of all sprites
        # in the event of an error, url links are used instead
        for sprite in self.sprites:
            try:
                self.sprites[sprite] = simplegui.load_image(
                    pathlib.Path(Image.open(getcwd() + '/sprites/' + sprite + '.png')).as_uri())
            except Exception:
                self.sprites[sprite] = simplegui.load_image(self.sprites[sprite])

        self.explosions = []
        self.enemies = []
        self.bullets = []
        self.powerUps = []
        self.shieldPowerUps = []
        self.bulletPowerUps = []

        self.player = ""
        self.keyboard = Keyboard()
        self.mouse = Mouse()
        self.background = Background(self.sprites["background"])

        self.interaction = Interaction(self)
        self.level = Levels(self)

        # tracks the number of enemies that do not track the player
        # the number of non tracking enemies is controlled to prevent the case
        # of only non tracking enemies flying around the screen
        self.nonTracking = 0
        self.bulletDmg = 1
        # set of enemy movement types
        self.enemyMovements = ["left", "right", "up", "down", "tracking", "tracking", "tracking"]

        self.gameOverSizeDims = [1, 1]
        self.gameOverDimsScale = (self.height / self.width) * 5
        self.inCollision = set()

    def update(self):
        # updates the velocity of the player if needed
        self.interaction.playerKeyboardMove()
        # updates the position and velocity of the player
        self.player.update()

        # for every explosion on the screen, if the animation has reached the
        # last frame, remove it from the list (and thereforescreen), otherwise
        # advance the frame
        for explosion in self.explosions:
            if explosion.current[0] == 8 and explosion.current[1] == 8:
                timerStop(explosion.timer)
                self.explosions.remove(explosion)
            else:
                explosion.nextFrame()

        self.interaction.update()

        # if the user has collected a shield power-up that is still active
        # then the user will gain a shield
        if len(self.shieldPowerUps) != 0:
            self.player.shieldIsActive = True
        else:
            self.player.shieldIsActive = False

        # if the user has collected a bullet power-up that is still active
        # then bullet damage will be increased
        if len(self.bulletPowerUps) != 0:
            self.bulletDmg = 2
        else:
            self.bulletDmg = 1

        # checks if the player is dead and if they are, set the draw handler to
        # display the game over screen and set the key down handler so that the
        # user can only press certain keys to do certain actions on the game
        # over screen
        if self.player.isDead():
            timerStop(self.player.timer)

            for powerup in self.powerUps:
                self.powerUps.remove(powerup)

            for enemy in self.enemies:
                self.enemies.remove(enemy)

            for bullet in self.bullets:
                self.bullets.remove(bullet)

            for explosion in self.explosions:
                self.explosions.remove(explosion)

            self.explosions.append(ExplosionAnimation(self.player.pos, 1))
            self.player.pos = Vector(-50, -50)
            frame.set_draw_handler(self.gameOver)
            frame.set_keydown_handler(self.keyboard.restartKeyDown)

    # safely stops all timers
    def stopTimers(self):
        timerStop(self.player.timer)
        timerStop(self.level.levelTimer)

        for bulletPowerUp in self.bulletPowerUps:
            timerStop(bulletPowerUp.timer)

        for shieldPowerUp in self.shieldPowerUps:
            timerStop(shieldPowerUp.timer)

        for explosion in self.explosions:
            timerStop(explosion.timer)

    # function used to display the game over screen
    # displays the number of points obtained during playthrough
    def gameOver(self, canvas):
        frame.set_keydown_handler(self.keyboard.disable)
        if len(self.explosions) != 0:
            for explosion in self.explosions:
                if explosion.current[0] == 8 and explosion.current[1] == 8:
                    timerStop(explosion.timer)
                    self.explosions.remove(explosion)
                else:
                    explosion.nextFrame()

                explosion.draw(canvas)
        else:
            if self.gameOverSizeDims[0] < self.width and self.gameOverSizeDims[1] < self.height:
                canvas.draw_image(self.sprites["gameOverScreen"],
                                  (self.sprites["gameOverScreen"].get_width() / 2,
                                   game.sprites["gameOverScreen"].get_height() / 2),
                                  (self.sprites["gameOverScreen"].get_width(),
                                   self.sprites["gameOverScreen"].get_height()),
                                  (self.width / 2, self.height / 2),
                                  (self.gameOverSizeDims[0], self.gameOverSizeDims[1]))
                self.gameOverSizeDims[0] += 5
                self.gameOverSizeDims[1] += self.gameOverDimsScale
            else:
                frame.set_keydown_handler(self.keyboard.restartKeyDown)
                canvas.draw_image(self.sprites["gameOverScreen"],
                                  (self.sprites["gameOverScreen"].get_width() / 2,
                                   game.sprites["gameOverScreen"].get_height() / 2),
                                  (self.sprites["gameOverScreen"].get_width(),
                                   self.sprites["gameOverScreen"].get_height()),
                                  (self.width / 2, self.height / 2),
                                  (self.width, self.height))
                canvas.draw_text("Points: " + str(round(self.player.points)), (0, 15), 20, "White")
                canvas.draw_text("Press any key to continue",
                                 (game.width / 2 - (frame.get_canvas_textwidth("Press Space to play again", 25) / 2),
                                  700),
                                 25, "White")

        # checks whether the user has chosen to restart
        if self.keyboard.restart:
            frame.set_keydown_handler(self.keyboard.disable)
            frame.set_mouseclick_handler(self.mouse.mainMenu)
            self.level.restart()

    # draw method for the main game
    # makes the clock tick, calls the update function in interaction and draws all
    # entities on the screen (player, explosions, enemies and bullets)
    def draw(self, canvas):
        self.background.drawBack(canvas)
        self.player.draw(canvas)

        for powerup in self.powerUps:
            powerup.draw(canvas)

        for explosion in self.explosions:
            explosion.draw(canvas)

        for enemy in self.enemies:
            enemy.draw(canvas)

        for bullet in self.bullets:
            bullet.draw(canvas)

            # for each bullet, check if it is in bounds otherwise remove it
            # removes redundant bullets flying off screen
            if not bullet.inBounds():
                self.bullets.remove(bullet)

        # draws the health and points
        # enemies is a temporary thing used in testing that will most likely be
        # removed from the main game
        canvas.draw_text("Health: " + str(self.player.health), (0, 15), 20, "Lime")
        canvas.draw_text("Points: " + str(round(self.player.points)), (0, 35), 20, "Lime")
        canvas.draw_text("Enemies: " + str(len(self.enemies)), (0, 55), 20, "Yellow")

        game.level.baseLevel(canvas)

    # draw function for the start screen
    def startScreen(self, canvas):
        frame.set_mouseclick_handler(self.mouse.mainMenu)
        frame.set_keydown_handler(self.keyboard.disable)
        canvas.draw_image(self.sprites["startScreen"],
                          (self.sprites["startScreen"].get_width() / 2, game.sprites["startScreen"].get_height() / 2),
                          (self.sprites["startScreen"].get_width(), self.sprites["startScreen"].get_height()),
                          (game.width / 2, game.height / 2),
                          (game.width, game.height))

    def helpScreen(self, canvas):
        frame.set_keydown_handler(self.keyboard.disable)
        canvas.draw_image(self.sprites["helpScreen"],
                          (self.sprites["helpScreen"].get_width() / 2, game.sprites["helpScreen"].get_height() / 2),
                          (self.sprites["helpScreen"].get_width(), self.sprites["helpScreen"].get_height()),
                          (game.width / 2, game.height / 2),
                          (game.width, game.height))

    # safely closes all timers before ending the game
    def endGame(self):
        self.stopTimers()
        frame.stop()


game = Game()

# creates frame and sets starting draw and key down handlers
frame = simplegui.create_frame("Group project", game.width, game.height)
frame.set_draw_handler(game.startScreen)

# text on the side of the screen
frame.add_label("Controls:")
frame.add_label("W - Forwards")
frame.add_label("A - Left")
frame.add_label("S - Backwards")
frame.add_label("D - Right")
frame.add_label("Click - Shoot")
frame.add_label("")
frame.add_label("")
# button that can be used to exit or start the game
frame.add_button("Exit", game.endGame, 100)

frame.start()