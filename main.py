from parser import MapParser
import sys

map_path = "maps/easy/03_basic_capacity.txt"
try:
    drone_map = MapParser(map_path).parse()
except Exception as e:
    print(f'Error happened while parsing: {e}')
    sys.exit()

print(drone_map)
