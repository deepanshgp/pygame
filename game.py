import sys
import math
import random
import os

import pygame
import pygame.gfxdraw

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy , DashEnemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('ninja game')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
            'font': pygame.font.Font('data/images/font/upheavtt.ttf', 16),
        }
        font_path = os.path.join('data', 'images', 'font', 'upheavtt.ttf')
        self.assets['font'] = pygame.font.Font(font_path, 32)

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }
        
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.2)

        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)
        self.level = 0
        self.load_level(self.level)
        
        self.screenshake = 0

        # Initialize database
        from scripts.database import HighScoreDB
        self.db = HighScoreDB()
        
        # Score system
        self.score = 0
        self.high_score, self.high_score_level = self.db.get_high_score()  # Load from database
        
        self.combo = 0
        self.combo_timer = 0
        self.combo_multiplier = 1
        self.last_kill_time = 0
        
        # Load high score from file
        self.load_high_score()
        
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        #this resets the character state on level change    
    
        self.player.velocity = [0,0]
        self.player.dashing  = 0
        self.player.air_time = 0
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            elif spawner['variant'] == 1:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
            elif spawner['variant'] == 2:  # New dashing enemy
                self.enemies.append(DashEnemy(self, spawner['pos'], (8, 15)))
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30   

    def load_high_score(self):
        """Load high score from file"""
        try:
            with open('data/high_score.txt', 'r') as f:
                self.high_score = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            self.high_score = 0
            
    def save_high_score(self):
        """Save high score to file"""
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open('data/high_score.txt', 'w') as f:
                    f.write(str(self.high_score))
            except:
                pass  # Silently fail if can't save
    
    def add_score(self, points, enemy_type="enemy"):
        """Add points to score with combo system"""
        current_time = pygame.time.get_ticks()
        
        # Combo system: if kills are close together, increase multiplier
        if current_time - self.last_kill_time < 2000:  # 2 second window
            self.combo += 1
            self.combo_timer = 180  # 3 seconds at 60 FPS
            self.combo_multiplier = min(5, 1 + self.combo // 3)  # Max 5x multiplier
        else:
            self.combo = 1
            self.combo_multiplier = 1
            self.combo_timer = 180
            
        self.last_kill_time = current_time
        
        # Calculate final points with multiplier
        final_points = points * self.combo_multiplier
        
        # Bonus points for different enemy types
        if enemy_type == "dash_enemy":
            final_points = int(final_points * 1.5)  # 50% more for dashing enemies
            
        self.score += final_points
        
        # Create score popup effect
        self.create_score_popup(final_points, self.combo_multiplier)
        
        return final_points
    
    def create_score_popup(self, points, multiplier):
        """Create floating score text at player position"""
        # We'll store popups in a list and render them
        if not hasattr(self, 'score_popups'):
            self.score_popups = []
        
        popup = {
            'text': f'+{points}',
            'pos': [self.player.pos[0], self.player.pos[1] - 20],
            'timer': 60,  # 1 second at 60 FPS
            'color': (255, 255, 0) if multiplier > 1 else (255, 255, 255),
            'size': 8 + (multiplier * 2)
        }
        self.score_popups.append(popup)

    def render_score_popups(self):
        """Render floating score popups"""
        if hasattr(self, 'score_popups'):
            for popup in self.score_popups[:]:  # Use copy for safe iteration
                popup['timer'] -= 1
                popup['pos'][1] -= 0.5  # Float upward
                
                # Create font for this popup
                try:
                    font = pygame.font.Font(None, popup['size'])
                    text_surface = font.render(popup['text'], True, popup['color'])
                    
                    # Calculate position with scroll offset
                    render_pos = (
                        popup['pos'][0] - self.scroll[0] - text_surface.get_width() // 2,
                        popup['pos'][1] - self.scroll[1]
                    )
                    
                    self.display.blit(text_surface, render_pos)
                    
                except:
                    pass
                
                # Remove expired popups
                if popup['timer'] <= 0:
                    self.score_popups.remove(popup)
    
    def update_combo(self):
        """Update combo timer"""
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0
            self.combo_multiplier = 1

    def render_score_ui(self, surface):
        """Render score, combo, and high score on screen with dynamic font scaling"""

        # Base size for reference (assuming your base surface is 320x240)
        base_width = 320
        scale_factor = self.display.get_width() / base_width

        # Dynamically scale font size
        scaled_font_size = int(24 * scale_factor)
        small_scaled_font_size = int(18 * scale_factor)

        # Here use a try except if for some reason our font does not exist or fail to load
        try:
            font = pygame.font.Font('font/Upheavtt.ttf', scaled_font_size)
            small_font = pygame.font.Font('font/Upheavtt.ttf', small_scaled_font_size)
        except Exception as e:
            print("Font load failed:", e)
            font = pygame.font.Font(None, scaled_font_size)
            small_font = pygame.font.Font(None, small_scaled_font_size)

        # Score display
        score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
        self.display.blit(score_text, (10, 10))

        # High score
        high_score_text = small_font.render(f'High: {self.high_score}', True, (255, 255, 255))
        self.display.blit(high_score_text, (5, 10 + score_text.get_height()))

        # Combo display 
        if self.combo > 1:
            combo_color = (
                min(255, 100 + self.combo * 20),  # R
                min(255, 200 - self.combo * 10),  # G  
                min(255, 100 + self.combo * 15)   # B   
            )

            combo_text = font.render(f'COMBO x{self.combo_multiplier}!', True, combo_color)
            combo_rect = combo_text.get_rect(topright=(self.display.get_width() - 5, 5))
            self.display.blit(combo_text, combo_rect)

    def create_blurred_display(self):
        """Create a blurred version of the current display """
        try:
            # Take a snapshot of the current display
            display_snapshot = self.screen.copy()
            
            # SIMPLE BLUR: Scale down and scale up
            # Scale down to 1/4 size
            small_width = display_snapshot.get_width() // 4
            small_height = display_snapshot.get_height() // 4
            small_size = (max(1, small_width), max(1, small_height))
            
            # Scale down
            small_surface = pygame.transform.scale(display_snapshot, small_size)
            # Scale back up to create blur effect
            blurred_surface = pygame.transform.scale(small_surface, display_snapshot.get_size())
            
            # Add dark overlay for better text readability
            dark_overlay = pygame.Surface(blurred_surface.get_size(), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 100))  # Semi-transparent black
            blurred_surface.blit(dark_overlay, (0, 0))
            
            print("Blur created successfully")  # Debug
            return blurred_surface
            
        except Exception as e:
            print(f"Blur failed: {e}")
            # Return the original display instead of blue screen
            return self.display.copy()

    def show_high_scores(self):
        """Show high scores screen with blurred display background"""
        print("Showing high scores...")  # Debug
        
        # Create blurred version of the entire current display
        blurred_bg = self.create_blurred_display()
        
        # Use the blurred background
        self.display.blit(blurred_bg, (0, 0))
        
        # Render the high scores UI on top
        self.render_high_scores_ui()
        
        # Update screen
        self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
        pygame.display.update()
        
        # Wait for continue input
        self.wait_for_continue_input()

    def render_high_scores_ui(self):
        """Simple fixed positioning for 320x240 display"""
        # Get high scores from database
        top_scores = self.db.get_top_scores(3) if self.db else []
        
        # Font setup for 320x240
        try:
            font = pygame.font.Font(None, 16)
            title_font = pygame.font.Font(None, 24)
            big_font = pygame.font.Font(None, 32)
        except:
            font = pygame.font.SysFont('arial', 16)
            title_font = pygame.font.SysFont('arial', 24)
            big_font = pygame.font.SysFont('arial', 32)
        
        center_x = 160  # Fixed center for 320 width
        
        # Clear any existing content by redrawing the blurred background
        blurred_bg = self.create_blurred_display()
        self.display.blit(blurred_bg, (0, 0))
        
        # Title
        title = big_font.render('GAME OVER', True, (255, 255, 0))
        title_rect = title.get_rect(center=(center_x, 30))
        
        # Title background
        title_bg = pygame.Surface((title_rect.width + 20, title_rect.height + 10), pygame.SRCALPHA)
        title_bg.fill((0, 0, 0, 0))
        title_bg_rect = title_bg.get_rect(center=(center_x, 30))
        self.display.blit(title_bg, title_bg_rect)
        self.display.blit(title, title_rect)
        
        # Current session info
        current_score = title_font.render(f'Score: {self.score}', True, (255, 255, 255))
        current_level = title_font.render(f'Level: {self.level}', True, (200, 200, 255))
        
        current_score_rect = current_score.get_rect(center=(center_x, 60))
        current_level_rect = current_level.get_rect(center=(center_x, 85))
        
        self.display.blit(current_score, current_score_rect)
        self.display.blit(current_level, current_level_rect)
        
        # High scores list
        scores_title = title_font.render('TOP SCORES', True, (255, 200, 0))
        scores_title_rect = scores_title.get_rect(center=(center_x, 120))
        self.display.blit(scores_title, scores_title_rect)
        
        # Display top scores
        if top_scores:
            for i, (score, level, date) in enumerate(top_scores):
                score_y = 140 + (i * 25)
                
                # Highlight current score
                if score == self.score and level == self.level:
                    color = (0, 255, 255)
                else:
                    color = (255, 255, 255)
                    
                score_text = font.render(f'{i+1}. {score} (Level {level})', True, color)
                score_rect = score_text.get_rect(center=(center_x, score_y))
                self.display.blit(score_text, score_rect)
        else:
            no_scores = font.render('No high scores yet!', True, (200, 200, 200))
            no_scores_rect = no_scores.get_rect(center=(center_x, 160))
            self.display.blit(no_scores, no_scores_rect)
        
        # Instructions
        instructions = font.render('Press SPACE to continue', True, (200, 200, 100))
        instructions_rect = instructions.get_rect(center=(center_x, 220))
        self.display.blit(instructions, instructions_rect)
        
        # New high score celebration
        is_new_high_score = (self.db and self.score > 0 and 
                        self.score == self.high_score and 
                        self.level == self.high_score_level)
        
        if is_new_high_score:
            celebration = title_font.render('NEW HIGH SCORE!', True, (255, 50, 50))
            celebration_rect = celebration.get_rect(center=(center_x, 110))
            self.display.blit(celebration, celebration_rect)

    def wait_for_continue_input(self):
        """Wait for user to press space to continue"""
        waiting = True
        is_new_high_score = (self.db and self.score > 0 and 
                        self.score == self.high_score and 
                        self.level == self.high_score_level)
        
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        waiting = False
            
            # Pulsing animation for new high score
            if is_new_high_score:
                current_time = pygame.time.get_ticks()
                pulse = (current_time // 200) % 2
                
                center_x = self.display.get_width() // 2
                scores_y = 150
                celebration_y = scores_y - 20
                
                # Redraw celebration with pulsing color
                celebration_bg = pygame.Surface((250, 35), pygame.SRCALPHA)
                celebration_color = (255, 255, 0, 200) if pulse else (255, 50, 50, 180)
                celebration_bg.fill(celebration_color)
                celebration_bg_rect = celebration_bg.get_rect(center=(center_x, celebration_y))
                
                # Clear the celebration area by redrawing the blurred background
                self.display.blit(self.create_blurred_display(), celebration_bg_rect, celebration_bg_rect)
                
                # Redraw celebration
                self.display.blit(celebration_bg, celebration_bg_rect)
                celebration = pygame.font.Font(None, 24).render('NEW HIGH SCORE!', True, (255, 255, 255))
                celebration_rect = celebration.get_rect(center=(center_x, celebration_y))
                self.display.blit(celebration, celebration_rect)
                
                # Update screen
                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
                pygame.display.update()
            
            self.clock.tick(60)
            
        
    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        self.sfx['ambience'].play(-1)
        while True:
            self.display.blit(self.assets['background'], (0, 0))
            # Update combo system
            self.update_combo()
            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level += 1
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1
            
            if self.dead:
                self.dead += 1
                #This prevents the game from going into next level on death
                if self.dead == 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    # Save high score to database if it's a new record
                    if self.score > self.high_score:
                        self.db.save_high_score(self.score, self.level)
                        
                        self.high_score = self.score
                        self.high_score_level = self.level
                    # Show high scores screen
                    self.show_high_scores()
                    self.load_level(self.level)
                    self.score = 0  # Reset score after saving
                    self.combo = 0
                    self.combo_timer = 0
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)
            
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.movement[0] = True
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.movement[1] = True
                    if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                        #self.player.jump()
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key in (pygame.K_x, pygame.K_k):
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.movement[0] = False
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.movement[1] = False

            # RENDER SCORE UI 
            self.render_score_ui(self.screen)
            self.render_score_popups()
            
            if self.transition:
                #Holy Resource intensive we making surface on surface crazy
                #used Alpha keying instead of color keying because it is smoother 
                
                transition_surf = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
                radius = max(0, 300 - abs(self.transition)*8) #had 30 instead of 300 here making it choppy because long jumps in radius int
                #also made ts cleaner because earlier it looked like a pattern code
                center = (self.display.get_width()) // 2, (self.display.get_height()) // 2
                transition_surf.fill((0, 0, 0, 255))
                pygame.draw.circle(transition_surf, (0,0,0,0), center, int(radius))
                self.display.blit(transition_surf, (0,0))
                

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)
            self.render_score_ui(self.screen)
            pygame.display.update()
            self.clock.tick(60)

Game().run()