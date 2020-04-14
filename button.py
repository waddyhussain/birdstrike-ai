import pygame
from settings import *


# Class for button object to be used in menus
class Button(pygame.sprite.Sprite):
    def __init__(self, text, pos, height, button_group, onclick=None, end_onclick=True, anchor='center', *args):
        pygame.sprite.Sprite.__init__(self, button_group)
        self.font_object = pygame.font.Font("game-font.ttf", height)  # Create font object
        self.default_text = self.font_object.render(text, False, WHITE)  # Text displayed when not highlighted
        self.highlighted_text = self.font_object.render(text, False, DIMMED_WHITE)  # Text displayed when highlighted
        self.onclick = onclick  # Function to be called when button is clicked
        self.end_onclick = end_onclick  # Decides whether or not the screen should end after a button is clicked
        self.args = args

        self.image = self.default_text  # Text surface that is displayed
        self.rect = self.image.get_rect(**{anchor: pos})  # Rect object representing where button is located

    # Detects if the mouse is hovering over the button
    def mouse_collide(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    # Update the button (highlight/un-highlight it, call its function when clicked)
    def update(self, clicked):
        if self.mouse_collide():
            self.image = self.highlighted_text  # Highlight text when the cursor hovers over button
            if clicked and self.onclick:
                try:
                    self.onclick(*self.args)  # Execute function "onclick" when button is clicked
                except TypeError:  # Catches error if "onclick" isn't callable
                    pass

                return True and self.end_onclick
        else:
            self.image = self.default_text  # Un-highlight text when mouse isn't hovering over button
