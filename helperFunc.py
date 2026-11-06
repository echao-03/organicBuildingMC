import random
from types import CellType
from typing import TYPE_CHECKING

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


"""
Need to determine how many doors can be placed in the house
1. Get totalRoom integer, use random.randint between (1 - totalRoom)
2. Obtain valid tiles that doesn't have an ID of a room
3. Add walls to valid tiles
    Once obtain all valid tiles, begin loop through range(random.randint(1 - totalRoom))
        Pick random valid tile, and obtain adjacency IDs from current tile
        Conditions:
            - If tile is next to external wall,
                - If there is a wall next to door placement, then proceed with placing door
                - If no wall, place wall adjacent from external wall 
            - If tile is away from external wall, 
            
"""


def internWallPlacement(floorplan: "Floorplan") -> None:
    for x in range(floorplan.width):
        for z in range(floorplan.length):
            cell = floorplan.get_cell(x, z)
            if cell is None:
                floorplan.set_cell(x, z, -1)


# def internDoorPlacement(floorplan: "Floorplan", totalRooms: int) -> None:
#     # If the total house only has one room, no need for internal doors
#     if totalRooms == 1:
#         return

#     totalDoors = random.randint(1, totalRooms)

#     for door in range(totalDoors):
