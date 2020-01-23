import random
import time
import asyncio
import curses

from curses_tools import draw_frame, read_controls, get_frame_size
from frames.rocket.rocket_frames import get_rockets_frames
from frames.garbage.garbage_frames import get_garbage_frames
from psysics import update_speed
from explosion import explode
from game_over import show_gameover
from obstacles import Obstacle, show_obstacles
from game_scenario import PHRASES, get_garbage_delay_tics

TIC_TIMEOUT = 0.1
STAR_SHAPES = '+*.:'
FRAME_BORDER_SIZE = 1
YEAR_TICS = int(1.5 / TIC_TIMEOUT)
INFO_WINDOW_WIDTH = 50
PLASMA_GUN_ERA = 2020
DEV_MODE = False

# global variables
space_objects = []
obstacles = []
obstacles_in_last_collisions = []
rocket_frames = get_rockets_frames()
spaceship_frame = rocket_frames[0]
year = 1957


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def change_years():
    global year
    while True:
        for _ in range(YEAR_TICS):
            await asyncio.sleep(0)
        year += 1


async def show_messages(canvas):
    """Shows year counter."""
    message_template = "Year: {} {}"
    while True:
        yr = message_template.format(year, PHRASES.get(year, ''))
        draw_frame(canvas, 0, 0, yr)
        await asyncio.sleep(0)
        draw_frame(canvas, 0, 0, yr, negative=True)


async def animate_spaceship():
    """Animates spaceship."""
    global spaceship_frame
    while True:
        for frame in rocket_frames:
            spaceship_frame = frame
            await sleep()


async def run_spaceship(canvas, start_row, start_col):
    """Display spaceship and moves it on canvas."""
    row, column = start_row, start_col
    row_speed, column_speed = 0, 0
    min_row, min_column = FRAME_BORDER_SIZE, FRAME_BORDER_SIZE
    max_row, max_column = get_max_height_width_of_canvas(canvas)

    while True:
        temp_spaceship_frame = spaceship_frame
        frame_size = get_frame_size(temp_spaceship_frame)

        move_row, move_column, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, move_row, move_column)
        row, column = row + row_speed, column + column_speed

        column = min(max(min_column, column), max_column - frame_size[1] - FRAME_BORDER_SIZE)
        row = min(max(min_row, row), max_row - frame_size[0] - FRAME_BORDER_SIZE)

        collisions = [obstacle
                      for obstacle in obstacles if obstacle.has_collision(row, column, frame_size[0], frame_size[1])]
        if collisions:
            await show_gameover(canvas, start_row, start_col)

        if space_pressed and year >= PLASMA_GUN_ERA:
            space_objects.append(fire(canvas, row, column + frame_size[1] // 2))

        draw_frame(canvas, row, column, temp_spaceship_frame)

        await sleep()
        draw_frame(canvas, row, column, temp_spaceship_frame, negative=True)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    max_row, max_column = get_max_height_width_of_canvas(canvas)
    # немного раздражает
    # curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')

        collisions = [obstacle
                      for obstacle in obstacles if obstacle.has_collision(round(row), round(column))]
        if collisions:
            obstacles_in_last_collisions.extend(collisions)
            return

        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, offset_tics, symbol='*'):
    """Display on blinking star on canvas."""
    animation_steps = (
        (int(2 / TIC_TIMEOUT), curses.A_DIM),
        (int(0.3 / TIC_TIMEOUT), curses.A_NORMAL),
        (int(0.5 / TIC_TIMEOUT), curses.A_BOLD),
        (int(0.3 / TIC_TIMEOUT), curses.A_NORMAL),
    )

    step, state = animation_steps[0]
    canvas.addstr(row, column, symbol, state)
    await sleep()

    # delay before start
    await sleep(offset_tics)

    while True:
        for step, state in animation_steps:
            canvas.addstr(row, column, symbol, state)
            await sleep(step)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    row_size, column_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, row_size, column_size)
    obstacles.append(obstacle)

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        obstacle.row, obstacle.column = row, column
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)

        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            await explode(canvas, row + row_size // 2, column + column_size // 2)
            break

        row += speed

    obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, max_width):
    """Fills canvas with garbage """
    garbage_objects = get_garbage_frames()

    while True:
        delay_tics = get_garbage_delay_tics(year)
        if delay_tics:
            space_objects.append(
                fly_garbage(canvas,
                            random.randint(FRAME_BORDER_SIZE, max_width - FRAME_BORDER_SIZE),
                            garbage_objects[random.randint(0, len(garbage_objects) - 1)]))

        await sleep(delay_tics or 1)


def get_max_height_width_of_canvas(canvas):
    """Get adjusted window size of window."""
    max_height, max_width = canvas.getmaxyx()
    return max_height - 1, max_width - 1


def draw(canvas):
    """Starts game in terminal."""
    curses.curs_set(False)
    canvas.border()
    canvas.refresh()
    canvas.nodelay(True)
    max_height, max_width = get_max_height_width_of_canvas(canvas)
    center_row, center_col = max_height // 2, max_width // 2

    info_window = canvas.derwin(1, INFO_WINDOW_WIDTH, max_height - FRAME_BORDER_SIZE, center_col)

    for _ in range(0, random.randint(100, 150)):
        space_objects.append(
            blink(canvas, random.randint(FRAME_BORDER_SIZE, max_height - FRAME_BORDER_SIZE),
                  random.randint(FRAME_BORDER_SIZE, max_width - FRAME_BORDER_SIZE),
                  random.randint(0, 20),
                  random.choice(STAR_SHAPES)))

    space_objects.append(animate_spaceship())
    space_objects.append(run_spaceship(canvas, center_row, center_col))
    space_objects.append(fill_orbit_with_garbage(canvas, max_width))
    space_objects.append(show_messages(info_window))
    space_objects.append(change_years())

    if DEV_MODE:
        space_objects.append(show_obstacles(canvas, obstacles))

    canvas.refresh()
    while True:
        exhausted_coroutines = []
        for space_object in space_objects:
            try:
                space_object.send(None)
            except StopIteration:
                exhausted_coroutines.append(space_object)

        canvas.border()
        canvas.refresh()
        info_window.refresh()
        time.sleep(TIC_TIMEOUT)
        for coroutine_to_remove in exhausted_coroutines:
            space_objects.remove(coroutine_to_remove)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
