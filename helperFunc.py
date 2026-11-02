import sys
import math
import random
import minescript as ms

# Function to check if blocks adjacent to initial placements exist
def hasRoomConflict(roomBlocks, occupiedBlocks):
        for x, y, z in roomBlocks:
            if (x, y, z) in occupiedBlocks:
                return True

            adjacentBlocks = (
                (x + 1, y, z),
                (x - 1, y, z),
                (x, y, z + 1),
                (x, y, z - 1),
            )
            if occupiedBlocks.intersection(adjacentBlocks):
                return True

        return False
    

    
"""Current peeves: 
    - Random choice sometimes lead room placements to clump to one side, might need to have weighted distribution?
    
"""

# Initalizes placement of rooms to start room growth
# Returns a key:value dictionary
    # Key: Room number
    # Value: list of initial coordinates of a room
def initPlacement(totalRooms, length, width, startX, foundationY, startZ):
    
    # 
    roomDict = {}
    occupiedBlocks = set()

    if totalRooms <= 0:
        return roomDict
    if length < 2 or width < 2:
        raise ValueError("The foundation must be at least 2x2 blocks")


    for i in range(totalRooms):
        # Keep list of available rooms to randomly choose
        availableRooms = []
        
        for side in ("top", "bottom"):
            for offset in range(width - 1):
                originX = startX + offset
                if side == "top":
                    originZ = startZ 
                else:
                    originZ = startZ + length - 2
                roomBlocks = [
                    (originX, foundationY, originZ),
                    (originX + 1, foundationY, originZ),
                    (originX, foundationY, originZ + 1),
                    (originX + 1, foundationY, originZ + 1),
                ]
                if not hasRoomConflict(roomBlocks, occupiedBlocks):
                    availableRooms.append(roomBlocks)

        for side in ("left", "right"):
            for offset in range(length - 1):
                if side == "left":
                    originX = startX 
                else:
                    originX = startX + width - 2
                originZ = startZ + offset
                roomBlocks = [
                    (originX, foundationY, originZ),
                    (originX + 1, foundationY, originZ),
                    (originX, foundationY, originZ + 1),
                    (originX + 1, foundationY, originZ + 1),
                ]
                if not hasRoomConflict(roomBlocks, occupiedBlocks):
                    availableRooms.append(roomBlocks)

        if not availableRooms:
            raise ValueError("Not enough room for non-overlapping 2x2 rooms")

        roomBlocks = random.choice(availableRooms)
        roomDict[i] = roomBlocks
        
        # Add block coordinates to occupied blocks so it doesn't choose room placement
        occupiedBlocks.update(roomBlocks)
        
    
    # To check inital placements visually in the world    
    for v in roomDict.values():
        for x, y, z in v:
            ms.execute(f"setblock {x} {y + 2} {z} minecraft:oak_wood")


    return roomDict