"""Generate room seeds, then render them in Minecraft or locally."""

import argparse
import math

from helperFunc import initPlacement, growRooms, internWallPlacement
from models import Building
from rendering import render_minecraft, pretty_print_building, pretty_print_floorplan


def main(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("length", type=int)
    parser.add_argument("width", type=int)
    parser.add_argument("--height", type=int, default=4)
    parser.add_argument(
        "--debug", action="store_true", help="Print locally without Minecraft"
    )
    options = parser.parse_args(args)
    if options.length < 2 or options.width < 2 or options.height < 1:
        parser.error("Length and width must be at least 2; height must be positive")

    if options.debug:
        origin = (0, 0, 0)
    else:
        # Only world-position selection depends on Minecraft here.
        import minescript as ms

        target = ms.player_get_targeted_block(max_distance=50)
        if target is None:
            ms.echo("Look at a nearby ground block first.")
            return
        x, y, z = target.position if hasattr(target, "position") else target[0]
        origin = (x - options.width // 2, y + 2, z - options.length // 2)

    building = Building(origin, options.width, options.length, options.height)
    totalRooms = round((options.length * options.width) ** (1 / 3))
    initPlacement(building.floorplan, totalRooms)
    growRooms(building.floorplan, showGrowth=options.debug)

    internWallPlacement(building.floorplan)

    if options.debug:
        pretty_print_floorplan(building.floorplan)
        print()
        pretty_print_building(building)
    else:
        render_minecraft(building)


if __name__ == "__main__":
    main()
