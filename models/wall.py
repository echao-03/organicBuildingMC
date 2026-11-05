class WallColumn:
    """A vertical column of wall blocks, stored bottom-to-top as cells[y].

    Building.wall_columns supplies the column's local (x, z) position.
    Y is a local height offset. Columns can form interior or exterior walls.

    We store wall columns to more easily represent rooms which are not rectangular.
    """

    WOOD = 0
    GLASS = 1

    def __init__(self, height: int) -> None:
        if height <= 0:
            raise ValueError("Wall height must be positive")

        self.height = height
        self.cells: list[int] = [self.WOOD for _ in range(height)]
