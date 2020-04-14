from pygame.locals import *

from menu import *


# Main class that creates window. Logic handled by Game class
class Main:
    def __init__(self, width, height, title):
        pygame.init()  # Initialise pygame module
        self.screen = pygame.display.set_mode((width, height))  # Create pygame display
        pygame.display.set_caption(title)
        self.SCREENRECT = Rect(0, 0, width, height)  # Create Rect object for screen
        self.clock = pygame.time.Clock()  # Create clock object
        self.playagain = True

        self.manager = SceneManager(StartScreen, self)
        self.manager.run()

        pygame.quit()  # Close pygame when program ends


# Scene manager that decides which screen to give control to
class SceneManager:
    def __init__(self, default_screen, *args):
        self.screen = default_screen
        self.args = args
        self.running = True

    # Starts the program
    def run(self):
        while self.running:
            self.screen(*self.args)

    # Gives control to a different screen
    def switch(self, screen, *args):
        self.screen = screen
        self.args = args

    # Ends the program
    def exit(self):
        self.running = False


# Start the program if this file is executed
if __name__ == "__main__":
    window = Main(WIDTH, HEIGHT, TITLE)  # Create instance of Main
