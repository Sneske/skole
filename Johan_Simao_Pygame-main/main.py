import pygame
from pygame.locals import *
import random
from statemachine import StateMachine, State
import sys
import math

class GameManagerMachine(StateMachine):
    main_menu = State(initial=True)
    game_active = State()
    game_over = State()
    game_ended = State()

    start_game = main_menu.to(game_active)

    end_game = game_active.to(game_over)

    restart_game = game_over.to(game_active)

    exit_game = (
        main_menu.to(game_ended)
        | game_active.to(game_ended)
        | game_over.to(game_ended)
        )

    def on_enter_main_menu(self):
        menu(self)

    def on_enter_game_active(self):
        main(self)

    def on_enter_game_over(self):
        menu_two(self)

    def on_enter_game_ended(self):
        pygame.quit()
        sys.exit()


class Constants:
    def __init__(self):

        #højde og brede på vinduet
        self.vinduebrede = 1500  
        self.vinduehojde = 800  

        # konstanter på flyve mekanismen

        # hvor hurtigt karateren stiger og falder
        self.tyndekraft = 0.25  
        self.opdrift = -0.2  

        # den maksimale hastighed karakteren kan stige og falde
        self.maxstige = -6 
        self.maxfalde = 6 

        
        self.banehojde = 100  
        self.floor_y = self.vinduehojde - self.banehojde  

        self.bgh = 2  # hastighed på baggrunden


class Character:
    """ 
    Denne class har funktioner, der tjekker om en af knapperne bliver trykket på. 
    Hvis en af knapperne bliver trykket på, vil figurens hastighed blive plusset med opdrift konstanten alt imens den tjekker om den ikke kommer over det maximale.
    Ellers vil den blive plusset med konstanten for tyndekraften og på samme vis vil den ikke komme over det maximale

    Funktioner tjekker også om figuren ikke falder i intetheden, ved at angive hvor vægge og bane er.

    Andre funktionen der tilhøre vores figuren kan også findes her.
    """

    def __init__(self, constants):
        self.health = 3

        self.bullets = 100  
        self.reload_timer = 0 

        self.images = [
            pygame.image.load("figurv2/R1.png").convert_alpha(),
            pygame.image.load("figurv2/R2.png").convert_alpha(),
            pygame.image.load("figurv2/R3.png").convert_alpha(),
            pygame.image.load("figurv2/R4.png").convert_alpha(),
            pygame.image.load("figurv2/R5.png").convert_alpha(),
            pygame.image.load("figurv2/R6.png").convert_alpha(),
            pygame.image.load("figurv2/R7.png").convert_alpha(),
            pygame.image.load("figurv2/R8.png").convert_alpha(),
            pygame.image.load("figurv2/R9.png").convert_alpha(),
        ]


        self.current_image = 0  # Starter med det første billede
        self.image = self.images[self.current_image]  # Det aktuelle billede til visning


        self.image.set_colorkey((0, 0, 0))  #fjerner den baggrunden ved at bruge samme farve som baggrunden
        self.karakterpos = 65
        self.rect = self.image.get_rect(topleft=(self.karakterpos, constants.floor_y - self.image.get_height()))
        self.hastighed = 0



    def update(self, keys, constants):

        self.current_image += 1
        if self.current_image >= len(self.images):
            self.current_image = 0
        self.image = self.images[self.current_image]

        """ hvis w eller pil op tasten bliver trykket vil figuren bevæge sig op ad"""
        if keys[K_UP] or keys[K_w]:
            self.hastighed += constants.opdrift
            if self.hastighed < constants.maxstige:
                self.hastighed = constants.maxstige
        else:
            self.hastighed += constants.tyndekraft
            if self.hastighed > constants.maxfalde:
                self.hastighed = constants.maxfalde

        self.rect.y += self.hastighed

        if self.rect.top < 0:
            self.rect.top = 0
            self.hastighed = 0
        elif self.rect.bottom > constants.floor_y:
            self.rect.bottom = constants.floor_y
            self.hastighed = 0

        if self.reload_timer > 0:
            self.reload_timer -= 1
            if self.reload_timer == 0:
                self.bullets = 100  
        elif self.bullets == 0:
            self.reload_timer = 300  

    def can_shoot(self):
        if self.bullets > 0 and self.reload_timer == 0:
            self.bullets -= 1
            return True
        return False


    def take_damage(self, damage):
        self.health -= damage

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def reloadtid(self, screen):
        if self.reload_timer > 0:
            sektilbage = self.reload_timer // 60
            font = pygame.font.Font(None, 36)
            text = font.render(f'Reloading: {str(sektilbage + 1)}', True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen.get_width() - 100, 50))
            screen.blit(text, text_rect)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        self.reloadtid(screen)

