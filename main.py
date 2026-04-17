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


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error caught! {e}")
    except KeyboardInterrupt:
        print("Bye bye!")
