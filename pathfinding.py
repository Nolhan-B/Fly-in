import heapq
from parser import DroneMap, ZoneType


def dijkstra(drone_map: DroneMap, start: str, end: str) -> list[str]:
    heap = [(0, start, [start])]
    visited = set()

    while heap:
        cost, current, path = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            return path

        for neighbor in drone_map.get_neighbors(current):
            if neighbor.name not in visited:
                bonus = -0.3 if neighbor.zone_type == ZoneType.PRIORITY else 0
                new_cost = cost + neighbor.movement_cost() + bonus
                heapq.heappush(
                    (heap, (new_cost, neighbor.name, path + [neighbor.name]))
                )

    return []


def find_multiple_paths(
    drone_map: DroneMap, start: str, end: str, max_paths: int = 3
) -> list[list[str]]:
    paths: list[list[str]] = []
    used_edges: set[tuple[str, str]] = set()

    for _ in range(max_paths):
        path = dijkstra_with_avoid(drone_map, start, end, used_edges)
        if not path:
            break

        paths.append(path)

        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            used_edges.add((a, b))
            used_edges.add((b, a))

    return paths


def dijkstra_with_avoid(
    drone_map: DroneMap, start: str,
    end: str, avoid_edges: set[tuple[str, str]]
) -> list[str]:
    import heapq

    heap = [(0, start, [start])]
    visited = set()

    while heap:
        cost, current, path = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            return path

        for neighbor in drone_map.get_neighbors(current):
            edge = (current, neighbor.name)

            extra_cost = 0
            if edge in avoid_edges:
                extra_cost = 5

            new_cost = cost + neighbor.movement_cost() + extra_cost
            heapq.heappush(
                           heap,
                           (new_cost, neighbor.name, path + [neighbor.name])
                           )

    return []