""" funktionen der laver banen figuren går på."""

def make_pavements(screen, constants):
    pavement_color = (192, 192, 192)  
    pygame.draw.rect(screen, pavement_color, (0, constants.floor_y, constants.vinduebrede, constants.banehojde))

""" liv bar """

def make_healthbar(screen, character):
        pos_x = 50
        pos_y = 50
        width = 299
        height = 30
        outline_width = 3
        margin = 2

        health_point_width = math.floor((width - outline_width * 2 - margin * 4) / 3) #Skal resultere i int for at virke, ellers bliver health-baren en skæv
        health_point_height = height - margin * 2 - outline_width * 2
        pygame.draw.rect(screen, (0, 100, 255), (pos_x, pos_y, width, height), outline_width)

        pos_x += outline_width + margin
        
        for x in range(character.health):
            pygame.draw.rect(screen, (230, 60, 60), (pos_x, pos_y + outline_width + margin, health_point_width, health_point_height))
            pos_x += health_point_width + margin


"""Background classen er baggrunden der kører bagerst i spillet. Det er et billede der køre i ring igen og igen"""

class Background:
    def __init__(self, image_path, fart):
        self.image = pygame.image.load(image_path).convert()
        self.fart = fart
        self.x1 = 0
        self.x2 = self.image.get_width()

    def update_and_draw(self, screen):
        self.x1 -= self.fart
        self.x2 -= self.fart

        if self.x1 <= -self.image.get_width():
            self.x1 = self.image.get_width()
        if self.x2 <= -self.image.get_width():
            self.x2 = self.image.get_width()

        screen.blit(self.image, (self.x1, 0))
        screen.blit(self.image, (self.x2, 0))

class Entity():
    """Class der kan tegne sig selv på en surface"""
    def __init__(self, pos_x, pos_y, sprite):
        """Initialiserer Entity med en position fra venstre øverste hjørne og en sprite"""
        self.pos_x = pos_x
        self.pos_y = pos_y

        self.sprite = sprite
        self.sprite.set_colorkey((0,255,0))
        self.sprite_rect = self.sprite.get_rect(topleft=(self.pos_x, self.pos_y))


    def draw_self(self, screen):
        """Tegner spriten ved position"""
        screen.blit(self.sprite, self.sprite_rect)


class Button(Entity):
    """Class der fungerer som knap, og arver fra Entity"""
    def __init__(self, pos_x, pos_y, sprite, id):
        """Initialiseres med et id, størrelse og position defineret fra midten af knappen"""
        self.id = id
        self.width = sprite.get_width()
        self.height = sprite.get_height()
        pos_x = pos_x - (self.width / 2)
        pos_y = pos_y - (self.height / 2)

        Entity.__init__(self, pos_x, pos_y, sprite)

    def check_click(self, mouse_pos):
        """Tjekker om museklik var på knappen"""
        if(self.sprite_rect.collidepoint(mouse_pos)):
            return True
        return False


