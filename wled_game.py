#!/usr/bin/env python3
"""
3D Raycaster FPS Game with WLED Matrix Streaming
Play a first-person shooter on your PC while streaming to 16x8 WLED matrix in real-time
"""

import pygame
import numpy as np
import requests
import time
import sys
import threading
from PIL import Image

# WLED Configuration
WLED_IP = "192.168.30.119"
MATRIX_WIDTH = 16
MATRIX_HEIGHT = 8
WLED_API_URL = f"http://{WLED_IP}/json/state"

# Game Configuration
GAME_WIDTH = 320
GAME_HEIGHT = 200
SCALE = 3  # Scale factor for display window

class WLEDStreamer:
    def __init__(self):
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_print = time.time()
        self.running = True
        self.session = requests.Session()

    def rgb_to_wled_index(self, x, y):
        """Convert x,y coordinates to WLED LED index
        WLED 2D configuration handles all panel mapping automatically!
        We just send sequential indices in row-major order.
        """
        return y * MATRIX_WIDTH + x

    def send_frame_to_wled(self, frame_data):
        """Send RGB frame data to WLED via JSON API"""
        try:
            ordered_leds = [None] * (MATRIX_WIDTH * MATRIX_HEIGHT)
            for y in range(MATRIX_HEIGHT):
                for x in range(MATRIX_WIDTH):
                    pixel = frame_data[y, x]
                    idx = self.rgb_to_wled_index(x, y)
                    ordered_leds[idx] = [int(pixel[0]), int(pixel[1]), int(pixel[2])]

            payload = {
                "on": True,
                "bri": 255,
                "seg": [{"id": 0, "i": ordered_leds}]
            }

            response = self.session.post(WLED_API_URL, json=payload, timeout=0.05)
            self.frame_count += 1

            if time.time() - self.last_fps_print >= 2.0:
                elapsed = time.time() - self.start_time
                fps = self.frame_count / elapsed if elapsed > 0 else 0
                print(f"[WLED] {self.frame_count} frames, {fps:.1f} FPS")
                self.last_fps_print = time.time()

            return response.status_code == 200
        except Exception as e:
            return False

    def downscale_surface(self, surface):
        """Downscale a pygame surface to matrix size"""
        # Convert pygame surface to numpy array
        rgb_array = pygame.surfarray.array3d(surface)
        # Transpose to correct orientation (pygame uses x,y instead of y,x)
        rgb_array = np.transpose(rgb_array, (1, 0, 2))

        # Convert to PIL Image and downscale
        img = Image.fromarray(rgb_array.astype('uint8'), 'RGB')
        img_resized = img.resize((MATRIX_WIDTH, MATRIX_HEIGHT), Image.Resampling.LANCZOS)

        return np.array(img_resized)

