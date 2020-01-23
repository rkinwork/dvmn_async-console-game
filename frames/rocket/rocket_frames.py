from pathlib import Path


def get_rockets_frames():
    """Init rocket animation frames."""
    frames_files = ['rocket_frame_1.txt', 'rocket_frame_2.txt']
    frames = [(Path(__file__).resolve().parent / frame_file_name).read_text() for frame_file_name in frames_files]

    return tuple(frames)