class Enemy(Entity):
    """Class der fungerer som template for alle enemies. Arver fra Entity"""
    def __init__(self, pos_x, pos_y, vel_x, vel_y, health, damage, sprite):
        """Instantieres med hastighed, liv, skade og hvorvidt specifik instans har skadet spiller"""
        self.vel_x = vel_x
        self.vel_y = vel_y

        self.health = health
        self.damage = damage

        self.has_damaged_player = False

        Entity.__init__(self, pos_x, pos_y, sprite)

    def delete_self(self):
        """Fjerner sig selv fra liste over fjender, så den kan blive slettet"""
        enemies_list.remove(self)

    def move_self(self):
        """Rykker sig selv over skærmen"""
        self.sprite_rect.x += self.vel_x
        self.sprite_rect.y += self.vel_y

    def collision(self, character):
        """Tjekker for kollision med spilleren. Skader spiller hvis sandt, og ikke har skadet spiller allerede"""
        if(pygame.Rect.colliderect(self.sprite_rect, character.rect) and not self.has_damaged_player):
            character.take_damage(self.damage)
            self.has_damaged_player = True
            return True
        return False

    def take_damage(self, damage_taken):
        """Tager skade når skudt af spiller. Fjerner objekt hvis det mister alt sit liv"""
        self.health -= damage_taken
        if self.health <= 0:
            self.delete_self()

    def update(self, character):
        """Enemy'ens handlinger hvert tick"""
        self.move_self()
        self.collision(character)

        if(self.sprite_rect.x < 0 - self.sprite.get_width()): #Fjerner objekt, hvis objekt er ude af skærmen
            self.delete_self()


class MissileEnemy(Enemy):
    """Implementering af Enemy class"""
    def __init__(self, constants):
        """Initialiserer missilet med valgte v;rdier"""
        Enemy.__init__(self, constants.vinduebrede, random.randrange(0, constants.vinduehojde - constants.banehojde - 100), -7, 0, 1, 1, pygame.image.load("enemies/missile.png").convert_alpha())

    def update(self, character):
        """Overrider update-method, saadan at missil slettes naar det rammer spilleren"""
        self.move_self()
        if self.collision(character):
            self.delete_self()

        if(self.sprite_rect.x < (0 - self.sprite.get_width())):
            self.delete_self()
        



class LaserEnemy(Enemy):
    def __init__(self, constants):
        """Initialiserer LaserEnemy og definerer laseren retning, farve, bredde"""
        Enemy.__init__(self, constants.vinduebrede + 100, constants.vinduehojde / 2, 0, 0, 10000, 1, pygame.image.load("enemies/missile.png").convert_alpha())
        self.ticks_active = 0
        self.color = (0,0,0)
        self.laser_width = 2
        self.line = ((0,0),(0,0))

    def draw_self(self, screen):
        """Overrider draw_self, da maaden laseren tegnes paa er anderledes end andre objekter"""
        self.line = pygame.draw.line(screen, self.color, (self.pos_x, self.pos_y),(self.target_x, self.target_y), self.laser_width)

    def collision(self, character):
        """Overrider collision, da laseren er et line frem for rect"""
        if(character.rect.clipline((self.pos_x, self.pos_y),(self.target_x, self.target_y)) and not self.has_damaged_player):
            character.take_damage(self.damage)
            self.has_damaged_player = True

    def update(self, character):
        self.ticks_active += 1

        if(self.ticks_active < 180):
            self.color = (60, 60, 255)
            self.laser_width = (2)

            self.target_x = character.rect.x + 20 - (self.pos_x - character.rect.x)
            self.target_y = character.rect.y + 35 - (self.pos_y - character.rect.y)

        elif(self.ticks_active >= 180 and self.ticks_active < 240):
            self.color = (60, 255, 60)

        elif(self.ticks_active >= 240 and self.ticks_active < 520):
            self.color = (255, 60, 60)
            self.laser_width = 20
            self.collision(character)
        else:
            self.delete_self()


class Crusher(Enemy):
    def __init__(self, constants):
        self.vinduehojde = constants.vinduehojde
        self.vinduebredde = constants.vinduebrede
        Enemy.__init__(self, self.vinduebredde, self.vinduehojde, -3, -4, 10000, 1, pygame.image.load("enemies/crusher2.png").convert_alpha())

    def update(self, character):
        if(self.sprite_rect.y <= (self.vinduehojde - self.sprite.get_height())):
            self.vel_y = 3
        elif(self.sprite_rect.y >= self.vinduehojde):
            self.vel_y = -3

        self.move_self()
        self.collision(character)

        if(self.sprite_rect.x < (0 - self.sprite.get_width())):
            self.delete_self()


