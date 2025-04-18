import pygame
import os.path
import random
import yaml
import toml

from pygame.math import Vector2
from pygame.color import Color

from game_objects import Snake, Walls, Apple


# Set up global config
config_file = 'config.toml'

if os.path.isfile(config_file):
    config = toml.load(config_file)
else:
    print(f"Config file {config_file} not found. Using default settings.")
    config = {}

# Assign global config variables
screen_size =     Vector2(config.get('SCREEN_SIZE_X',     800), config.get('SCREEN_SIZE_Y',     800))
snake_grid_size = Vector2(config.get('SNAKE_GRID_SIZE_X', 10),  config.get('SNAKE_GRID_SIZE_Y', 10))
snake_default_textures =  config.get('SNAKE_DEFAULT_TEXTURES', "default.png")
food_default_textures =   config.get('FOOD_DEFAULT_TEXTURES',  "default.png")
walls_default_textures =  config.get('WALLS_DEFAULT_TEXTURES', "default.png")
initial_apples =      int(config.get('INITIAL_APPLES',       2))
default_apple_power = int(config.get('DEFAULT_APPLES_POWER', 1))
pause_key =  config.get('PAUSE_KEY', 'SPACE')
exit_key =   config.get('EXIT_KEY',  'ESCAPE')
tps =      float(config.get('TICK_PER_SECOND', 2))
wall_map =       config.get('WALLS_MAP', 'default.csv')
bg_color = Color(config.get('BACKGROUND_COLOR', '#eeeeee'))

snake_grid_thikness = Vector2(screen_size.x // snake_grid_size.x, screen_size.y // snake_grid_size.y)


# Apple generator function
def apple_spawner(snakes: list[Snake], walls: Walls, apples_local: list[Apple]) -> Apple:

    # Create a list with every spot in the grid
    spots = []
    for x in range(int(snake_grid_size.x)):
        for y in range(int(snake_grid_size.y)):
            spots.append(Vector2(x*snake_grid_thikness.x, y*snake_grid_thikness.y))
    
    # Remove the spots where the snakes are
    for snake in snakes:
        if snake.pos in spots: spots.remove(snake.pos)
        for piece in snake.pieces:
            if piece in spots: spots.remove(piece)
    
    # Remove the spots where the walls are
    for wall in walls.custom_walls:
        if wall in spots: spots.remove(wall)

    # Fix: Remove spots where apples already exist
    for apple in apples_local:
        if apple.pos in spots: spots.remove(apple.pos)
    
    if len(spots) == 0:
        print('No space to spawn new food, removing one, total food remaining:', len(apples_local))
        return None

    pos = random.choice(spots)
    return Apple(pos, default_apple_power, snake_grid_thikness, food_default_textures)


# Initialize pygame
pygame.init()
display = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()

# Load walls
walls = Walls(screen_size,wall_map,snake_grid_thikness,walls_default_textures)

original_exit_key = str(exit_key)
# Translate exit and pause keys
pause_key = pygame.key.key_code(pause_key)
exit_key = pygame.key.key_code(exit_key)

# Load the players
snakes: list[Snake] = []
for filename in os.listdir('players'):
    if filename.endswith(".yml"):
        with open('players/'+filename, 'r') as file:
            player_data = yaml.safe_load(file)
            snakes.append(
                Snake(
                    name=player_data['name'],
                    keybindings=player_data['keybindings'],
                    thikness=snake_grid_thikness,
                    textures=player_data['textures'],
                    pos=Vector2(player_data['starting_pos'][0]*snake_grid_thikness.x,player_data['starting_pos'][1]*snake_grid_thikness.y),
                    length=player_data['starting_length']
                    )
                )

apples: list[Apple] = []
for _ in range(initial_apples):
    apples.append(apple_spawner(snakes, walls, apples))

paused = False

while True:

    # Get events
    for event in pygame.event.get():

        # Quit when closing the window
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        # KEYBOARD PRESS EVENTS
        if event.type == pygame.KEYDOWN:
            
            # Quality of life, quit when ESC
            if event.key == exit_key:
                pygame.quit()
                quit()
            
            elif event.key == pause_key:
                paused = not paused

            if paused:
                continue

            # Update snakes moves
            for snake in snakes:
                if event.key in snake.keybindings:
                    snake.move(event.key)
    
    # Winning condition
    if len(apples) == 0 and paused == False:
        paused = True
        print('Game over, you won!')
        print(f'press {original_exit_key} to exit')


    if paused:
        clock.tick(60)
        continue

    
    # Update snakes logics
    for snake in snakes:

        # Update the position
        snake.update()

        # Check for walls collisions
        if snake in walls:
            snake.kill()
            snakes.remove(snake)
            continue
        
        # Check for collision with itself
        if snake.pos in snake.pieces:
            snake.kill()
            snakes.remove(snake)
            continue
        
        # Check fro snake to snake collisions
        snakes_copy = snakes[:]
        snakes_copy.remove(snake)
        for second_snake in snakes_copy:
            # Head to head collision
            if snake.pos == second_snake.pos:
                snake.kill()
                second_snake.kill()
                snakes.remove(snake)
                snakes.remove(second_snake)
                break
            # Head to tail collision
            if snake.pos in second_snake.pieces:
                snake.kill()
                snakes.remove(snake)
                break
        
        # If no collision was found then continue
        else:

            # Check for apple collisions
            for apple in apples:
                if apple.pos == snake.pos:
                    # Update the snake
                    snake.eat(apple.power)
                    # Remove the pervious apple from the list and add a new one
                    apples.remove(apple)
                    apples.append(apple_spawner(snakes,walls,apples))
                    break
    
    
    # Quit by game over
    if not len(snakes):
        print('Game over, every one is dead.')
        pygame.quit()
        quit()


    # Clear the screen and update
    display.fill(bg_color)

    # Draw the snakes in whatever state they are
    for snake in snakes:
        snake.frame(display)

    # Remove None elements from apple list, None elements are created by the apple spawner
    apples = list(filter(lambda x: x is not None, apples))

    # Draw the apples
    for apple in apples:
        apple.frame(display)

    # Draw the walls
    walls.frame(display)

    pygame.display.update()

    # Limit the refresh rate to the tps
    clock.tick(tps)