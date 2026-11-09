import random
from types import CellType
from typing import TYPE_CHECKING
from collections import defaultdict
from typing import DefaultDict

if TYPE_CHECKING:
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


# Current get_door_candidates is only obtaining valid placements from walls that are straight
# Diagonal placement of walls cannot be considered as candidates, which hinders possible door placements
# Can be solved in internDoorPlacement() by just adding walls adjacent to doors
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
    print("doorExtras:", doorExtras)
    for _ in range(doorExtras):
        room_pair, placements = random.choice(list(grouped_candidates.items()))
        print("a room_pair:", room_pair, "a placements:", placements)
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
