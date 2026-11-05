import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.floorplan import Floorplan

def hasRoomConflict(floorplan: "Floorplan", roomBlocks: list[tuple[int, int]]) -> bool:
    """Check local (x, z) candidates for occupied cells or adjacent rooms.
    """
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
    

    
"""Current peeves: 
    - Random choice sometimes lead room placements to clump to one side, might need to have weighted distribution?
    
"""

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
                if not hasRoomConflict(floorplan, roomBlocks):
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
                if not hasRoomConflict(floorplan, roomBlocks):
                    availableRooms.append(roomBlocks)

        if not availableRooms:
            raise ValueError("Not enough room for non-overlapping 2x2 rooms")

        roomBlocks = random.choice(availableRooms)
        for x, z in roomBlocks:
            floorplan.set_cell(x, z, i)
