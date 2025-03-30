"""main.py"""
import sys
import pygame

from .constant import SCREEN_WIDTH, SCREEN_HEIGHT
from .game_object import clear_objects_on_screen, draw_objects_on_screen
from .player import Player
from .ghost import Ghost, GHOST_TYPES

# pygame setup
# pylint: disable=no-member
pygame.init()
# pylint: enable=no-member

pygame.display.set_caption("Pacman Game")
clock = pygame.time.Clock()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
background = pygame.Surface(screen.get_size())
background.fill((0, 0, 0))
screen.blit(background, (0, 0))

# create game objects
player: Player = Player((SCREEN_WIDTH // 2, SCREEN_HEIGHT * 4 // 5), 5)

ghosts: list[Ghost] = []
SECTION_COUNT = len(GHOST_TYPES) + 4
for index, ghost_type in enumerate(GHOST_TYPES):
    x = SCREEN_WIDTH // (SECTION_COUNT + 1) * (index + 3)
    Y = SCREEN_HEIGHT * 2 // 5
    ghost = Ghost(ghost_type, (x, Y), 3)
    ghosts.append(ghost)

while True:
    # poll for events
    # pygame.QUIT event means the user clicked the close button
    for event in pygame.event.get():
        if event.type == pygame.constants.QUIT: # pylint: disable=c-extension-no-member
            sys.exit()

    # clean the previous frame
    clear_objects_on_screen(screen, background, player, *ghosts)

    # main game logic
    keys = pygame.key.get_pressed()
    player.move_by_arrow_keys(keys)

    # start rendering the new frame
    draw_objects_on_screen(screen, player, *ghosts)

    # update the display
    pygame.display.flip()

    # cap the frame rate
    clock.tick(60)
