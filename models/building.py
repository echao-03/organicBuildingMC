from .floorplan import Floorplan
from .wall import WallColumn


class Building:
    """A rectangular building with a shared Floorplan and vertical wall columns.

    Walls are keyed by local (x, z) coordinates for interior and exterior walls.
    """

    def __init__(self, origin: tuple[int, int, int], width: int,
                 length: int, height: int) -> None:
        if width <= 0 or length <= 0 or height <= 0:
            raise ValueError("Building dimensions must be positive")

        self.origin = tuple(origin)
        self.width = width
        self.length = length
        self.height = height
        # Represents the bottom-most slice of the building.
        self.floorplan = Floorplan(width, length)
        # Store the wall as columns, since rooms are not rectangular.
        self.wall_columns: dict[tuple[int, int], WallColumn] = {}