class Weapon(Entity):
    """ funktionen arver fra positionen og sprite fra enitity classen """
    def __init__(self, pos_x, pos_y, sprite, move_delay=300):
        super().__init__(pos_x, pos_y, sprite)  
        self.collected = False
        self.move_delay = move_delay  
        self.moving = False

    """ våbnet ligger på koordinaterne 1000, 1000 og går stille og roligt mod spillerens possition. hvor hurtigt våbnet kommer mod figuren kan indstilles på move_delay variablen"""
    def move_towards_character(self, character):
        if self.moving:
            direction_x = character.rect.centerx - self.sprite_rect.centerx
            direction_y = character.rect.centery - self.sprite_rect.centery
            distance = max(abs(direction_x), abs(direction_y))
            if distance != 0:
                self.vel_x = direction_x / distance
                self.vel_y = direction_y / distance
                self.pos_x += self.vel_x
                self.pos_y += self.vel_y
                self.sprite_rect.x = int(self.pos_x)
                self.sprite_rect.y = int(self.pos_y)

    def update(self, character):
        if not self.collected:
            if self.move_delay > 0:
                self.move_delay -= 1
            else:
                self.moving = True
                self.move_towards_character(character)

    """når figuren har samlet våbnet op vil figuren kunne skyde"""
    def collect(self, character):
        if pygame.Rect.colliderect(self.sprite_rect, character.rect) and not self.collected:
            self.collected = True
            return True
        return False

class Projectile(Entity):
    def __init__(self, pos_x, pos_y, vel_x, vel_y, health=1):  
        super().__init__(pos_x, pos_y, pygame.Surface((10, 5)))
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.health = health
        self.sprite.fill((255, 255, 0)) 

    def update(self, enemies):
        self.pos_x += self.vel_x
        self.pos_y += self.vel_y
        self.sprite_rect.x = int(self.pos_x)
        self.sprite_rect.y = int(self.pos_y)

        for enemy in enemies:
            if self.sprite_rect.colliderect(enemy.sprite_rect):
                enemy.take_damage(0.05)  #hvor meget et skud kan skade. et skud med 1.00 skade vil dræbe raketen med det samme.
                self.health -= 1  
                if self.health <= 0:
                    return True  
                
        if self.pos_x > 1500 or self.pos_y < 0 or self.pos_y > 800:
            return True
        return False


"""
i main funktionen bliver vores objekter såsom forhindring og våbnet sat ind i spillet. 
"""


def main(game_manager):
    background = Background("background2.png", constants.bgh)
    character = Character(constants)

    weapon_collected = False

    weapon = Weapon(1000, 1000 , pygame.image.load("3004.png").convert_alpha())
    projectiles = []

    global enemies_list
    enemies_list = []
    enemy_spawned_ticks = 0
    laser_spawned_ticks = 0
    crusher_spawned_ticks = 0
    
    running = True

    paused = False

    enemies_list.append(Crusher(constants))

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                game_manager.exit_game()
                running = False
            
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    paused = True

        keys = pygame.key.get_pressed()
        weapon.update(character)

        """ den tjekker om våbnet er blevet samlet om i variablen i character classen """
        if weapon.collect(character):
            weapon_collected = True 

        """ her bliver skuddene sat in på skaermen hvis våbnet er blevet taget og hvis man trykker på mellemrum"""
        if weapon_collected and keys[K_SPACE]:
            if character.can_shoot():
                projectiles.append(Projectile(character.rect.centerx + 20, character.rect.centery, 10, 0))  
        for projectile in projectiles[:]: 
            if projectile.update(enemies_list):
                projectiles.remove(projectile)
        

        for projectile in projectiles:
            projectile.draw_self(screen)

        
        enemy_spawned_ticks += 1
        laser_spawned_ticks += 1
        crusher_spawned_ticks += 1

        if(len(enemies_list) < 10 and enemy_spawned_ticks > 30):
           enemies_list.append(MissileEnemy(constants))
           enemy_spawned_ticks = 0

        if(laser_spawned_ticks > 1200):
           enemies_list.append(LaserEnemy(constants))
           laser_spawned_ticks = 0

        if(crusher_spawned_ticks > 800):
           enemies_list.append(Crusher(constants))
           crusher_spawned_ticks = 0

        for enemy in enemies_list:
            enemy.update(character)
        keys = pygame.key.get_pressed()
        character.update(keys, constants)

        if(character.health <= 0):
            running = False

        background.update_and_draw(screen)
        for enemy in enemies_list:
            enemy.draw_self(screen)
        make_pavements(screen, constants)
        character.draw(screen)
        make_healthbar(screen, character)
        
        if not weapon.collected:
            weapon.draw_self(screen)
        for projectile in projectiles:
            projectile.draw_self(screen)

        pygame.display.flip()
        clock.tick(60) 

        if(paused == True):
            menu_pause(game_manager)
            paused = False

    game_manager.end_game()

