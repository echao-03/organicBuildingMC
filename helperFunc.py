import random
from types import CellType
from typing import TYPE_CHECKING
from collections import defaultdict
from typing import DefaultDict

from models.wall import WallColumn

from typing import TypeAlias

# Type alias for readability
CellGrid: TypeAlias = list[list[int]]
GenerationRound: TypeAlias = tuple[CellGrid, int | None]
GenerationHistory: TypeAlias = list[GenerationRound]
ExternalWallResult: TypeAlias = tuple[list[WallColumn], GenerationHistory]

if TYPE_CHECKING:
    from models.building import Building
    from models.floorplan import Floorplan


def hasRoomConflict(floorplan: "Floorplan", roomBlocks: list[tuple[int, int]]) -> bool:
    """Check local (x, z) candidates for occupied cells or adjacent rooms."""
    for x, z in roomBlocks:
        if not (0 <= x < floorplan.width and 0 <= z < floorplan.length):
            return True
        if floorplan.get_cell(x, z) is not floorplan.UNASSIGNED:
            return True

        adjacentBlocks = (
            (x + 1, z),
            (x - 1, z),
            (x, z + 1),
            (x, z - 1),
        )

        # Check for adjoining rooms
        for adjacentX, adjacentZ in adjacentBlocks:
            if 0 <= adjacentX < floorplan.width and 0 <= adjacentZ < floorplan.length:
                value = floorplan.get_cell(adjacentX, adjacentZ)
                if value is not None and value >= 0:
                    return True

    return False


