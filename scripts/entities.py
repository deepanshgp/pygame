import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')
        
        self.last_movement = [0, 0]
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        
        self.walking = 0
        
    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 16):
                    if (self.flip and dis[0] < 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dis[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        elif random.random() < 0.02:
            self.walking = random.randint(30, 120)
        
        super().update(tilemap, movement=movement)
        
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                # ADD SCORING - Award points for killing regular enemy
                self.game.add_score(100, "enemy")
                return True
            
        dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        if (abs(dis[1]) < 24) and (abs(dis[0]) < 200):  # Player is within range
            if random.random() < 0.01:  # 1% chance every frame to shoot when player is in range
                if (self.flip and dis[0] < 0) or (not self.flip and dis[0] > 0):
                    self.game.sfx['shoot'].play()
                    x_offset = -7 if self.flip else 7
                    self.game.projectiles.append([[self.rect().centerx + x_offset, self.rect().centery], 
                                                -1.5 if self.flip else 1.5, 0])
                    for i in range(4):
                        angle = random.random() - 0.5 + (math.pi if self.flip else 0)
                        self.game.sparks.append(Spark(self.game.projectiles[-1][0], angle, 2 + random.random()))

        
            
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
    
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        input_dir  = movement[0]
        self.air_time += 1
        
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
            
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        #(((unsuccessfully))) implementing dash cancel 
        input_dir = movement[0]
        if self.dashing != 0:
            dash_dir = int(abs(self.dashing)/self.dashing)
            if input_dir != 0 and input_dir != dash_dir:
                self.dashing = 0
                self.velocity[0]
                #okay so I accidentally did a thing that instead of dash cancel, it launches you into the opposite direction instead lmao. I think it's pretty cool let's see if anyone actually notices it lmaoaoaoa, fun lil easter egg lol
                self.flip = input_dir

        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
                
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
                
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

class DashEnemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        
        self.walking = 0
        self.dashing = 0
        self.dash_cooldown = 0
        self.dash_range = 80  # Distance at which enemy will dash
        self.last_seen_player_pos = None
        
    def update(self, tilemap, movement=(0, 0)):
        player_pos = self.game.player.pos
        dis_to_player = (player_pos[0] - self.pos[0], player_pos[1] - self.pos[1])
        
        # Track player position when visible
        if abs(dis_to_player[1]) < 20:  # Player is at similar height
            self.last_seen_player_pos = player_pos.copy()
        
        # Dash behavior
        if self.dashing == 0 and self.dash_cooldown <= 0 and self.last_seen_player_pos:
            current_dis_to_player = abs(self.last_seen_player_pos[0] - self.pos[0])
            
            # Dash if player is within range and on same platform level
            if current_dis_to_player < self.dash_range and abs(self.last_seen_player_pos[1] - self.pos[1]) < 16:
                self.dash_towards_player()
        
        # Handle dashing physics
        if self.dashing != 0:
            if self.dashing > 0:
                self.dashing = max(0, self.dashing - 1)
            if self.dashing < 0:
                self.dashing = min(0, self.dashing + 1)
                
            if abs(self.dashing) > 50:
                self.velocity[0] = abs(self.dashing) / self.dashing * 6  # Slightly slower than player dash
                if abs(self.dashing) == 51:
                    self.velocity[0] *= 0.1
                # Dash particles
                pvelocity = [abs(self.dashing) / self.dashing * random.random() * 2, 0]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        
        # Cooldown management
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        
        # Normal walking behavior when not dashing
        if self.walking and self.dashing == 0:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            
        elif random.random() < 0.01 and self.dashing == 0:
            self.walking = random.randint(30, 120)
        
        super().update(tilemap, movement=movement)
        
        # Animation states
        if self.dashing != 0:
            self.set_action('run')  # Use run animation for dashing
        elif movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                # ADD SCORING - Award points for killing regular enemy
                self.game.add_score(150, "enemy")
                return True
            
        # FIXED: Collision damage with player during dash - enemy damages player instead of dying
        if abs(self.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                
                # Damage the player instead of killing the enemy
                if not self.game.dead:  # Only damage if player isn't already dead
                    self.game.dead += 1
                    self.game.screenshake = max(16, self.game.screenshake)
                    
                    # Player death effects
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, 
                                                          velocity=[math.cos(angle + math.pi) * speed * 0.5, 
                                                                   math.sin(angle + math.pi) * speed * 0.5], 
                                                          frame=random.randint(0, 7)))
                
                # Stop dash on collision but enemy survives
                self.dashing = 0
                self.velocity[0] *= 0.5
                self.dash_cooldown = 90  # Cooldown after hitting player
                
                # Impact effects at collision point
                for i in range(15):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 3
                    collision_point = [
                        (self.rect().centerx + self.game.player.rect().centerx) / 2,
                        (self.rect().centery + self.game.player.rect().centery) / 2
                    ]
                    self.game.sparks.append(Spark(collision_point, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', collision_point, 
                                                      velocity=[math.cos(angle) * speed * 0.5, 
                                                               math.sin(angle) * speed * 0.5], 
                                                      frame=random.randint(0, 7)))
            
        # Wall collision during dash
        if abs(self.dashing) >= 50 and (self.collisions['right'] or self.collisions['left']):
            self.dashing = 0
            self.velocity[0] = 0
            self.dash_cooldown = 60  # Longer cooldown if hitting wall
            # Wall impact effects
            for i in range(15):
                angle = math.pi if self.collisions['right'] else 0
                self.game.sparks.append(Spark(self.rect().center, angle + random.random() - 0.5, 2 + random.random()))
    
    def dash_towards_player(self):
        """Initiate dash towards the last seen player position"""
        if self.last_seen_player_pos:
            # Determine dash direction
            if self.last_seen_player_pos[0] > self.pos[0]:
                self.dashing = 60  # Dash right
                self.flip = False
            else:
                self.dashing = -60  # Dash left
                self.flip = True
            
            self.dash_cooldown = 120  # 2 second cooldown
            self.game.sfx['dash'].play()
            
            # Dash initiation particles
            for i in range(10):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.8 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
    
    def render(self, surf, offset=(0, 0)):
        # Add visual effect during dash
        if abs(self.dashing) > 50:
            # Create a trail effect
            trail_pos = [self.pos[0] - (3 if self.dashing > 0 else -3), self.pos[1]]
            surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), 
                     (trail_pos[0] - offset[0] + self.anim_offset[0], 
                      trail_pos[1] - offset[1] + self.anim_offset[1]))
            
        super().render(surf, offset=offset)
         # FIXED: Cooldown indicator - make sure it renders after the enemy sprite
        if self.dash_cooldown > 0:
            cooldown_ratio = self.dash_cooldown / 120.0
            
            # Position above enemy head
            bar_width = 12
            bar_height = 3
            bar_x = self.pos[0] - bar_width // 2 - offset[0] + self.size[0] // 2
            bar_y = self.pos[1] - 8 - offset[1]  # Position above enemy
            
            # Only draw if on screen
            if (0 <= bar_x <= surf.get_width() and 0 <= bar_y <= surf.get_height()):
                # Background (empty part)
                pygame.draw.rect(surf, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
                # Cooldown progress (filled part)
                fill_width = max(1, bar_width * (1 - cooldown_ratio))
                pygame.draw.rect(surf, (0, 255, 0), (bar_x, bar_y, fill_width, bar_height))
                # Border
                pygame.draw.rect(surf, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)