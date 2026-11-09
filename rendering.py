from models import Building, Floorplan, WallColumn


def _door_facing(building: Building, x: int, z: int) -> str:
    """Face across the wall; ambiguous layouts default to north."""

    def is_wall(nx: int, nz: int) -> bool:
        if not (0 <= nx < building.width and 0 <= nz < building.length):
            return False
        return (nx, nz) in building.wall_columns or building.floorplan.get_cell(
            nx, nz
        ) in (Floorplan.WALL, Floorplan.DOOR)

    along_x = sum(is_wall(nx, z) for nx in (x - 1, x + 1))
    along_z = sum(is_wall(x, nz) for nz in (z - 1, z + 1))
    return "east" if along_z > along_x else "north"


def _block_at(building: Building, x: int, y: int, z: int) -> str:

    # Foundation base
    if y == -1:
        return "spruce_planks"
    cell = building.floorplan.get_cell(x, z)
    if cell == Floorplan.DOOR and y < 2:
        if building.height < 2:
            raise ValueError("Doors require a building height of at least 2")
        half = "lower" if y == 0 else "upper"
        facing = _door_facing(building, x, z)
        return (
            f"oak_door[facing={facing},half={half},hinge=left,open=false,powered=false]"
        )
    column = building.wall_columns.get((x, z))
    if column is not None:
        if y >= column.height:
            return "air"
        return {WallColumn.WOOD: "oak_wood", WallColumn.GLASS: "glass"}[column.cells[y]]

    # Wall blocks
    if cell in (Floorplan.WALL, Floorplan.DOOR):
        return "oak_planks"
    return "air"


def render_minecraft(building: Building) -> None:
    """Place the foundation and all building layers, including clearing air."""
    import minescript as ms

    if building.height < 2 and any(
        Floorplan.DOOR in column for column in building.floorplan.cells
    ):
        raise ValueError("Doors require a building height of at least 2")
    origin_x, origin_y, origin_z = building.origin
    for y in range(-1, building.height):
        for x in range(building.width):
            for z in range(building.length):
                block = _block_at(building, x, y, z)
                # Finish surrounding blocks before placing either door half.
                if block.startswith("oak_door["):
                    block = "air"
                ms.execute(
                    f"setblock {origin_x + x} {origin_y + y} {origin_z + z} minecraft:{block}"
                )
    for x in range(building.width):
        for z in range(building.length):
            if building.floorplan.get_cell(x, z) == Floorplan.DOOR:
                for y in (0, 1):
                    block = _block_at(building, x, y, z)
                    ms.execute(
                        f"setblock {origin_x + x} {origin_y + y} {origin_z + z} minecraft:{block}"
                    )


def pretty_print_building(building: Building) -> None:
    """Print physical layers bottom-to-top, with X rightward and Z downward."""
    symbols = {"air": ".", "stone": "S", "oak_wood": "W", "glass": "G", "oak_door": "D"}
    for y in range(-1, building.height):
        label = "Foundation" if y == -1 else f"Layer {y}"
        print(f"{label} (world Y={building.origin[1] + y})")
        for z in range(building.length):
            print(
                " ".join(
                    symbols[_block_at(building, x, y, z).split("[", 1)[0]]
                    for x in range(building.width)
                )
            )
        print()
    print("Legend: . = air, S = stone, W = wood, G = glass, D = door")


def pretty_print_floorplan(floorplan: Floorplan) -> None:
    """Print the logical layout, including room IDs, walls, and doors."""
    floorplan.pretty_print()
