# -----------------------------------------------------------------------------
#
# Enhanced Pong Game
# Language - Python
# Modules - pygame, sys, random, math
#
# Controls:
#   - Left Paddle: WASD Keys
#   - Right Paddle (Player vs Player Mode): Arrow Keys
# Additional:
#   - Space/P: Pause/Resume
#   - R: Reset Game (or return to menu from Game Over)
#   - Q: Quit
#
# Features:
# - Modern visual design with gradients and effects
# - Sound effects
# - Particle effects
# - Ball trails
# - Enhanced UI with animations
# - Multiple Game Modes: Player vs Player, Player vs Computer AI
#
# -----------------------------------------------------------------------------

import pygame
import sys
import random
import math
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH = 1000
HEIGHT = 600
FPS = 180

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (52, 152, 219)
RED = (231, 76, 60)
GREEN = (46, 204, 113)
YELLOW = (241, 196, 15)
ORANGE = (230, 126, 34)
DARK_BLUE = (44, 62, 80)
LIGHT_BLUE = (174, 214, 241)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 20, 147)

# Initialize display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Enhanced Pong Game by Imron Fathurrahman")
clock = pygame.time.Clock()

# Fonts
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 36)
font_large = pygame.font.Font(None, 72)
font_title = pygame.font.Font(None, 96)

# Game variables
score_left = 0
score_right = 0
max_score = 10
game_state = "menu"  # menu, playing, paused, game_over
winner = ""
game_mode = "none" # "none", "player_vs_player", "player_vs_ai"

# Sound effects (create simple tones)
def create_tone(frequency, duration, sample_rate=22050):
    try:
        import numpy as np
        frames = int(duration * sample_rate)
        arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    except ImportError:
        # Fallback without numpy
        try:
            frames = int(duration * sample_rate)
            arr = []
            for i in range(frames):
                wave = int(4096 * math.sin(2 * math.pi * frequency * i / sample_rate))
                arr.append([wave, wave])
            
            # Convert to pygame array format
            import array
            sound_array = array.array('h', [])
            for frame in arr:
                sound_array.extend(frame)
            
            return pygame.sndarray.make_sound(sound_array)
        except:
            # Return None if sound creation fails
            return None

# Create sound effects
try:
    paddle_hit_sound = create_tone(440, 0.1)
    wall_hit_sound = create_tone(220, 0.1)
    score_sound = create_tone(880, 0.3)
    sound_enabled = True
except:
    # Disable sound if creation fails
    paddle_hit_sound = None
    wall_hit_sound = None
    score_sound = None
    sound_enabled = False
    print("Sound disabled - continuing without audio")

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.life = 255
        self.decay = random.uniform(3, 6)
        self.size = random.uniform(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        self.size *= 0.98
        
    def draw(self, surface):
        if self.life > 0:
            alpha = max(0, self.life)
            color_with_alpha = (*self.color, int(alpha))
            temp_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, color_with_alpha, (self.size, self.size), int(self.size))
            surface.blit(temp_surface, (self.x - self.size, self.y - self.size))
    
    def is_alive(self):
        return self.life > 0

class Trail:
    def __init__(self, max_length=10):
        self.positions = []
        self.max_length = max_length
    
    def add_position(self, x, y):
        self.positions.append((x, y))
        if len(self.positions) > self.max_length:
            self.positions.pop(0)
    
    def draw(self, surface, color):
        for i, pos in enumerate(self.positions):
            alpha = int(255 * (i + 1) / len(self.positions))
            size = int(5 * (i + 1) / len(self.positions))
            if size > 0:
                temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, (*color, alpha), (size, size), size)
                surface.blit(temp_surface, (pos[0] - size, pos[1] - size))

# ... (bagian kode lainnya) ...

