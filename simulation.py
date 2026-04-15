from dataclasses import dataclass, field
from pathfinding import dijkstra
from parser import DroneMap, Zone, Connection, ZoneType


@dataclass
class Drone:
    id: int
    current_zone: str
    path_index: int = 0
    turns_waiting: int = 0
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

    def get_connection(self, zone_a: str, zone_b: str, drone_map: DroneMap) -> Connection | None:
        for conn in drone_map.connections:
            if {conn.zone_a, conn.zone_b} == {zone_a, zone_b}:
                return conn
        return None

    def get_zone_by_name(self, name:str) -> Zone:
        return self.zones[name]

    def get_drones_from_zone(self, zone_name: str) -> list[Drone]:
        return [drone for drone in self.drones
                if drone.current_zone == zone_name]

    def can_drone_enter_zone(self, from_zone: str, zone_name: str, drone_map: DroneMap, turn_moves: list[str]) -> bool:
        if zone_name == self.end_zone:
            return True
        zone = self.zones[zone_name]
        if len(self.get_drones_from_zone(zone_name)) >= zone.max_drones:
            return False
        conn = self.get_connection(from_zone, zone_name, drone_map)
        if conn:
            already_using = sum(1 for m in turn_moves if m.endswith(f"-{zone_name}"))
            if already_using >= conn.max_link_capacity:
                return False
        return True

    def run(self, drone_map: DroneMap) -> None:
        assert drone_map.end_zone is not None
        i = 1
        while not all(d.current_zone == drone_map.end_zone for d in self.drones):
            turn_moves = []
            for d in self.drones:
                current_zone_obj = self.zones.get(d.current_zone)
                if current_zone_obj and current_zone_obj.zone_type == ZoneType.RESTRICTED:
                    if d.turns_waiting == 0:
                        d.turns_waiting = 1
                        continue
                    else:
                        d.turns_waiting = 0
                if d.current_zone != self.end_zone:
                    if self.can_drone_enter_zone(d.current_zone, d.path[d.path_index + 1], drone_map, turn_moves):
                        d.path_index += 1
                        turn_moves.append(f"D{d.id}-{d.path[d.path_index]}")
                        d.current_zone = d.path[d.path_index]
            print(" ".join(turn_moves))