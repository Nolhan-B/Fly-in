from dataclasses import dataclass, field
from pathfinding import dijkstra
from parser import DroneMap


@dataclass
class Drone:
    id: int
    current_zone: str
    path: list[str] = field(default_factory=list)


class Simulation:
    def __init__(self, drone_map: DroneMap) -> None:
        assert drone_map.start_zone is not None
        assert drone_map.end_zone is not None
        self.drones = [Drone(id=i, current_zone=drone_map.start_zone)
                       for i in range(drone_map.nb_drones)]
        for drone in self.drones:
            drone.path = dijkstra(drone_map, drone_map.start_zone, drone_map.end_zone)

    def get_drones_from_zone(self, zone_name: str) -> list[Drone]:
        return [drone for drone in self.drones
                if drone.current_zone == zone_name]