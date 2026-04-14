from dataclasses import dataclass, field
from pathfinding import dijkstra
from parser import DroneMap, Zone


@dataclass
class Drone:
    id: int
    current_zone: str
    path_index: int = 0
    path: list[str] = field(default_factory=list)


class Simulation:
    def __init__(self, drone_map: DroneMap) -> None:
        assert drone_map.start_zone is not None
        assert drone_map.end_zone is not None
        self.drones = [Drone(id=i, current_zone=drone_map.start_zone)
                    for i in range(drone_map.nb_drones)]
        self.zones = drone_map.zones
        self.end_zone = drone_map.end_zone
        for drone in self.drones:
            drone.path = dijkstra(drone_map, drone_map.start_zone, drone_map.end_zone)

    def get_zone_by_name(self, name:str) -> Zone:
        return self.zones[name]

    def get_drones_from_zone(self, zone_name: str) -> list[Drone]:
        return [drone for drone in self.drones
                if drone.current_zone == zone_name]

    def can_drone_enter_zone(self, zone_name: str) -> bool:
        if zone_name == self.end_zone:
            return True
        zone = self.zones[zone_name]

        return len(self.get_drones_from_zone(zone_name)) < zone.max_drones

    def run(self, drone_map: DroneMap) -> None:
        assert drone_map.end_zone is not None
        i = 1
        while not all(d.current_zone == drone_map.end_zone for d in self.drones):
            turn_moves = []
            for d in self.drones:
                if d.current_zone != self.end_zone:
                    if self.can_drone_enter_zone(d.path[d.path_index + 1]):
                        d.path_index += 1
                        turn_moves.append(f"D{d.id}-{d.path[d.path_index]}")
                        d.current_zone = d.path[d.path_index]
            print(" ".join(turn_moves))