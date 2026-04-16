"""Entry point for the Fly-in drone routing system."""

import sys
from parser import MapParser
from run_visual import run_visual
from simulation import Simulation


def main() -> None:
    """Parse map file and run the simulation."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    try:
        drone_map = MapParser(sys.argv[1]).parse()
        simulation = Simulation(drone_map)
        simulation.run(drone_map)
        run_visual(drone_map)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # print(simulation.drones)
    # print(simulation.zones)
    # print(simulation.can_drone_go_on_zone(simulation.drones[0], simulation.zones[1]))
    # print(simulation.drones)
#
if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as e:
        print(f"Error caught! {e}")