""" funktion der viser hovedmenuen når man kommer ind i spillet. Funktionen bruger statemachine som er diffineret i toppen af koden"""
def menu(game_manager):
    #img_path = "./AAAA.png"
    #game_manager._graph().write_png(img_path)
    Running = True

    button_list = []
    button_list.append(Button(constants.vinduebrede/2, constants.vinduehojde/2, pygame.image.load("buttons/start_game.png").convert_alpha(),1))
    button_list.append(Button(constants.vinduebrede/2, constants.vinduehojde/2 + 200, pygame.image.load("buttons/quit_game.png").convert_alpha(),2))

    while Running:
        for event in pygame.event.get():
            if event.type == QUIT:
                game_manager.exit_game()
                Running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in button_list:
                    if button.check_click(mouse_pos) == True:
                        if(button.id == 1):
                            game_manager.start_game()
                            Running = False
                        elif(button.id == 2):
                            game_manager.exit_game()
                            Running = False

        for button in button_list:
            button.draw_self(screen)
        pygame.display.flip()
        clock.tick(60) 

def menu_pause(game_manager):
    Running = True
    button_list = []
    button_list.append(Button(constants.vinduebrede/2, constants.vinduehojde/2, pygame.image.load("buttons/resume_game.png").convert_alpha(),1))
    button_list.append(Button(constants.vinduebrede/2, constants.vinduehojde/2 + 200, pygame.image.load("buttons/quit_game.png").convert_alpha(),2))

    while Running:
        for event in pygame.event.get():
            if event.type == QUIT:
                Running = False
                game_manager.exit_game()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    Running = False 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in button_list:
                    if button.check_click(mouse_pos) == True:
                        if(button.id == 1):
                            Running = False
                        elif(button.id == 2):
                            print(game_manager)
                            game_manager.exit_game()
                            pygame.quit()
                            sys.exit()
                            print("CALLED")
                            Running = False

        for button in button_list:
            button.draw_self(screen)
        pygame.display.flip()
        clock.tick(60) 


def menu_two(game_manager):
    Running = True
    button_list = []
    button_list.append(Button(constants.vinduebrede/2, constants.vinduehojde/2, pygame.image.load("buttons/restart_game.png").convert_alpha(),1))
    button_list.append(Button(constants.vinduebrede/2, constants.vinduehojde/2 + 200, pygame.image.load("buttons/quit_game.png").convert_alpha(),2))

    while Running:
        for event in pygame.event.get():
            if event.type == QUIT:
                Running = False
                game_manager.exit_game()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in button_list:
                    if button.check_click(mouse_pos) == True:
                        if(button.id == 1):
                            Running = False
                            game_manager.restart_game()
                        elif(button.id == 2):
                            Running = False
                            game_manager.exit_game()

        for button in button_list:
            button.draw_self(screen)
        pygame.display.flip()
        clock.tick(60) 

def game_ended():
    pygame.quit()

if __name__ == "__main__":
    constants = Constants()
    pygame.init()
    screen = pygame.display.set_mode((constants.vinduebrede, constants.vinduehojde))
    pygame.display.set_caption('flyve frank')
    clock = pygame.time.Clock()
    game_manager = GameManagerMachine()
