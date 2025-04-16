import sys
import pygame as pg

def show_game_over_screen(screen, message = "The ghost has caught you!"):
    screen_sizes =screen.get_size()

    overlay = pg.Surface((screen_sizes[0], screen_sizes[1]), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    font =pg.font.SysFont("Arial", 72, bold=True)
    game_over_text = font.render("Game Over!", True, (255, 0, 0))
    text_rect = game_over_text.get_rect(center=(screen_sizes[0] // 2, screen_sizes[1] // 2 - 80))
    screen.blit(game_over_text, text_rect)
    sub_font = pg.font.SysFont("Arial", 24)
    sub_text = sub_font.render(message, True, (255, 255, 255))
    sub_rect = sub_text.get_rect(center=(screen_sizes[0] // 2, screen_sizes[1] // 2 ))
    screen.blit(sub_text, sub_rect)

    button_font = pg.font.SysFont("Arial", 32)
    
    replay_text = button_font.render("Replay", True, (255, 255, 255))
    replay_button = pg.Rect(0,0,150,50)
    replay_button.center = (screen_sizes[0] //2 - 100,screen_sizes[1] //2 + 80 )

    exit_text = button_font.render("Exit", True, (255, 255, 255))
    exit_button = pg.Rect(0,0,150,50)
    exit_button.center = (screen_sizes[0] //2 + 100,screen_sizes[1] //2 + 80 )

    pg.draw.rect(screen,(50,150,50),replay_button,border_radius=10)
    pg.draw.rect(screen,(150,50,50),exit_button,border_radius=10)

    screen.blit(replay_text, replay_text.get_rect(center=replay_button.center))
    screen.blit(exit_text, exit_text.get_rect(center=exit_button.center))

    pg.display.flip()

    waiting = True
    while waiting:
        for event in pg.event.get():
            if event.type ==pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                if replay_button.collidepoint(mouse_pos):
                    return "replay"
                elif exit_button.collidepoint(mouse_pos):
                    return "exit"
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    return "replay"
                elif event.key == pg.K_ESCAPE:
                    return "exit"