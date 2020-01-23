import asyncio
from curses_tools import draw_frame, get_frame_size

GAME_OVER_TEXT = \
    """\
       _____                         ____                 
      / ____|                       / __ \                
     | |  __  __ _ _ __ ___   ___  | |  | |_   _____ _ __ 
     | | |_ |/ _` | '_ ` _ \ / _ \ | |  | \ \ / / _ \ '__|
     | |__| | (_| | | | | | |  __/ | |__| |\ V /  __/ |   
      \_____|\__,_|_| |_| |_|\___|  \____/  \_/ \___|_|"""


async def show_gameover(canvas, center_row, center_column):
    rows, columns = get_frame_size(GAME_OVER_TEXT)
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    while True:
        draw_frame(canvas, corner_row, corner_column, GAME_OVER_TEXT)
        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, GAME_OVER_TEXT, negative=True)
