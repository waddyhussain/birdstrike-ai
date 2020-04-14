# Constants for screen dimensions
WIDTH = 950
HEIGHT = 650

# Window title and FPS
TITLE = "Birdstrike"
FPS = 60

# Bird spawn settings
INITIAL_BIRD_PROBABILITY = 0.5  # Average chance of bird spawning each second
INITIAL_SPAWNRATE = 6  # Max number of birds that can spawn each second (If greater than FPS, will be set to FPS)
INITIAL_MAXTIME = 3  # Maximum time in seconds that can pass without a bird spawning

# Config file location
CONFIG_FILE = "config-feedforward.txt"

# AI Settings
NUM_BIRDS_INPUT = 2
NUM_INPUTS = NUM_BIRDS_INPUT * 2 + 1
SPEED_STAGES = [1, 2, 3, 5, 10]

# Colour constants
BLACK = (0, 0, 0)
DIMMED_BLACK = (0, 0, 0, 175)
WHITE = (255, 255, 255)
DIMMED_WHITE = (175, 175, 175)
LIGHT_BLUE = (3, 168, 244)