class Paddle:
    def __init__(self, x, y, width=15, height=80):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = 6 # Max speed of the paddle
        self.color = WHITE
        self.glow_intensity = 0
        self.target_y = y
        
    def move(self, direction):
        self.y += self.speed * direction
        self.y = max(20, min(HEIGHT - 20 - self.height, self.y))
    
    def ai_move(self, ball_y, difficulty=0.2): # difficulty now controls error margin (0.0 = perfect, higher = more error)
        center_y = self.y + self.height // 2
        
        # Calculate the desired target Y, with a slight offset for "difficulty"
        # This introduces a controlled amount of "human-like" error
        target_y = ball_y + random.uniform(-self.height * difficulty, self.height * difficulty)
        
        # Calculate the difference to the target
        diff_y = target_y - center_y
        
        # Move proportionally to the difference, but cap at paddle's max speed
        # This creates a smoother, "easing" movement towards the target
        # The multiplier (e.g., 0.1) determines responsiveness
        move_amount = diff_y * 0.1 
        
        # Ensure move_amount does not exceed paddle's defined speed
        if abs(move_amount) > self.speed:
            move_amount = self.speed if move_amount > 0 else -self.speed
        
        self.y += move_amount
        
        # Keep paddle within bounds
        self.y = max(20, min(HEIGHT - 20 - self.height, self.y))
    
    def draw(self, surface):
        # Main paddle
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height), 2)
        
        # Glow effect
        if self.glow_intensity > 0:
            glow_surface = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            glow_color = (*NEON_GREEN, int(self.glow_intensity))
            pygame.draw.rect(glow_surface, glow_color, (10, 10, self.width, self.height))
            surface.blit(glow_surface, (self.x - 10, self.y - 10))
            self.glow_intensity = max(0, self.glow_intensity - 5)
    
    def activate_glow(self):
        self.glow_intensity = 100

# ... (bagian kode lainnya) ...


class Ball:
    def __init__(self, x, y, radius=12):
        self.x = x
        self.y = y
        self.radius = radius
        self.reset_ball()
        self.trail = Trail(15)
        self.particles = []
        
    def reset_ball(self):
        self.speed = 6
        angle = random.uniform(-math.pi/6, math.pi/6)
        if random.choice([True, False]):
            angle += math.pi
        self.vx = self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        # Add trail
        self.trail.add_position(self.x, self.y)
        
        # Update particles
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update()
        
        # Wall collision
        if self.y - self.radius <= 20 or self.y + self.radius >= HEIGHT - 20:
            self.vy = -self.vy
            if wall_hit_sound and sound_enabled:
                wall_hit_sound.play()
            self.create_particles(ORANGE)
        
        # Score detection
        if self.x < 0:
            global score_right
            score_right += 1
            if score_sound and sound_enabled:
                score_sound.play()
            self.create_particles(RED, 20)
            self.reset_ball()
        elif self.x > WIDTH:
            global score_left
            score_left += 1
            if score_sound and sound_enabled:
                score_sound.play()
            self.create_particles(BLUE, 20)
            self.reset_ball()
    
    def check_paddle_collision(self, paddle):
        if (self.x - self.radius <= paddle.x + paddle.width and 
            self.x + self.radius >= paddle.x and
            self.y - self.radius <= paddle.y + paddle.height and
            self.y + self.radius >= paddle.y):
            
            # Calculate bounce angle
            paddle_center = paddle.y + paddle.height // 2
            hit_pos = (self.y - paddle_center) / (paddle.height // 2)
            bounce_angle = hit_pos * math.pi / 3  # Max 60 degrees
            
            # Determine direction
            if paddle.x < WIDTH // 2:  # Left paddle
                self.vx = abs(self.vx)
            else:  # Right paddle
                self.vx = -abs(self.vx)
            
            self.vy = self.speed * math.sin(bounce_angle)
            
            # Increase speed slightly
            self.speed = min(12, self.speed + 0.2)
            speed_magnitude = math.sqrt(self.vx**2 + self.vy**2)
            self.vx = (self.vx / speed_magnitude) * self.speed
            self.vy = (self.vy / speed_magnitude) * self.speed
            
            if paddle_hit_sound and sound_enabled:
                paddle_hit_sound.play()
            paddle.activate_glow()
            self.create_particles(NEON_PINK, 15)
            
            return True
        return False
    
    def create_particles(self, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(self.x, self.y, color))
    
    def draw(self, surface):
        # Draw trail
        self.trail.draw(surface, NEON_GREEN)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
        
        # Draw ball with glow effect
        glow_surface = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*YELLOW, 50), (self.radius * 3, self.radius * 3), self.radius * 2)
        surface.blit(glow_surface, (self.x - self.radius * 3, self.y - self.radius * 3))
        
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

