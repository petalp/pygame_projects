import pygame
import sys
from scripts.utilites import  load_images
from scripts.tiles import TileMap



RENDER_SCALE = 2.0

class Editor:
    def __init__(self) -> None:
        pygame.init()
        
        pygame.display.set_caption("Editor") 
        self.screen = pygame.display.set_mode((900, 700))
        self.display = pygame.Surface((300, 200))
        self.clock = pygame.time.Clock()
        self.assets = {
            "decor" : load_images("tiles/decor"), 
            "grass" : load_images("tiles/grass"), 
            "large_decor" : load_images("tiles/large_decor"), 
            "stone" : load_images("tiles/stone"),
            "spawners":load_images("tiles/spawners")    
        }
    
        
        self.movement = [False, False, False, False]
        
        
        self.tilemap = TileMap(self, tile_size=16)
        try:
            self.tilemap.load("map.json")
        except FileNotFoundError:
            pass
        
        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        
        #mouse click 
        self.left_clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = False
    
    def mouse_click(self, event):
        "Handles mouse interaction"
        #check for the mouse event
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.left_clicking = True
                if not self.ongrid:
                    self.tilemap.offgrid_tiles.append({'type':self.tile_list[self.tile_group], 'variant':self.tile_variant, 'pos':(self.mpos[0]+self.scroll[0], self.mpos[1]+self.scroll[1])})
            if event.button == 3:
                self.right_clicking = True
            if self.shift:
                if event.button == 4:
                    self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                if event.button == 5:
                    self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
            else:
                if event.button == 4:
                    self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                    self.tile_variant = 0
                if event.button == 5:
                    self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                    self.tile_variant = 0
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.left_clicking = False
            if event.button == 3:
                self.right_clicking = False
                
    def keyboard_clicks(self, event):
        "handles the keyboard interaction"         
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self.movement[0] = True
                if event.key == pygame.K_d:
                    self.movement[1] = True
                if event.key == pygame.K_w:
                    self.movement[2] = True
                if event.key == pygame.K_s:
                    self.movement[3] = True
                if event.key == pygame.K_g:
                    self.ongrid = not self.ongrid
                if event.key == pygame.K_o:
                    self.tilemap.save("map.json")
                if event.key == pygame.K_t:
                    self.tilemap.autotile()
                if event.key == pygame.K_LSHIFT:
                    self.shift = True
                     
        if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    self.movement[0] = False
                if event.key == pygame.K_d:
                    self.movement[1] = False
                if event.key == pygame.K_w:
                    self.movement[2] = False
                if event.key == pygame.K_s:
                    self.movement[3] = False
                if event.key == pygame.K_LSHIFT:
                    self.shift = False
                  
    def events(self, event):
        """Handle the entire event for the game  """
        if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
        #check for mouse event
        self.mouse_click(event=event)         
              
        #check for keyboard event
        self.keyboard_clicks(event=event)
    
    def grid_display(self, current_tile_img, tile_pos):
        "display the image on the grid system "
        if self.ongrid:
            self.display.blit(current_tile_img, (tile_pos[0]*self.tilemap.tile_size - self.scroll[0], tile_pos[1]*self.tilemap.tile_size - self.scroll[0]))
        else:
            self.display.blit(current_tile_img, self.mpos)
               
        if self.left_clicking and self.ongrid:
            self.tilemap.tilemap[str(tile_pos[0])+';'+str(tile_pos[1])] = {"type":self.tile_list[self.tile_group], "variant":self.tile_variant,'pos':tile_pos }
        if self.right_clicking:
            tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
            if tile_loc in self.tilemap.tilemap:
                del self.tilemap.tilemap[tile_loc]
            for tile in self.tilemap.offgrid_tiles.copy():
                tile_img = self.assets[tile['type']][tile['variant']]
                tile_r = pygame.Rect(tile['pos'][0]-self.scroll[0], tile['pos'][1]-self.scroll[1], tile_img.get_width(), tile_img.get_height())
                if tile_r.collidepoint(self.mpos):
                    self.tilemap.offgrid_tiles.remove(tile)
                                     
                    
    def image_displays(self):
        """displays all the images onto the screen """
        self.display.fill((0, 0, 0))
        self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
        self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
        
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        self.tilemap.render(self.display, offset=render_scroll)
        
        current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
        current_tile_img.set_alpha(100)
    
        self.mpos = pygame.mouse.get_pos()
        self.mpos = (self.mpos[0]/RENDER_SCALE, self.mpos[1]/RENDER_SCALE)
        tile_pos = (int((self.mpos[0]+self.scroll[0])//self.tilemap.tile_size), 
                    int((self.mpos[1]+self.scroll[1])//self.tilemap.tile_size))
        
        self.grid_display(current_tile_img=current_tile_img, tile_pos=tile_pos)
        
        
        self.display.blit(current_tile_img, (5, 5))
    
    def run(self):
        while True:
            self.image_displays() # display player image, enemy and tiles on the screen
        
            for event in pygame.event.get():
                self.events(event)   
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0,0))
            pygame.display.update()
            self.clock.tick(60)
            
Editor().run()
        
