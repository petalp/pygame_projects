#!/usr/bin/env python3

import pygame
import sys
import math
import random
import os

from scripts.entities import Player, Enemy
from scripts.utilites import load_image, load_images, Animation
from scripts.tiles import TileMap
from scripts.cloud import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self) -> None:
        pygame.init()
        
        pygame.display.set_caption("Ninja Game") 
        self.screen = pygame.display.set_mode((900, 700))
        self.display = pygame.Surface((300, 200), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((300, 200))
        self.clock = pygame.time.Clock()
        self.assets = {
            "decor" : load_images("tiles/decor"), 
            "grass" : load_images("tiles/grass"), 
            "large_decor" : load_images("tiles/large_decor"), 
            "stone" : load_images("tiles/stone"), 
            "player" : load_image("entities/player.png"),
            "background" : load_image("background.png"),
            "cloud" : load_images("clouds"),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run": Animation(load_images("entities/enemy/run"), img_dur=6),
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=6),
            "player/jump": Animation(load_images("entities/player/jump"), img_dur=6),
            "player/run": Animation(load_images("entities/player/run")),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
            "particle/leaf": Animation(load_images("particles/leaf"), img_dur=20),
            "particle/particle": Animation(load_images("particles/particle"), img_dur=20),
            'gun':load_image('gun.png'),
            'projectile':load_image('projectile.png'),
            }
        
        self.sfx = {
            "jump":pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash":pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit":pygame.mixer.Sound("data/sfx/hit.wav"),
            "shoot":pygame.mixer.Sound("data/sfx/shoot.wav"),
            "ambience":pygame.mixer.Sound("data/sfx/ambience.wav"),
        }
        self.sfx["ambience"].set_volume(0.2)
        self.sfx["shoot"].set_volume(0.4)
        self.sfx["hit"].set_volume(0.8)
        self.sfx["dash"].set_volume(0.3)
        self.sfx["jump"].set_volume(0.7)
        
        
        self.movement = [False, False]
        
        self.player = Player(self, (50, 50), (8 , 15))
        self.tilemap = TileMap(self, tile_size=16)
        self.cloud = Clouds(self.assets["cloud"], count=16)
        self.level = 0
        self.load_level(self.level)
        
        self.particles = []
        self.projectiles = []
        self.sparks = []
        self.screenshake = 0
        
        
    def load_level(self, map_id):
        self.tilemap.load('data/maps/'+str(map_id)+".json")
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)],keep=True):
            self.leaf_spawners.append(pygame.Rect(4+tree['pos'][0], 4+tree['pos'][1], 23, 13))
        
        self.enemy = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemy.append(Enemy(self, spawner['pos'], (8, 15)))
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
    
    def events(self, event):
        """Handle the entire event for the game  """
        if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.movement[0] = True
                if event.key == pygame.K_LEFT:
                    self.movement[1] = True
                if event.key == pygame.K_UP:
                    if self.player.jump():
                        self.sfx["jump"].play()
                if event.key == pygame.K_x:
                    self.player.dash()
        if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    self.movement[0] = False
                if event.key == pygame.K_LEFT:
                    self.movement[1] = False
                    
    def bullet_movement(self, render_scroll=(0, 0)):
        for projectile in self.projectiles.copy():
            projectile[0][0] += projectile[1]
            projectile[2] += 1
            img = self.assets['projectile']
            self.display.blit(img, (projectile[0][0]-img.get_width()/2-render_scroll[0], projectile[0][1]-img.get_height()/2 -render_scroll[1]))
            if self.tilemap.solid_rock(projectile[0]):
                self.projectiles.remove(projectile)
                for i in range(4):
                    self.sparks.append(Spark(projectile[0], random.random()-0.5+(math.pi  if projectile[1]>0 else 0), 2+random.random()))
            elif projectile[2] > 360:
                self.projectiles.remove(projectile)
            elif abs(self.player.dashing) < 50:
                if self.player.rect().collidepoint(projectile[0]):
                    self.projectiles.remove(projectile)
                    self.dead += 1
                    self.sfx["hit"].play()
                    self.screenshake = max(16, self.screenshake) 
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.sparks.append(Spark(self.player.rect().center, angle, 2+random.random()))
                        velocity = [math.cos(angle+math.pi)*speed*0.5, math.sin(angle+math.pi)*speed*0.5]
                        self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=velocity, frame=random.randint(0, 7)))           
    
    def spark_particle(self, render_scroll):
        
        for spark in self.sparks.copy():
            kill = spark.update()
            spark.render(self.display, offset=render_scroll)
            if kill:
                self.sparks.remove(spark) 
        
        display_mask = pygame.mask.from_surface(self.display)
        display_shilloutte = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0,0,0,0))
        
        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.display_2.blit(display_shilloutte, offset) 
                    
        for particle in self.particles.copy():
            kill = particle.update()
            particle.render(self.display, offset=render_scroll)
            if particle.type == 'leaf':
                particle.pos[0] += math.sin(particle.animation.frame*0.035)*0.3
            if kill:
                self.particles.remove(particle)
    
    def game_transition(self):
        
        #check if the enemy is dead to make a transition to the next level
        if not len(self.enemy):
            self.transition += 1
            if self.transition > 30:
                self.level = min(self.level+1, len(os.listdir('data/maps'))-1)
                self.load_level(self.level)
        if self.transition < 0:
            self.transition += 1
        
        #check if the player is dead to restart the level
        if self.dead:
            self.dead += 1
            if self.dead >= 10:
                self.transition = min(30, self.transition + 1)
            if self.dead > 40:
                self.load_level(self.level)
                
    def player_enemy_cloud(self, render_scroll):
        self.cloud.update()
        self.cloud.render(self.display_2, offset=render_scroll)
            
        self.tilemap.render(self.display, offset=render_scroll)
        
        for enemy in self.enemy.copy():
            kill = enemy.update(self.tilemap, (0, 0))
            enemy.render(self.display, offset=render_scroll)
            if kill:
                self.enemy.remove(enemy)
                
        if not self.dead:
            self.player.update(self.tilemap,(self.movement[0]-self.movement[1], 0))
            self.player.render(self.display, offset=render_scroll)
        
                        
    def image_displays(self):
        """displays all the images onto the screen """
        self.display.fill((0, 0, 0, 0))
        self.display_2.blit(self.assets['background'], (0, 0))
        self.screenshake = max(0, self.screenshake-1)
        
        #game transition
        self.game_transition()
                
        self.scroll[0] += (self.player.rect().centerx - self.display.get_width()/2 - self.scroll[0])/30
        self.scroll[1] += (self.player.rect().centery - self.display.get_height()/2 - self.scroll[1])/30
        
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        
        for rect in self.leaf_spawners:
            if random.random() * 49999< rect.width * rect.height:
                pos=(rect.x + random.random()*rect.width, rect.y+random.random()*rect.height)
                self.particles.append(Particle(self, "leaf", pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
                
        self.player_enemy_cloud(render_scroll=render_scroll)
        
        #bullet movement 
        self.bullet_movement(render_scroll=render_scroll)
        
        #bullet movement             
        self.spark_particle(render_scroll=render_scroll)
        
    
    def run(self):
        pygame.mixer.music.load("data/music.wav")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        
        self.sfx["ambience"].play(-1)
        
        while True:
            self.image_displays() # display player image, enemy and tiles on the screen
        
            for event in pygame.event.get():
                self.events(event)
        
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width()//2, self.display.get_height()//2), (30-abs(self.transition))*8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
            
            self.display_2.blit(self.display, (0, 0))
                
            screenshake_offset = (random.random()*self.screenshake-self.screenshake/2,random.random()*self.screenshake-self.screenshake/2)   
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)
            
Game().run()
        