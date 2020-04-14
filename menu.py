import math

from button import *
from game import *
from extended_population import delete_instance, rename_instance


# Class that extends functionality of PyGame's default Group class
class ButtonGroup(pygame.sprite.Group):
    # Update will now return True if any of the members of the group returned True
    def update(self, *args):
        output = False
        for s in self.sprites():
            output = s.update(*args) or output

        return output


# Base class for screen classes to inherit from
class ScreenBase:
    def __init__(self, master, title="", titlesize=100, ypos=130):
        # Create title text
        self.title_font = pygame.font.Font("game-font.ttf", titlesize)
        self.title = self.title_font.render(title, False, WHITE)
        self.title_rect = self.title.get_rect(center=(master.SCREENRECT.width // 2, ypos))

        self.buttons = ButtonGroup()  # Group that will contain all buttons on the screen
        self.running = True
        self.master = master
        self.win = master.screen
        self.switch = master.manager.switch
        self.exit = master.manager.exit

    # Default loop containing logic for the menu
    def run(self, background=None, function=None, *args):
        if background is None:
            background = pygame.Surface(self.master.SCREENRECT.size)
            background.fill(LIGHT_BLUE)

        self.win.blit(background, (0, 0))

        while self.running:
            clicked = False  # Variable for representing whether or not the left mouse button has been clicked

            # Event loop
            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.QUIT:
                    self.running = False
                    self.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        clicked = True

            # Update buttons
            button_executed = self.buttons.update(clicked)
            self.running = (not button_executed) and self.running

            try:
                # Call function passed through
                function(*args)
            except TypeError:  # Catch error if no function was passed
                pass

            if not self.running: break

            # Draw to screen
            self.win.blit(self.title, self.title_rect)
            self.buttons.draw(self.win)

            pygame.display.update()


# Start Screen
class StartScreen(ScreenBase):
    def __init__(self, master):
        ScreenBase.__init__(self, master, TITLE)

        # Create button objects
        Button("Play Game", (master.SCREENRECT.width // 2, 280), 60, self.buttons, lambda: self.switch(Game, master))
        Button("AI", (master.SCREENRECT.width // 2, 360), 60, self.buttons, lambda: self.switch(AIScreen, master))
        Button("Quit", (master.SCREENRECT.width // 2, 430), 60, self.buttons, self.exit)

        # Start menu loop
        self.run()


# Game Over Screen
class GameOver(ScreenBase):
    def __init__(self, master, score, playagain=Game, menu_screen=StartScreen, *args):
        ScreenBase.__init__(self, master, "Game Over", 110)

        # Create surface to dim the screen
        surf = pygame.Surface(self.master.SCREENRECT.size, flags=pygame.SRCALPHA)
        surf.fill(DIMMED_BLACK)

        # Create font for score
        self.score_font = pygame.font.Font("game-font.ttf", 70)
        self.score = self.score_font.render(f"Score: {score}", False, WHITE)
        self.score_rect = self.score.get_rect(center=(master.SCREENRECT.width // 2, 230))

        # Create button objects
        Button("Play Again", (master.SCREENRECT.width // 2, 350), 60, self.buttons,
               lambda: self.switch(playagain, master, *args))
        Button("Exit to Menu", (master.SCREENRECT.width // 2, 430), 60, self.buttons,
               lambda: self.switch(menu_screen, master))
        Button("Exit to Windows", (master.SCREENRECT.width // 2, 500), 60, self.buttons, self.exit)

        # Start menu loop
        self.run(surf, self.draw_score)

    # Method that draws score text to screen
    def draw_score(self):
        self.win.blit(self.score, self.score_rect)  # Draw score


# Pause Screen
class PauseScreen(ScreenBase):
    def __init__(self, master, game, screen=StartScreen):
        ScreenBase.__init__(self, master, "GAME PAUSED", 110)
        self.game = game

        # Create surface to dim the screen
        surf = pygame.Surface(self.master.SCREENRECT.size, flags=pygame.SRCALPHA)
        surf.fill(DIMMED_BLACK)

        # Create button objects
        Button("Resume", (master.SCREENRECT.width // 2, 280), 60, self.buttons, "exit")
        Button("Exit to Menu", (master.SCREENRECT.width // 2, 360), 60, self.buttons,
               lambda: self.exit_game(self.switch, screen, master))
        Button("Exit to Windows", (master.SCREENRECT.width // 2, 440), 60, self.buttons,
               lambda: self.exit_game(self.exit))

        # Start menu loop
        self.run(surf, self.modified_run)

    # Additional method executed in 'run' method
    # Makes the program close completely when the close button is clicked, and makes game resume when Esc is pressed
    def modified_run(self):
        for event in self.events:
            if event.type == pygame.QUIT:
                self.exit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    # Exits the game, and can run an additional function afterwards
    def exit_game(self, function=None, *args):
        self.game.running = False

        try:
            function(*args)
        except TypeError:
            pass


# Pause Screen to be used when training AI
class TrainingPauseScreen(ScreenBase):
    def __init__(self, master, game):
        ScreenBase.__init__(self, master, "TRAINING PAUSED", 90)
        self.game = game

        # Create surface to dim the screen
        surf = pygame.Surface(self.master.SCREENRECT.size, flags=pygame.SRCALPHA)
        surf.fill(DIMMED_BLACK)

        # Create button objects
        Button("Resume", (master.SCREENRECT.width // 2, 280), 60, self.buttons, "exit")
        Button("Save and Exit to Menu", (master.SCREENRECT.width // 2, 360), 60, self.buttons,
               lambda: self.exit_training(self.switch, AIScreen, master))
        Button("Save and Exit to Windows", (master.SCREENRECT.width // 2, 440), 60, self.buttons,
               lambda: self.exit_training(self.exit))

        # Start menu loop
        self.run(surf, self.modified_run)

    # Additional method executed in 'run' method
    # Ends program when close button is pressed and exits pause screen when escape is pressed
    def modified_run(self):
        for event in self.events:
            if event.type == pygame.QUIT:
                self.game.running = False
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    # Ends the training session
    def exit_training(self, function=None, *args):
        self.game.running = False
        self.game.population.running = False

        try:
            function(*args)
        except TypeError:
            pass


# AI Screen
class AIScreen(ScreenBase):
    def __init__(self, master):
        ScreenBase.__init__(self, master)

        # Create button objects
        Button("Train AI", (master.SCREENRECT.width // 2, 200), 60, self.buttons,
               lambda: self.switch(SelectAI, master, TrainAI, "Select AI to train"))
        Button("Test AI", (master.SCREENRECT.width // 2, 280), 60, self.buttons,
               lambda: self.switch(SelectAI, master, test_ai, "Select AI to test", False))
        Button("Manage AI Instances", (master.SCREENRECT.width // 2, 360), 60, self.buttons,
               lambda: self.switch(ManageAI, self.master))
        Button("Back", (master.SCREENRECT.width // 2, 430), 60, self.buttons, lambda: self.switch(StartScreen, master))

        # Start menu loop
        self.run()


# Screen displayed to select which AI instance to train
class SelectAI(ScreenBase):
    def __init__(self, master, screen, title=None, enable_new=True):
        ScreenBase.__init__(self, master, title, 70, 70)
        self.screen = screen
        self.enable_new = enable_new
        self.button_groups = self.create_buttons()

        if self.button_groups:
            self.page = 0
            self.buttons = self.button_groups[0]
            self.run(None, self.modified_run)
        else:
            self.run()

    # Modifies run method to allow user to switch between pages with arrow keys
    def modified_run(self):
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and self.page != len(self.button_groups) - 1:
                    self.page += 1
                    self.buttons = self.button_groups[self.page]
                    self.win.fill(LIGHT_BLUE)
                if event.key == pygame.K_LEFT and self.page != 0:
                    self.page -= 1
                    self.buttons = self.button_groups[self.page]
                    self.win.fill(LIGHT_BLUE)

    # Method that creates buttons and divides them into pages if necessary
    def create_buttons(self):
        names = get_instance_names()
        num_pages = math.ceil(len(names) / 5)

        if num_pages > 1:  # If multiple pages are needed
            # Creates button group for each page of buttons
            button_groups = [ButtonGroup() for i in range(num_pages)]

            # Creates button objects for each page, adding them to their respective button group
            for page in range(num_pages):
                for num, name in enumerate(names[page * 5:(page + 1) * 5]):
                    Button(name, (self.master.SCREENRECT.width // 2, 160 + num * 80), 60, button_groups[page],
                           self.switch, True, 'center', self.screen, self.master, name)

                Button("Back", (self.master.SCREENRECT.width // 2 - (90 * self.enable_new), 580), 60,
                       button_groups[page], lambda: self.switch(AIScreen, self.master))
                if self.enable_new:
                    Button("New", (self.master.SCREENRECT.width // 2 + 90, 580), 60, button_groups[page],
                           lambda: self.switch(TextInput, self.master, self.screen, SelectAI,
                                               "Enter name for the new AI"))

            return button_groups

        else:  # If only one page is needed
            for num, name in enumerate(names):
                Button(name, (self.master.SCREENRECT.width // 2, 160 + num * 80), 60, self.buttons,
                       self.switch, True, 'center', self.screen, self.master, name)

            Button("Back", (self.master.SCREENRECT.width // 2 - (90 * self.enable_new), 580), 60, self.buttons,
                   lambda: self.switch(AIScreen, self.master))
            if self.enable_new:
                Button("New", (self.master.SCREENRECT.width // 2 + 90, 580), 60, self.buttons,
                       lambda: self.switch(TextInput, self.master, self.screen, SelectAI, "Enter name for the new AI"))


# Train AI Screen
class TrainAI(ScreenBase):
    def __init__(self, master, ai_name):
        ScreenBase.__init__(self, master, f"Training {ai_name}", 70)

        # Create button objects
        Button("Real Time", (master.SCREENRECT.width // 2, 240), 60, self.buttons,
               lambda: self.switch(train_ai, master, ai_name))
        Button("Quick Time", (master.SCREENRECT.width // 2, 320), 60, self.buttons,
               lambda: self.switch(train_ai, master, ai_name, True))
        Button("Back", (master.SCREENRECT.width // 2, 400), 60, self.buttons,
               lambda: self.switch(SelectAI, master, TrainAI))

        # Start menu loop
        self.run()


# Screen for receiving text input from the user
class TextInput(ScreenBase):
    def __init__(self, master, screen, return_screen, title, screen_args=None, rscreen_args=None):
        ScreenBase.__init__(self, master, title, 60, 90)
        self.screen = screen
        self.return_screen = return_screen
        self.input = ""
        self.screen_args = screen_args if screen_args else (self.master, )
        self.rscreen_args = rscreen_args if rscreen_args else (self.master, self.screen)

        # Create font to display text input
        self.text_font = pygame.font.Font("game-font.ttf", 70)
        self.text = None
        self.text_rect = None

        # Create buttons
        Button("Back", (self.master.SCREENRECT.width // 2, 580), 60, self.buttons,
               lambda: self.switch(return_screen, *self.rscreen_args))

        self.run(None, self.modified_run)

    # Additional method executed in 'run' method
    # Handles keyboard input and draws the text that the user has input to the screen
    def modified_run(self):
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.running = False
                    self.switch(self.screen, *self.screen_args, self.input)
                elif event.key == pygame.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif len(self.input) < 15 and 32 <= event.key <= 126:
                    mod_states = pygame.key.get_mods()
                    self.input += chr(event.key - (32 * (mod_states & pygame.KMOD_SHIFT)))

        self.text = self.text_font.render(self.input, False, WHITE)
        self.text_rect = self.text.get_rect(center=(self.master.SCREENRECT.width // 2, 300))
        self.win.fill(LIGHT_BLUE)
        self.win.blit(self.text, self.text_rect)


# Quick Time Screen
class QuickTime(ScreenBase):
    def __init__(self, master, game):
        ScreenBase.__init__(self, master, "Training AI...", 80, 80)
        self.game = game
        self.font = pygame.font.Font("game-font.ttf", 60)  # Create text font object

        # Create button
        Button("Save and Exit to Menu", (master.SCREENRECT.width // 2, 490), 60, self.buttons,
               lambda: self.exit_training(self.switch, AIScreen, master))
        Button("Save and Exit to Windows", (master.SCREENRECT.width // 2, 570), 60, self.buttons,
               lambda: self.exit_training(self.exit))

    # Main loop
    def run(self):
        clicked = False

        for event in self.game.event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True

        self.buttons.update(clicked)  # Update buttons

        # Clear window
        self.win.fill(LIGHT_BLUE)

        # Draw title
        self.win.blit(self.title, self.title_rect)

        # Create and draw score
        text = self.font.render(f"Score:{self.game.score}", False, WHITE)
        rect = text.get_rect(center=(self.master.SCREENRECT.width // 2, 210))
        self.win.blit(text, rect)

        # Create and draw generation number
        text = self.font.render(f"Gen:{self.game.population.generation}", False, WHITE)
        rect = text.get_rect(center=(self.master.SCREENRECT.width // 2, 290))
        self.win.blit(text, rect)

        # Create and draw number of players alive
        text = self.font.render(f"Alive:{len(self.game.players)}", False, WHITE)
        rect = text.get_rect(center=(self.master.SCREENRECT.width // 2, 370))
        self.win.blit(text, rect)

        self.buttons.draw(self.win)  # Draw buttons

        pygame.display.update()

    # Ends the training session
    def exit_training(self, function=None, *args):
        self.game.running = False
        self.game.population.running = False

        try:
            function(*args)
        except TypeError:
            pass


# Manage AI Instances Screen
class ManageAI(ScreenBase):
    def __init__(self, master, function=None, *args):
        ScreenBase.__init__(self, master)
        self.button_groups = self.create_buttons()

        try:
            # Call function passed through
            function(*args)
            self.switch(ManageAI, master)
            return
        except TypeError:  # Catch error if no function was passed
            pass

        # Start main loop
        if self.button_groups:
            self.page = 0
            self.buttons = self.button_groups[0]
            self.run(None, self.modified_run)
        else:
            self.run()

    # Modifies run method to allow user to switch between pages with arrow keys
    def modified_run(self):
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and self.page != len(self.button_groups) - 1:
                    self.page += 1
                    self.buttons = self.button_groups[self.page]
                    self.win.fill(LIGHT_BLUE)
                if event.key == pygame.K_LEFT and self.page != 0:
                    self.page -= 1
                    self.buttons = self.button_groups[self.page]
                    self.win.fill(LIGHT_BLUE)

    # Method that creates buttons and divides them into pages if necessary
    def create_buttons(self):
        names = get_instance_names()
        num_pages = math.ceil(len(names) / 5)

        if num_pages > 1:  # If multiple pages are needed
            # Creates button group for each page of buttons
            button_groups = [ButtonGroup() for i in range(num_pages)]

            # Creates button objects for each page, adding them to their respective button group
            for page in range(num_pages):
                for num, name in enumerate(names[page * 5:(page + 1) * 5]):
                    Button(name, (self.master.SCREENRECT.width // 2, 160 + num * 80), 60, button_groups[page],
                           self.show_options, False, 'center', name)

                Button("Back", (self.master.SCREENRECT.width // 2, 580), 60, button_groups[page],
                       lambda: self.switch(AIScreen, self.master))

            return button_groups

        else:  # If only one page is needed
            for num, name in enumerate(names):
                Button(name, (self.master.SCREENRECT.width // 2, 160 + num * 80), 60, self.buttons, self.show_options,
                       False, 'center', name)

            Button("Back", (self.master.SCREENRECT.width // 2, 580), 60, self.buttons,
                   lambda: self.switch(AIScreen, self.master))

    # Shows screen with Rename and Delete options
    def show_options(self, ai_name):
        # Create new button group
        self.temp_buttons = self.buttons
        self.buttons = ButtonGroup()

        # Create new buttons
        Button("Rename", (self.master.SCREENRECT.width // 2, self.master.SCREENRECT.height // 2 - 40), 60, self.buttons,
               lambda: self.switch(TextInput, self.master, ManageAI, ManageAI, "Enter new name for AI",
                                   (self.master, rename_instance, ai_name), (self.master, )))
        Button("Delete", (self.master.SCREENRECT.width // 2, self.master.SCREENRECT.height // 2 + 40), 60, self.buttons,
               lambda: self.switch(ManageAI, self.master, delete_instance, ai_name))
        Button("Back", (self.master.SCREENRECT.width // 2, 500), 60, self.buttons, self.hide_options, False)

        # Dim the screen
        surf = pygame.Surface(self.master.SCREENRECT.size, flags=pygame.SRCALPHA)
        surf.fill(DIMMED_BLACK)
        self.win.blit(surf, (0, 0))

    # Closes options screen
    def hide_options(self):
        # Restore previous buttons
        self.buttons = self.temp_buttons

        # Clear window
        surf = pygame.Surface(self.master.SCREENRECT.size)
        surf.fill(LIGHT_BLUE)
        self.win.blit(surf, (0, 0))
