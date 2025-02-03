import pygame
from pygame.locals import *
import random
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class GameConfig:
    SCREEN_WIDTH: int = 600
    SCREEN_HEIGHT: int = 735
    FPS: int = 60
    PIPE_GAP: int = 150
    PIPE_FREQUENCY: int = 1450
    SCROLL_SPEED: int = 4
    GRAVITY: float = 0.5
    JUMP_SPEED: float = -10
    MAX_SPEED: float = 8.5
    GROUND_HEIGHT: int = 576
    BIRD_START_X: int = 200

class Bird(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int):
        super().__init__()
        self.images = [pygame.image.load(f'images/bird_{i}.png') for i in range(1, 4)]
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = 0
        self.animation_index = 0
        self.animation_timer = 0
        self.animation_cooldown = 5
        self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.velocity = GameConfig.JUMP_SPEED
            self.is_jumping = True

    def release_jump(self):
        self.is_jumping = False

    def update(self, game_state):
        if game_state.is_playing:
            # Apply gravity
            self.velocity = min(self.velocity + GameConfig.GRAVITY, GameConfig.MAX_SPEED)
            if self.rect.bottom < GameConfig.GROUND_HEIGHT:
                self.rect.y += int(self.velocity)

            # Handle animation
            self.animation_timer += 1
            if self.animation_timer >= self.animation_cooldown:
                self.animation_timer = 0
                self.animation_index = (self.animation_index + 1) % len(self.images)
                self.image = pygame.transform.rotate(
                    self.images[self.animation_index], 
                    self.velocity * -2
                )
        elif game_state.is_game_over:
            self.image = pygame.transform.rotate(self.images[self.animation_index], -90)

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, is_top: bool):
        super().__init__()
        self.image = pygame.image.load('images/pipe.png')
        if is_top:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect = self.image.get_rect(bottomleft=(x, y - GameConfig.PIPE_GAP // 2))
        else:
            self.rect = self.image.get_rect(topleft=(x, y + GameConfig.PIPE_GAP // 2))

    def update(self):
        self.rect.x -= GameConfig.SCROLL_SPEED
        if self.rect.right < 0:
            self.kill()

class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.is_playing = False
        self.is_game_over = False
        self.base_scroll = 0
        self.last_pipe_time = 0
        self.pass_pipe = False

class FlappyBird:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption('Flappy Bird')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('arial black', 55)
        
        # Load assets
        self.background = pygame.image.load('images/background.png')
        self.base = pygame.image.load('images/base.png')
        self.restart_button = pygame.image.load('images/restart.png')
        self.restart_rect = self.restart_button.get_rect(topleft=(150, 100))
        
        self.game_state = GameState()
        self.init_sprites()

    def init_sprites(self):
        self.bird = Bird(GameConfig.BIRD_START_X, GameConfig.SCREEN_HEIGHT // 2)
        self.bird_group = pygame.sprite.GroupSingle(self.bird)
        self.pipe_group = pygame.sprite.Group()

    def spawn_pipes(self):
        if (pygame.time.get_ticks() - self.game_state.last_pipe_time) > GameConfig.PIPE_FREQUENCY:
            height = random.randint(-100, 100)
            center_y = GameConfig.SCREEN_HEIGHT // 2
            self.pipe_group.add(
                Pipe(GameConfig.SCREEN_WIDTH, center_y + height, True),
                Pipe(GameConfig.SCREEN_WIDTH, center_y + height, False)
            )
            self.game_state.last_pipe_time = pygame.time.get_ticks()

    def update_score(self):
        if self.pipe_group:
            pipe = self.pipe_group.sprites()[0]
            if (self.bird.rect.left > pipe.rect.left and 
                self.bird.rect.left < pipe.rect.right and 
                not self.game_state.pass_pipe):
                self.game_state.pass_pipe = True
            elif self.game_state.pass_pipe and self.bird.rect.left > pipe.rect.right:
                self.game_state.score += 1
                self.game_state.pass_pipe = False

    def check_collisions(self):
        if (pygame.sprite.spritecollide(self.bird, self.pipe_group, False) or 
            self.bird.rect.top < 0 or 
            self.bird.rect.bottom >= GameConfig.GROUND_HEIGHT):
            self.game_state.is_game_over = True
            self.game_state.is_playing = False

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.pipe_group.draw(self.screen)
        self.bird_group.draw(self.screen)
        self.screen.blit(self.base, (self.game_state.base_scroll, GameConfig.GROUND_HEIGHT))
        
        score_text = self.font.render(str(self.game_state.score), True, (0, 0, 0))
        self.screen.blit(score_text, (GameConfig.SCREEN_WIDTH // 2, 15))
        
        if self.game_state.is_game_over:
            self.screen.blit(self.restart_button, self.restart_rect)

        # Draw controls info
        controls_font = pygame.font.SysFont('arial', 20)
        controls_text = controls_font.render('SPACE to jump | Q to quit', True, (0, 0, 0))
        self.screen.blit(controls_text, (10, 10))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            # Handle mouse input
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self.game_state.is_playing and not self.game_state.is_game_over:
                    self.game_state.is_playing = True
                if self.game_state.is_game_over and self.restart_rect.collidepoint(event.pos):
                    self.game_state = GameState()
                    self.init_sprites()
                self.bird.jump()
            if event.type == pygame.MOUSEBUTTONUP:
                self.bird.release_jump()
                
            # Handle keyboard input
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not self.game_state.is_playing and not self.game_state.is_game_over:
                        self.game_state.is_playing = True
                    self.bird.jump()
                elif event.key == pygame.K_q:
                    return False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bird.release_jump()
                    
        return True

    def update(self):
        if self.game_state.is_playing:
            self.spawn_pipes()
            self.pipe_group.update()
            self.update_score()
            self.check_collisions()
            
            self.game_state.base_scroll -= GameConfig.SCROLL_SPEED
            if abs(self.game_state.base_scroll) > 70:
                self.game_state.base_scroll = 0
        
        self.bird_group.update(self.game_state)

    def run(self):
        running = True
        while running:
            self.clock.tick(GameConfig.FPS)
            running = self.handle_input()
            self.update()
            self.draw()
            pygame.display.update()
        pygame.quit()

if __name__ == '__main__':
    game = FlappyBird()
    game.run()