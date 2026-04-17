from dataclasses import dataclass, field
from pathfinding import find_multiple_paths
from parser import DroneMap, Connection, ZoneType


@dataclass
class Drone:
    id: int
    current_zone: str
    path_index: int = 0
    turns_waiting: int = 0
    path: list[str] = field(default_factory=list)
    in_flight: bool = False
    target_zone: str | None = None


class Simulation:
    def __init__(self, drone_map: DroneMap) -> None:
        assert drone_map.start_zone is not None
        assert drone_map.end_zone is not None

        self.drones = [
            Drone(id=i + 1, current_zone=drone_map.start_zone)
            for i in range(drone_map.nb_drones)
        ]

        self.zones = drone_map.zones
        self.end_zone = drone_map.end_zone

        self.paths = find_multiple_paths(
            drone_map,
            drone_map.start_zone,
            drone_map.end_zone
        )

        if not self.paths:
            raise ValueError("No path found")

        for i, drone in enumerate(self.drones):
            drone.path = self.paths[i % len(self.paths)]

    def get_connection(
        self, zone_a: str, zone_b: str, drone_map: DroneMap
    ) -> Connection | None:
        for conn in drone_map.connections:
            if {conn.zone_a, conn.zone_b} == {zone_a, zone_b}:
                return conn
        return None

    def get_drones_from_zone(self, zone_name: str) -> list[Drone]:
        return [drone for drone in self.drones
                if drone.current_zone == zone_name]

    def count_drones_on_connection(
        self,
        zone_a: str,
        zone_b: str,
    ) -> int:
        target = {zone_a, zone_b}

        return sum(
            1
            for d in self.drones
            if {d.current_zone, d.target_zone} == target
            and d.in_flight
        )

    def can_drone_enter_zone(
        self, from_zone: str, zone_name: str,
        drone_map: DroneMap, turn_moves: list[str]
    ) -> bool:
        if zone_name == self.end_zone:
            return True

        if from_zone == zone_name:
            return False

        zone = self.zones[zone_name]

        future = len([d for d in self.drones if d.current_zone == zone_name])
        incoming = sum(1 for m in turn_moves if m.endswith(f"-{zone_name}"))

        if future + incoming >= zone.max_drones:
            return False

        conn = self.get_connection(from_zone, zone_name, drone_map)
        if conn:
            already_using = sum(
                                1 for m in turn_moves
                                if m.endswith(f"-{zone_name}")
                                )
            if already_using >= conn.max_link_capacity:
                return False

        return True

    def run(self, drone_map: DroneMap) -> None:
        assert drone_map.end_zone is not None

        while not all(
            d.current_zone == drone_map.end_zone
            for d in self.drones
        ):
            turn_moves = []

            self.drones.sort(key=lambda d: -d.path_index)

            for d in self.drones:
                current_zone_obj = self.zones.get(d.current_zone)

                if (
                    current_zone_obj
                    and current_zone_obj.zone_type == ZoneType.RESTRICTED
                ):
                    if d.turns_waiting == 0:
                        d.turns_waiting = 1
                        continue
                    else:
                        d.turns_waiting = 0

                if d.current_zone == self.end_zone:
                    continue

                if d.path_index + 1 >= len(d.path):
                    continue

                next_zone = d.path[d.path_index + 1]

                conn = self.get_connection(
                                           d.current_zone,
                                           next_zone,
                                           drone_map
                                           )

                if not d.in_flight and conn:
                    d.in_flight = True
                    d.target_zone = next_zone
                    turn_moves.append(f"D{d.id}-{conn.name}")
                    continue

                if d.in_flight:
                    assert d.target_zone is not None

                    d.in_flight = False
                    d.path_index += 1
                    d.current_zone = d.target_zone
                    turn_moves.append(f"D{d.id}-{d.current_zone}")
                    d.target_zone = None
                    continue
            if turn_moves:
                print(" ".join(turn_moves))