def chooseRoomSeed(
    availableRooms: list[list[tuple[int, int]]],
    placedOrigins: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    if not availableRooms:
        raise ValueError("Not enough room for non-overlapping 2x2 rooms")

    if not placedOrigins:
        return random.choice(availableRooms)

    def distanceToNearestRoom(candidates: list[tuple[int, int]]) -> int:
        x, z = candidates[0]
        return min(
            (x - placedX) ** 2 + (z - placedZ) ** 2
            for placedX, placedZ in placedOrigins
        )

    distances = [distanceToNearestRoom(candidates) for candidates in availableRooms]
    bestDistance = max(distances)

    bestCandidates = [
        candidate
        for candidate, distance in zip(availableRooms, distances)
        if distance == bestDistance
    ]

    return random.choice(bestCandidates)


def initPlacement(floorplan: "Floorplan", totalRooms: int) -> None:
    """Place initial 2x2 room seeds along a floorplan's perimeter in place.

    Room IDs run from 0 to totalRooms - 1; call before adding other rooms.
    If space runs out, raise ValueError and leave already placed seeds intact.
    """
    if totalRooms <= 0:
        return

    length = floorplan.length
    width = floorplan.width
    if length < 2 or width < 2:
        raise ValueError("The foundation must be at least 2x2 blocks")

    placedOrigins: list[tuple[int, int]] = []

    for i in range(totalRooms):
        availableRooms = []

        for side in ("top", "bottom"):
            for offset in range(width - 1):
                originX = offset
                if side == "top":
                    originZ = 0
                else:
                    originZ = length - 2
                roomBlocks = [
                    (originX, originZ),
                    (originX + 1, originZ),
                    (originX, originZ + 1),
                    (originX + 1, originZ + 1),
                ]
                if roomBlocks not in availableRooms and not hasRoomConflict(
                    floorplan, roomBlocks
                ):
                    availableRooms.append(roomBlocks)

        for side in ("left", "right"):
            for offset in range(length - 1):
                if side == "left":
                    originX = 0
                else:
                    originX = width - 2
                originZ = offset
                roomBlocks = [
                    (originX, originZ),
                    (originX + 1, originZ),
                    (originX, originZ + 1),
                    (originX + 1, originZ + 1),
                ]
                if roomBlocks not in availableRooms and not hasRoomConflict(
                    floorplan, roomBlocks
                ):
                    availableRooms.append(roomBlocks)

        if not availableRooms:
            break

        roomBlocks = chooseRoomSeed(availableRooms, placedOrigins)
        for x, z in roomBlocks:
            floorplan.set_cell(x, z, i)

        placedOrigins.append(roomBlocks[0])


def getGrowthCandidates(
    floorplan: "Floorplan",
    roomId: int,
) -> list[tuple[int, int]]:

    candidates = []

    for x in range(floorplan.width):
        for z in range(floorplan.length):
            if floorplan.get_cell(x, z) is not floorplan.UNASSIGNED:
                continue

            adjacentRooms = set()

            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                adjacentX = x + dx
                adjacentZ = z + dz

                if (
                    0 <= adjacentX < floorplan.width
                    and 0 <= adjacentZ < floorplan.length
                ):
                    value = floorplan.get_cell(adjacentX, adjacentZ)

                    if value is not None and value >= 0:
                        adjacentRooms.add(value)

            if adjacentRooms == {roomId}:
                candidates.append((x, z))

    return candidates


def growRooms(floorplan: "Floorplan", showGrowth: bool = False) -> None:
    roomIds = sorted(
        {
            cell
            for column in floorplan.cells
            for cell in column
            if cell is not None and cell >= 0
        }
    )
    rounds = 0

    if showGrowth:
        print("\nRound 0: initial seeds")
        floorplan.pretty_print()

    while True:
        random.shuffle(roomIds)
        grew = False

        for roomId in roomIds:
            candidates = getGrowthCandidates(floorplan, roomId)

            if candidates:
                x, z = random.choice(candidates)
                floorplan.set_cell(x, z, roomId)
                grew = True

        if not grew:
            if showGrowth:
                print(f"\nGrowth finished after {rounds} growth rounds.")
            return

        rounds += 1

        if showGrowth:
            print(f"\nRound {rounds}")
            floorplan.pretty_print()


def internWallPlacement(floorplan: "Floorplan") -> None:
    for x in range(floorplan.width):
        for z in range(floorplan.length):
            cell = floorplan.get_cell(x, z)
            if cell is None:
                floorplan.set_cell(x, z, -1)


def _generate_external_wall(
    height: int,
    span: int,
    # Returns a tuple (list, list), list of newly created walls, and history of wall generations
) -> ExternalWallResult:
    cells = [
        [
            # Change float if you want to change total distribution of glass
            WallColumn.GLASS if random.random() < 0.25 else WallColumn.WOOD
            for _ in range(span)
        ]
        for _ in range(height)
    ]
    history = [([row[:] for row in cells], None)]

    # Main loop for cellular automata of glass blocks (range = # of generations)
    for round_number in range(1, 11):
        next_cells = [[WallColumn.WOOD for _ in range(span)] for _ in range(height)]
        for y in range(height):
            for offset in range(span):
                neighbors = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
                total = sum(
                    cells[y + dy][offset + dx]
                    for dx, dy in neighbors
                    # Check adjacent neighbor of current block, and if neighbor + current height of block is higher than set building height, then skip
                    if 0 <= y + dy < height and 0 <= offset + dx < span
                )
                next_cells[y][offset] = (
                    WallColumn.GLASS if total in (2, 3) else WallColumn.WOOD
                )
        changed_cells = sum(
            cells[y][offset] != next_cells[y][offset]
            for y in range(height)
            for offset in range(span)
        )
        cells = next_cells
        history.append(([row[:] for row in cells], changed_cells))

    columns = []
    for offset in range(span):
        column = WallColumn(height)
        column.cells = [cells[y][offset] for y in range(height)]
        columns.append(column)
    return columns, history


def externWallPlacements(building: "Building") -> None:
    """Generate four cellular-automata walls around a building footprint."""
    width = building.width
    length = building.length

    building.wall_columns = {
        coordinates: column
        for coordinates, column in building.wall_columns.items()
        if 0 <= coordinates[0] < width and 0 <= coordinates[1] < length
    }

    # obtain arrays of the wall, as well as another array for past wall generations
    north_wall, north_history = _generate_external_wall(building.height + 1, width + 2)
    south_wall, south_history = _generate_external_wall(building.height + 1, width)
    west_wall, west_history = _generate_external_wall(building.height + 1, length + 1)
    east_wall, east_history = _generate_external_wall(building.height + 1, length + 1)
    building.wall_generation_history = {
        "North": north_history,
        "South": south_history,
        "West": west_history,
        "East": east_history,
    }

    for offset, column in enumerate(north_wall):
        building.wall_columns[(offset - 1, -1)] = column
    for offset, column in enumerate(south_wall):
        building.wall_columns[(offset, length)] = column
    for offset, column in enumerate(west_wall):
        building.wall_columns[(-1, offset)] = column
    for offset, column in enumerate(east_wall):
        building.wall_columns[(width, offset)] = column

    # If door is already implemented, then continue
    if building.external_door is not None:
        inside, outside = building.external_door
    # Randomly choose which side to install a door
    else:
        side, offset = random.choice(
            [("north", x) for x in range(width)]
            + [("south", x) for x in range(width)]
            + [("west", z) for z in range(length)]
            + [("east", z) for z in range(length)]
        )
        if side == "north":
            inside, outside = (offset, 0), (offset, -1)
        elif side == "south":
            inside, outside = (offset, length - 1), (offset, length)
        elif side == "west":
            inside, outside = (0, offset), (-1, offset)
        else:
            inside, outside = (width - 1, offset), (width, offset)

    building.external_door = (inside, outside)


def is_room(value) -> bool:
    return isinstance(value, int) and value >= 0


def get_door_candidates(floorplan: "Floorplan"):
    candidates = []

    for x in range(1, floorplan.width - 1):
        for z in range(1, floorplan.length - 1):
            if floorplan.get_cell(x, z) != floorplan.WALL:
                continue

            # Door dividing rooms left/right.
            left = floorplan.get_cell(x - 1, z)
            right = floorplan.get_cell(x + 1, z)
            side_walls = (
                floorplan.get_cell(x, z - 1),
                floorplan.get_cell(x, z + 1),
            )

            if (
                isinstance(left, int)
                and left >= 0
                and isinstance(right, int)
                and right >= 0
                and left != right
                and any(value == floorplan.WALL for value in side_walls)
            ):
                candidates.append(((x, z), left, right))

            # Door dividing rooms up/down.
            above = floorplan.get_cell(x, z - 1)
            below = floorplan.get_cell(x, z + 1)
            side_walls = (
                floorplan.get_cell(x - 1, z),
                floorplan.get_cell(x + 1, z),
            )

            if (
                isinstance(above, int)
                and above >= 0
                and isinstance(below, int)
                and below >= 0
                and above != below
                and any(value == floorplan.WALL for value in side_walls)
            ):
                candidates.append(((x, z), above, below))
                

            # # Door dividing rooms diagonally: northwest/southeast.
            # northwest = floorplan.get_cell(x - 1, z - 1)
            # southeast = floorplan.get_cell(x + 1, z + 1)

            # if is_room(northwest) and is_room(southeast) and northwest != southeast:
            #     candidates.append(((x, z), northwest, southeast))

            # # Door dividing rooms diagonally: northeast/southwest.
            # northeast = floorplan.get_cell(x + 1, z - 1)
            # southwest = floorplan.get_cell(x - 1, z + 1)

            # if is_room(northeast) and is_room(southwest) and northeast != southwest:
            #     candidates.append(((x, z), northeast, southwest))

    return candidates


def group_door_candidates(floorplan: "Floorplan"):
    grouped: DefaultDict[tuple[int, int], list[tuple[tuple[int, int], int, int]]] = (
        defaultdict(list)
    )

    for candidate in get_door_candidates(floorplan):
        coordinates, room_a, room_b = candidate
        room_pair = tuple(sorted((room_a, room_b)))

        grouped[room_pair].append(candidate)

    return grouped


def internDoorPlacement(floorplan: "Floorplan", totalRooms: int) -> None:
    # If the total house only has one room, no need for internal doors
    if totalRooms == 1:
        return

    grouped_candidates = group_door_candidates(floorplan)

    # Initial door placements, makes sure that every rooms are connected once
    for room_pair, placements in grouped_candidates.items():
        print("room_pair:", room_pair, "placements:", placements)
        coordinates, room_a, room_b = random.choice(placements)
        x, z = coordinates
        floorplan.set_cell(x, z, floorplan.DOOR)
        grouped_candidates[room_pair].remove((coordinates, room_a, room_b))

    # Add extra doors and randomly choose any from grouped_candidates

    doorExtras = random.randint(1, totalRooms - 1)
    for _ in range(doorExtras):
        room_pair, placements = random.choice(list(grouped_candidates.items()))
        if len(placements) == 0:
            continue
        coordinates, room_a, room_b = random.choice(placements)
        x, z = coordinates
        floorplan.set_cell(x, z, floorplan.DOOR)
        grouped_candidates[room_pair].remove((coordinates, room_a, room_b))

    # Final check of all doors and add walls if necessary
    for x in range(1, floorplan.width - 1):
        for z in range(1, floorplan.length - 1):

            if floorplan.get_cell(x, z) == floorplan.DOOR:
                left = floorplan.get_cell(x - 1, z)
                right = floorplan.get_cell(x + 1, z)
                above = floorplan.get_cell(x, z - 1)
                below = floorplan.get_cell(x, z + 1)

                # If left and right are rooms, check above and below for walls and doors
                if (
                    isinstance(left, int)
                    and left >= 0
                    and isinstance(right, int)
                    and right >= 0
                ):
                    if isinstance(above, int) and (
                        above == floorplan.WALL or above == floorplan.DOOR
                    ):
                        floorplan.set_cell(x, z + 1, floorplan.WALL)

                    if isinstance(below, int) and (
                        below == floorplan.WALL or below == floorplan.DOOR
                    ):
                        floorplan.set_cell(x, z - 1, floorplan.WALL)
                # If above and below are rooms, check left and right for walls and doors
                if (
                    isinstance(above, int)
                    and above >= 0
                    and isinstance(below, int)
                    and below >= 0
                ):

                    if isinstance(left, int) and (
                        left == floorplan.WALL or left == floorplan.DOOR
                    ):
                        floorplan.set_cell(x + 1, z, floorplan.WALL)

                    if isinstance(right, int) and (
                        right == floorplan.WALL or right == floorplan.DOOR
                    ):
                        floorplan.set_cell(x - 1, z, floorplan.WALL)