def draw_gradient_background(surface):
    for y in range(HEIGHT):
        color_ratio = y / HEIGHT
        r = int(DARK_BLUE[0] * (1 - color_ratio) + BLACK[0] * color_ratio)
        g = int(DARK_BLUE[1] * (1 - color_ratio) + BLACK[1] * color_ratio)
        b = int(DARK_BLUE[2] * (1 - color_ratio) + BLACK[2] * color_ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

def draw_center_line(surface):
    for y in range(20, HEIGHT - 20, 30):
        pygame.draw.rect(surface, WHITE, (WIDTH // 2 - 2, y, 4, 20))

def draw_ui(surface):
    # Draw borders
    pygame.draw.rect(surface, WHITE, (0, 0, WIDTH, 20))
    pygame.draw.rect(surface, WHITE, (0, HEIGHT - 20, WIDTH, 20))
    
    # Draw scores with glow effect
    score_text_left = font_large.render(str(score_left), True, BLUE)
    score_text_right = font_large.render(str(score_right), True, RED)
    
    # Glow effect for scores
    glow_left = font_large.render(str(score_left), True, LIGHT_BLUE)
    glow_right = font_large.render(str(score_right), True, (255, 150, 150))
    
    surface.blit(glow_left, (WIDTH // 4 - 32, 48))
    surface.blit(glow_right, (3 * WIDTH // 4 - 32, 48))
    surface.blit(score_text_left, (WIDTH // 4 - 30, 50))
    surface.blit(score_text_right, (3 * WIDTH // 4 - 30, 50))

def draw_menu(surface):
    draw_gradient_background(surface)
    
    # Title
    title_text = font_title.render("PONG", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 50))
    surface.blit(title_text, title_rect)
    
    # Subtitle with glow
    subtitle_text = font_medium.render("Enhanced Edition", True, NEON_GREEN)
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 20))
    surface.blit(subtitle_text, subtitle_rect)
    
    # Game Mode Selection
    pvp_text = font_medium.render("Press 1 for Player vs Player", True, WHITE)
    pvp_rect = pvp_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    surface.blit(pvp_text, pvp_rect)

    pva_text = font_medium.render("Press 2 for Player vs Computer", True, WHITE)
    pva_rect = pva_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90))
    surface.blit(pva_text, pva_rect)

    # General Instructions
    instructions = [
        "P - Pause | R - Reset | Q - Quit"
    ]
    
    for i, instruction in enumerate(instructions):
        text = font_small.render(instruction, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150 + i * 30))
        surface.blit(text, text_rect)

def draw_pause_screen(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    surface.blit(overlay, (0, 0))
    
    pause_text = font_large.render("PAUSED", True, WHITE)
    pause_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(pause_text, pause_rect)
    
    resume_text = font_medium.render("Press SPACE to Resume", True, NEON_GREEN)
    resume_rect = resume_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    surface.blit(resume_text, resume_rect)

def draw_game_over(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    winner_text_str = ""
    winner_color = WHITE

    if winner == "left":
        winner_text_str = "Player 1 Wins!" if game_mode == "player_vs_player" else "You Win!"
        winner_color = BLUE
    elif winner == "right":
        winner_text_str = "Player 2 Wins!" if game_mode == "player_vs_player" else "Computer Wins!"
        winner_color = RED

    winner_text = font_large.render(winner_text_str, True, winner_color)
    winner_rect = winner_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(winner_text, winner_rect)
    
    restart_text = font_medium.render("Press R to Play Again | Q to Quit", True, WHITE)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
    surface.blit(restart_text, restart_rect)

def reset_game():
    global score_left, score_right, game_state, game_mode
    score_left = 0
    score_right = 0
    # If coming from game_over, go back to menu to choose mode
    if game_state == "game_over":
        game_state = "menu"
        game_mode = "none"
    else: # Otherwise, just reset and continue playing in current mode
        game_state = "playing"

def main():
    global game_state, winner, game_mode
    
    # Create game objects
    left_paddle = Paddle(30, HEIGHT // 2 - 40)
    right_paddle = Paddle(WIDTH - 45, HEIGHT // 2 - 40)
    ball = Ball(WIDTH // 2, HEIGHT // 2)
    
    # Input handling flags
    left_up = left_down = right_up = right_down = False
    
    running = True
    while running:
        dt = clock.tick(FPS)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if game_state == "menu" and game_mode != "none": # Only start if mode selected
                        game_state = "playing"
                        reset_game()
                    elif game_state == "playing":
                        game_state = "paused"
                    elif game_state == "paused":
                        game_state = "playing"
                elif event.key == pygame.K_p:
                    if game_state == "playing":
                        game_state = "paused"
                    elif game_state == "paused":
                        game_state = "playing"
                elif event.key == pygame.K_r:
                    reset_game() # Handles resetting scores and potentially changing state to menu
                
                # Mode selection in menu
                if game_state == "menu":
                    if event.key == pygame.K_1:
                        game_mode = "player_vs_player"
                        game_state = "playing" # Start game immediately after selection
                        reset_game() # Reset scores
                    elif event.key == pygame.K_2:
                        game_mode = "player_vs_ai"
                        game_state = "playing" # Start game immediately after selection
                        reset_game() # Reset scores

                # Paddle controls (only active if playing)
                if game_state == "playing":
                    # Left Paddle (Player 1)
                    if event.key == pygame.K_w:
                        left_up = True
                    elif event.key == pygame.K_s:
                        left_down = True
                    
                    # Right Paddle (Player 2, if PvP mode)
                    if game_mode == "player_vs_player":
                        if event.key == pygame.K_UP:
                            right_up = True
                        elif event.key == pygame.K_DOWN:
                            right_down = True
            
            elif event.type == pygame.KEYUP:
                # Paddle controls (only active if playing)
                if game_state == "playing":
                    # Left Paddle (Player 1)
                    if event.key == pygame.K_w:
                        left_up = False
                    elif event.key == pygame.K_s:
                        left_down = False
                    
                    # Right Paddle (Player 2, if PvP mode)
                    if game_mode == "player_vs_player":
                        if event.key == pygame.K_UP:
                            right_up = False
                        elif event.key == pygame.K_DOWN:
                            right_down = False
        
        # Game logic
        if game_state == "playing":
            # Left Paddle movement (Player 1)
            if left_up:
                left_paddle.move(-1)
            if left_down:
                left_paddle.move(1)
            
            # Right Paddle movement (Player 2 or AI)
            if game_mode == "player_vs_player":
                if right_up:
                    right_paddle.move(-1)
                if right_down:
                    right_paddle.move(1)
            elif game_mode == "player_vs_ai":
                right_paddle.ai_move(ball.y) # AI controls right paddle
            
            # Ball update
            ball.update()
            ball.check_paddle_collision(left_paddle)
            ball.check_paddle_collision(right_paddle)
            
            # Check for win condition
            if score_left >= max_score:
                winner = "left"
                game_state = "game_over"
            elif score_right >= max_score:
                winner = "right"
                game_state = "game_over"
        
        # Drawing
        if game_state == "menu":
            draw_menu(screen)
        else:
            draw_gradient_background(screen)
            draw_center_line(screen)
            draw_ui(screen)
            
            # Draw paddles and ball only if not in menu state
            if game_state in ["playing", "paused", "game_over"]:
                left_paddle.draw(screen)
                right_paddle.draw(screen)
                ball.draw(screen)
            
            if game_state == "paused":
                draw_pause_screen(screen)
            elif game_state == "game_over":
                draw_game_over(screen)
        
        pygame.display.flip() # Update the full display Surface to the screen
    
    pygame.quit() # Uninitialize all pygame modules
    sys.exit() # Exit the program

if __name__ == "__main__":
    main()
