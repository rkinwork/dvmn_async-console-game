from pathlib import Path


def get_garbage_frames():
    """Init list with garbage objects."""
    garbage_objects = [garbage_object.read_text() for garbage_object in Path(__file__).resolve().parent.glob('*.txt')]
    return garbage_objects
