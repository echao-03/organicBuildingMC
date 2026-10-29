import minescript as ms
import sys
import math






def main(args):
    
    # Taking argument as {number} x {number} grid
    lengthArg = int(args[0])
    widthArg = int(args[1])
    
    # Grabs current cursor target from raycasting
    cursorTarget = ms.player_get_targeted_block(max_distance=20)
        
    ms.echo(cursorTarget[0])
    x, y, z = cursorTarget[0]
    
    startX = x - (widthArg // 2)
    startZ = z - (lengthArg // 2)
    
    
    for i in range(widthArg):
        for j in range(lengthArg):
            ms.execute(f"setblock {startX + i} {y + 1} {startZ + j} minecraft:stone")

    # Calculated total area and cube root to obtain the total room
    totalRooms = math.floor((lengthArg * widthArg) ** (1 / 3) )

    # ms.echo(f"totalRooms is {totalRooms}")
    


if __name__ == "__main__":
    main(sys.argv[1:])

