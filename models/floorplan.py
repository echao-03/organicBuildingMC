class Floorplan:
    """A top-down grid of the building using local (x, z) coordinates.
    Rooms within a Building share a Floorplan.
    Cells contain UNASSIGNED, WALL, DOOR, or room_id >= 0.
    """

    UNASSIGNED = None
    WALL = -1
    DOOR = -2

    def __init__(self, width: int, length: int) -> None:
        if width <= 0 or length <= 0:
            raise ValueError("Width and length must be positive")

        self.width = width
        self.length = length
        self.cells: list[list[int | None]] = [
            [self.UNASSIGNED for _ in range(length)]
            for _ in range(width)
        ]

    def _check_coordinates(self, x: int, z: int) -> None:
        if not (0 <= x < self.width and 0 <= z < self.length):
            raise IndexError(f"Cell ({x}, {z}) is outside the floorplan")

    def get_cell(self, x: int, z: int) -> int | None:
        """Return the state at (x, z)."""
        self._check_coordinates(x, z)
        return self.cells[x][z]

    def set_cell(self, x: int, z: int, value: int | None) -> None:
        """Set a cell to a room ID, WALL, DOOR, or UNASSIGNED."""
        self._check_coordinates(x, z)
        if value is not None:
            if value < -2:
                raise ValueError("Room IDs must be nonnegative")
        self.cells[x][z] = value

    def pretty_print(self) -> None:
        """Print the floorplan with X increasing rightward and Z downward."""
        symbols: dict[int | None, str] = {
            self.UNASSIGNED: ".", self.WALL: "#", self.DOOR: "D"
        }
        rows = [
            [symbols.get(self.cells[x][z], str(self.cells[x][z]))
             for x in range(self.width)]
            for z in range(self.length)
        ]
        cell_width = max(len(symbol) for row in rows for symbol in row)
        for row in rows:
            print(" ".join(symbol.rjust(cell_width) for symbol in row))
        print("Legend: . = unassigned, # = wall, D = door, numbers = room IDs")
