import os
from pathlib import Path
import random
import time
import asyncio
import curses

from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1
STAR_SHAPES = '+*.:'
FRAME_BORDER_SIZE = 1


async def animate_spaceship(canvas, start_row, start_col):
    """Display spaceship and moves it on canvas."""
    row, column = start_row, start_col
    min_row, min_column = FRAME_BORDER_SIZE, FRAME_BORDER_SIZE
    max_row, max_column = get_max_height_width_of_canvas(canvas)
    frames_files = ['rocket_frame_1.txt', 'rocket_frame_2.txt']
    frames = []
    for frame_file_name in frames_files:
        with open(os.path.join(Path(__file__).parent, 'frames', frame_file_name)) as f:
            frame = f.read()
            frame_row, frame_col = get_frame_size(frame)
            frames.append((frame, (frame_row, frame_col)))

    while True:
        for frame, frame_size in frames:
            move_row, move_column, space_pressed = read_controls(canvas)
            row += move_row
            column += move_column

            column = min(max(min_column, column), max_column - frame_size[1] - FRAME_BORDER_SIZE)
            row = min(max(min_row, row), max_row - frame_size[0] - FRAME_BORDER_SIZE)

            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, frame, negative=True)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    max_row, max_column = get_max_height_width_of_canvas(canvas)
    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
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
    await asyncio.sleep(0)

    # delay before start
    for i in range(offset_tics):
        await asyncio.sleep(0)

    while True:
        for step, state in animation_steps:
            for i in range(step):
                canvas.addstr(row, column, symbol, state)
                await asyncio.sleep(0)


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
    space_objects = []

    for _ in range(0, random.randint(100, 150)):
        space_objects.append(
            blink(canvas, random.randint(FRAME_BORDER_SIZE, max_height - FRAME_BORDER_SIZE),
                  random.randint(FRAME_BORDER_SIZE, max_width - FRAME_BORDER_SIZE),
                  random.randint(0, 20),
                  random.choice(STAR_SHAPES)))

    space_objects.append(fire(canvas, center_row, center_col))
    space_objects.append(animate_spaceship(canvas, center_row, center_col))

    canvas.refresh()
    while True:
        exhausted_coroutines = []
        for star_show in space_objects:
            try:
                star_show.send(None)
            except StopIteration:
                exhausted_coroutines.append(star_show)

        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)
        for coroutine_to_remove in exhausted_coroutines:
            space_objects.remove(coroutine_to_remove)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