class RaycastGame:
    """3D raycasting FPS game"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE))
        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        pygame.display.set_caption("3D FPS on WLED Matrix - Use Arrow Keys to Move")

        self.clock = pygame.time.Clock()
        self.running = True

        # Player position and angle
        self.player_x = 3.5
        self.player_y = 3.5
        self.player_angle = 0

        # Simple map (1 = wall, 0 = empty)
        self.map = [
            [1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,1],
            [1,0,1,0,0,1,0,1],
            [1,0,0,0,0,0,0,1],
            [1,0,1,0,0,1,0,1],
            [1,0,0,0,0,0,0,1],
            [1,0,0,1,1,0,0,1],
            [1,1,1,1,1,1,1,1],
        ]

        # Colors
        self.sky_color = (50, 50, 100)
        self.floor_color = (100, 100, 100)
        self.wall_colors = [
            (200, 50, 50),   # Red
            (150, 30, 30),   # Dark red
        ]

        # Movement
        self.move_speed = 0.05
        self.rot_speed = 0.05

        # Weapon/Shooting
        self.shooting = False
        self.muzzle_flash_timer = 0
        self.shot_cooldown = 0
        self.bullet_impacts = []  # List of (x_pos, timer) for bullet impacts

    def cast_ray(self, angle):
        """Cast a single ray and return distance to wall"""
        ray_x = self.player_x
        ray_y = self.player_y

        dx = np.cos(angle) * 0.02
        dy = np.sin(angle) * 0.02

        for _ in range(200):
            ray_x += dx
            ray_y += dy

            map_x = int(ray_x)
            map_y = int(ray_y)

            if (0 <= map_y < len(self.map) and
                0 <= map_x < len(self.map[0]) and
                self.map[map_y][map_x] == 1):

                dist = np.sqrt((ray_x - self.player_x)**2 + (ray_y - self.player_y)**2)
                return dist, (map_x + map_y) % 2

        return 100, 0

    def render(self):
        """Render the 3D view using raycasting"""
        # Fill sky and floor
        self.game_surface.fill(self.sky_color)
        pygame.draw.rect(self.game_surface, self.floor_color,
                        (0, GAME_HEIGHT//2, GAME_WIDTH, GAME_HEIGHT//2))

        # Cast rays for each column
        fov = np.pi / 3  # 60 degree FOV
        num_rays = GAME_WIDTH

        for i in range(num_rays):
            ray_angle = self.player_angle - fov/2 + (i / num_rays) * fov
            dist, wall_type = self.cast_ray(ray_angle)

            # Fix fisheye effect
            dist *= np.cos(ray_angle - self.player_angle)

            if dist > 0.1:
                wall_height = int(GAME_HEIGHT / dist)
                wall_top = (GAME_HEIGHT - wall_height) // 2

                # Add distance shading
                shade = max(0, min(1, 1 - dist / 8))
                color = tuple(int(c * shade) for c in self.wall_colors[wall_type])

                pygame.draw.line(self.game_surface, color,
                               (i, wall_top), (i, wall_top + wall_height))

        # Draw bullet impacts on walls
        for impact_x, timer in self.bullet_impacts:
            if timer > 0:
                # Find the wall at this x position
                ray_angle = self.player_angle - fov/2 + (impact_x / GAME_WIDTH) * fov
                dist, _ = self.cast_ray(ray_angle)
                dist *= np.cos(ray_angle - self.player_angle)

                if dist > 0.1:
                    wall_height = int(GAME_HEIGHT / dist)
                    wall_top = (GAME_HEIGHT - wall_height) // 2
                    wall_center = wall_top + wall_height // 2

                    # Draw bullet impact (bright yellow flash)
                    impact_size = max(2, int(5 * timer / 10))
                    pygame.draw.circle(self.game_surface, (255, 255, 0),
                                     (impact_x, wall_center), impact_size)

        # Draw weapon sprite at bottom center
        self.draw_weapon()

    def draw_weapon(self):
        """Draw large pixel art pistol sprite - classic FPS style"""
        base_x = GAME_WIDTH // 2
        base_y = GAME_HEIGHT - 80  # Higher position

        # Recoil animation
        recoil = 8 if self.muzzle_flash_timer > 3 else (3 if self.muzzle_flash_timer > 0 else 0)
        weapon_y = base_y + recoil

        # Bright colors for visibility
        gun_dark = (60, 60, 70)
        gun_light = (140, 140, 150)
        gun_barrel = (50, 50, 60)
        handle_color = (100, 70, 50)

        # MUCH BIGGER WEAPON (4x scale)
        # Barrel
        pygame.draw.rect(self.game_surface, gun_barrel, (base_x - 16, weapon_y + 10, 32, 20))
        # Slide (top part)
        pygame.draw.rect(self.game_surface, gun_light, (base_x - 24, weapon_y + 25, 48, 18))
        pygame.draw.rect(self.game_surface, gun_dark, (base_x - 20, weapon_y + 28, 40, 12))
        # Frame (body)
        pygame.draw.rect(self.game_surface, gun_light, (base_x - 20, weapon_y + 43, 40, 24))
        # Trigger guard
        pygame.draw.rect(self.game_surface, gun_dark, (base_x - 8, weapon_y + 55, 16, 10))
        # Handle/Grip (large and visible)
        pygame.draw.rect(self.game_surface, handle_color, (base_x - 16, weapon_y + 65, 24, 35))
        # Grip details
        for i in range(4):
            y_pos = weapon_y + 70 + i * 6
            pygame.draw.line(self.game_surface, (80, 50, 30), (base_x - 12, y_pos), (base_x + 8, y_pos), 2)
        # Front sight (bright)
        pygame.draw.rect(self.game_surface, (255, 255, 100), (base_x - 4, weapon_y + 20, 8, 8))

        # HUGE muzzle flash
        if self.muzzle_flash_timer > 0:
            flash_x = base_x
            flash_y = weapon_y + 10
            flash_size = 50 if self.muzzle_flash_timer > 3 else 30

            # Massive layered flash
            pygame.draw.circle(self.game_surface, (255, 80, 0), (flash_x, flash_y), flash_size + 20)
            pygame.draw.circle(self.game_surface, (255, 200, 50), (flash_x, flash_y), flash_size + 10)
            pygame.draw.circle(self.game_surface, (255, 255, 255), (flash_x, flash_y), flash_size)

            # Big flash rays
            if self.muzzle_flash_timer > 3:
                for i in range(8):
                    angle = i * 0.785  # 45 degrees
                    length = 60
                    end_x = flash_x + int(np.cos(angle) * length)
                    end_y = flash_y + int(np.sin(angle) * length)
                    pygame.draw.line(self.game_surface, (255, 255, 200), (flash_x, flash_y), (end_x, end_y), 5)

    def handle_input(self):
        """Handle keyboard input"""
        keys = pygame.key.get_pressed()

        # Rotation
        if keys[pygame.K_LEFT]:
            self.player_angle -= self.rot_speed
        if keys[pygame.K_RIGHT]:
            self.player_angle += self.rot_speed

        # Movement
        if keys[pygame.K_UP]:
            new_x = self.player_x + np.cos(self.player_angle) * self.move_speed
            new_y = self.player_y + np.sin(self.player_angle) * self.move_speed
            if self.map[int(new_y)][int(new_x)] == 0:
                self.player_x = new_x
                self.player_y = new_y

        if keys[pygame.K_DOWN]:
            new_x = self.player_x - np.cos(self.player_angle) * self.move_speed
            new_y = self.player_y - np.sin(self.player_angle) * self.move_speed
            if self.map[int(new_y)][int(new_x)] == 0:
                self.player_x = new_x
                self.player_y = new_y

        # Strafing
        if keys[pygame.K_a]:
            new_x = self.player_x + np.cos(self.player_angle - np.pi/2) * self.move_speed
            new_y = self.player_y + np.sin(self.player_angle - np.pi/2) * self.move_speed
            if self.map[int(new_y)][int(new_x)] == 0:
                self.player_x = new_x
                self.player_y = new_y

        if keys[pygame.K_d]:
            new_x = self.player_x + np.cos(self.player_angle + np.pi/2) * self.move_speed
            new_y = self.player_y + np.sin(self.player_angle + np.pi/2) * self.move_speed
            if self.map[int(new_y)][int(new_x)] == 0:
                self.player_x = new_x
                self.player_y = new_y

        # Shooting
        if keys[pygame.K_SPACE] and self.shot_cooldown == 0:
            self.shoot()

    def shoot(self):
        """Fire weapon"""
        self.shooting = True
        self.muzzle_flash_timer = 5  # Flash for 5 frames
        self.shot_cooldown = 10  # 10 frames between shots

        # Cast ray to see if we hit a wall
        dist, _ = self.cast_ray(self.player_angle)
        if dist < 10:  # Hit something
            # Add bullet impact at center of screen
            impact_x = GAME_WIDTH // 2
            self.bullet_impacts.append([impact_x, 10])  # Impact lasts 10 frames

    def update_timers(self):
        """Update all animation timers"""
        # Muzzle flash
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= 1

        # Shot cooldown
        if self.shot_cooldown > 0:
            self.shot_cooldown -= 1

        # Bullet impacts
        for impact in self.bullet_impacts:
            if impact[1] > 0:
                impact[1] -= 1

        # Remove expired impacts
        self.bullet_impacts = [imp for imp in self.bullet_impacts if imp[1] > 0]

    def run_with_wled_stream(self):
        """Main game loop with WLED streaming"""
        streamer = WLEDStreamer()

        print("\n" + "="*60)
        print("3D Raycaster FPS Game Running!")
        print("="*60)
        print("\nControls:")
        print("  Arrow Keys / WASD - Move and rotate")
        print("  SPACE - Shoot")
        print("  ESC - Quit")
        print(f"\nStreaming to WLED matrix at {WLED_IP}")
        print("="*60 + "\n")

        last_wled_update = time.time()
        wled_frame_time = 1.0 / 20  # 20 FPS to WLED

        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # Handle input
            self.handle_input()

            # Update timers
            self.update_timers()

            # Render game
            self.render()

            # Scale up to display window
            scaled_surface = pygame.transform.scale(self.game_surface,
                                                    (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE))
            self.screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()

            # Stream to WLED (at lower frame rate)
            current_time = time.time()
            if current_time - last_wled_update >= wled_frame_time:
                downscaled = streamer.downscale_surface(self.game_surface)
                streamer.send_frame_to_wled(downscaled)
                last_wled_update = current_time

            # Cap frame rate
            self.clock.tick(35)  # 35 FPS for game

        pygame.quit()
        print("\nGame ended. Total frames sent to WLED:", streamer.frame_count)

def main():
    print("="*60)
    print("3D FPS Game with WLED Matrix Streaming")
    print(f"Matrix: {MATRIX_WIDTH}x{MATRIX_HEIGHT} @ {WLED_IP}")
    print("="*60)

    try:
        game = RaycastGame()
        game.run_with_wled_stream()
    except KeyboardInterrupt:
        print("\n\nGame interrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
