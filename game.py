import neat
import time
import csv

import menu
from sprites import *
from extended_population import ExtendedPopulation, get_instance_names, pickle


class Game:
    cap = True

    def __init__(self, master, ai_control=False, training=False, quick_time=False):
        # Initialise default attributes
        self.master = master
        self.window = master.screen
        self.clock = master.clock
        self.ai_control = ai_control
        self.training = training
        self.quick_time = quick_time
        self.fps = FPS
        self.tickcount = 0
        self.score = 0
        self.running = True
        self.quicktime_object = menu.QuickTime(master, self) if self.quick_time else None

        # Create font object
        self.pixelfont = pygame.font.Font("game-font.ttf", 30)

        # Reset difficulty for Bird class
        Bird.reset()

        # Initialise Sprite Groups
        self.all = pygame.sprite.Group()
        self.birds = pygame.sprite.Group()
        self.players = pygame.sprite.Group()

        # Assign groups to each sprite class
        Background.containers = self.all
        Player.containers = [self.all, self.players]
        Bird.containers = [self.all, self.birds]

        # Create instance of Background Class
        self.background = Background()

        if not ai_control:
            self.player = Player(self)
            self.run()

    # Main game loop
    def run(self):
        while self.running:
            if (self.cap or not self.ai_control) and not self.quick_time: self.clock.tick(self.fps)  # Cap FPS
            self.tickcount += 1
            self.events()

            # End game when 'running' is False or there are no players left
            planes_alive = len(self.players)
            if (not self.running) or planes_alive == 0:
                break

            self.update()

            if not self.quick_time:
                self.draw()
            else:
                self.quicktime_object.run()

            if not self.ai_control: self.increase_difficulty()  # Don't increase difficulty for AI

            # Check for collision
            if not self.ai_control:
                if pixelperfect_collision(self.players, self.birds, False, False):
                    time.sleep(0.1)
                    menu.GameOver(self.master, self.score)
                    break
            elif not self.training:
                if pixelperfect_collision(self.players, self.birds, False, False):
                    menu.GameOver(self.master, self.score, test_ai, menu.AIScreen, self.ai_name)
                    break
            else:
                pygame.sprite.groupcollide(self.players, self.birds, True, False)

            # Increase score
            if self.tickcount % (FPS // 20) == 0:
                self.score += 1

            # Increase fitness
            try:
                for sprite in self.players.sprites():
                    in_middle = HEIGHT // 10 <= sprite.rect.centery <= (9 * HEIGHT) // 10
                    genome = self.ai_players[sprite][1]
                    genome.fitness += 0.1 + (-1.1 * (not in_middle))
            except AttributeError:
                pass

    # Handles game events
    def events(self):
        # Main event loop
        self.event_list = pygame.event.get()
        for event in self.event_list:
            if event.type == pygame.QUIT:
                self.running = False
                self.master.manager.exit()
                if self.training:
                    pygame.quit()
                    quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not self.ai_control:
                        menu.PauseScreen(self.master, self)
                    elif not self.training:
                        menu.PauseScreen(self.master, self, menu.AIScreen)
                    else:
                        menu.TrainingPauseScreen(self.master, self)
                if self.training:
                    if event.key == pygame.K_SPACE:
                        Game.cap = not Game.cap
                    if event.key == pygame.K_RIGHT:
                        Game.stage = (Game.stage + 1) % len(self.stages)
                        self.fps = FPS * self.stages[self.stage]
                    if event.key == pygame.K_LEFT:
                        Game.stage = (Game.stage - 1) % len(self.stages)
                        self.fps = FPS * self.stages[self.stage]

        try:
            # Remove birds that have left the screen
            birds = self.birds.sprites()
            if birds[0].rect.right < 0:
                birds[0].kill()

            # Remove birds behind planes from birds_infront
            bird = self.birds_infront[0]
            if bird.rect.right < self.players.sprites()[0].rect.left:
                self.birds_infront.pop(0)
        except IndexError:
            pass
        except AttributeError:
            pass

        # Calls random spawn method 'spawnrate' times per second
        try:
            Bird.lastspawn += 1
            spawn_bird = self.tickcount % (FPS // Bird.spawnrate) == 0
        except ZeroDivisionError:
            Bird.spawnrate = FPS  # Set spawnrate to FPS if it is set to a value greater than FPS
            spawn_bird = self.tickcount % (FPS // Bird.spawnrate) == 0
        finally:
            if spawn_bird:
                bird = Bird.random_spawn(self)
                if bird and self.ai_control:
                    self.birds_infront.append(bird)

    # Updates game sprites
    def update(self):
        self.all.update()

        # Moves plane(s) up or down depending on keyboard/neural network input(s)
        if self.ai_control:
            for player in self.players.sprites():
                inputs = self.get_inputs(player)
                outputs = self.ai_players[player][0].activate(inputs)
                max_output = max(outputs)
                if max_output >= 0.25:
                    index = outputs.index(max_output)
                    direction = 2*index - 1
                else:
                    direction = 0

                player.move(direction)

                # Remove fitness if planes stay still for too long
                try:
                    if player.lastmoved >= 2 * FPS:
                        self.ai_players[player][1].fitness -= 1
                except AttributeError:
                    pass
        else:
            keystate = pygame.key.get_pressed()
            direction = (keystate[pygame.K_s] or keystate[pygame.K_DOWN]) - \
                        (keystate[pygame.K_w] or keystate[pygame.K_UP])

            self.player.move(direction)

    # Draws to and updates the window
    def draw(self):
        self.all.draw(self.window)  # Draws all sprites to the window

        # Draw score to window
        scoretext = self.pixelfont.render(f"Score: {self.score}", False, WHITE)
        self.window.blit(scoretext, (5, 5))

        if self.training:
            # Draw generation number to window
            gentext = self.pixelfont.render(f"Gen: {self.population.generation}", False, WHITE)
            self.window.blit(gentext, (5, 40))

            # Draw number of planes alive to window
            alivetext = self.pixelfont.render(f"Alive: {len(self.players)}", False, WHITE)
            self.window.blit(alivetext, (5, 75))

            # Draw game speed
            if not self.cap:
                speedtext = self.pixelfont.render("Unlimited", False, WHITE)
            elif self.stage != 0:
                speedtext = self.pixelfont.render(f"{self.stages[self.stage]}x", False, WHITE)
            else:
                speedtext = self.pixelfont.render("", False, WHITE)

            self.window.blit(speedtext, (5, 110))

        pygame.display.update()

    # Make game get progressively harder
    def increase_difficulty(self):
        Bird.vel -= (0.3 / FPS)
        self.background.vel -= (0.2 / FPS)

        if Bird.spawnrate < FPS:  # Stop increasing spawnrate when it reaches FPS
            Bird.spawnrate += (1 / FPS)

        if Bird.maxtime > 0.25:  # Stop increasing maxtime when it reaches 0.25
            Bird.maxtime -= (0.07 / FPS)

    # Returns inputs for neural network
    def get_inputs(self, player):
        n = NUM_INPUTS
        inputs = [player.rect.centery] + [bird.rect.center[coord] - player.rect.center[coord]
                                          for bird in self.birds_infront for coord in range(2)]

        return inputs[:n] + [1000] * (n - len(inputs))

    # Creates game object for training the AI
    @classmethod
    def from_ai(cls, genomes, config):
        game = cls(cls.master, True, True, cls.quick_time)
        game.ai_players = {}  # Empty dictionary to link player sprites with their networks and genomes
        game.birds_infront = []  # List that will store all bird sprites in front of the plane
        game.fps = FPS * game.stages[game.stage]

        # Set game difficulty
        Bird.vel = -18
        Bird.spawnrate = 2
        Bird.maxtime = 0.5

        for genome_id, genome in genomes:
            genome.fitness = 0
            network = neat.nn.FeedForwardNetwork.create(genome, config)
            game.ai_players[Player(game)] = [network, genome]

        game.run()
        return game


# Train AI
def train_ai(master, ai_name, quick_time=False):
    # Load settings from NEAT config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, CONFIG_FILE)

    # Create population
    names = [name.lower() for name in get_instance_names()]
    if ai_name.lower() in names:  # If AI instance exists, continue training
        with open("ai-instances/index.csv") as file:
            reader = csv.reader(file)

            for row in reader:
                try:
                    if row[0].lower() == ai_name.lower() and len(row) > 1:
                        filepath = row[1]
                        checkpoint = neat.Checkpointer(None, None)
                        population = ExtendedPopulation.from_population(checkpoint.restore_checkpoint(filepath),
                                                                        ai_name)
                        break
                except IndexError:
                    pass
                except FileNotFoundError:
                    population = ExtendedPopulation(config, ai_name)
                    break

            else:
                population = ExtendedPopulation(config, ai_name)

    else:  # Else create new population
        population = ExtendedPopulation(config, ai_name)

    Game.master = master
    Game.population = population
    Game.stages = SPEED_STAGES
    Game.stage = 0
    Game.cap = True
    Game.quick_time = quick_time

    winner = population.run(Game.from_ai, 99999)  # Run AI and store best network in winner
    master.manager.switch(menu.AIScreen, master)


# Test AI
def test_ai(master, ai_name):
    # Load settings from NEAT config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, CONFIG_FILE)

    # Create game instance and set attributes
    game = Game(master, True)
    game.birds_infront = []  # Create empty list for tracking birds infront of plane
    game.ai_name = ai_name

    # Set game difficulty
    Bird.vel = -18
    Bird.spawnrate = 2
    Bird.maxtime = 0.5

    # Load best genome
    filepath = f"ai-instances/{ai_name}/best.pickle"
    try:
        with open(filepath, 'rb') as file:
            genome = pickle.load(file)
    except FileNotFoundError as e:
        print(f"Error: {e}. Please train the instance before testing")
        master.manager.switch(menu.AIScreen, master)
        return

    # Create neural network and player sprite, then link sprite, NN, and genome together
    network = neat.nn.FeedForwardNetwork.create(genome, config)
    player = Player(game)
    game.ai_players = {player: [network, genome]}

    game.run()
