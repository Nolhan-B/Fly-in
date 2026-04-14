import heapq
from parser import DroneMap


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
                new_cost = cost + neighbor.movement_cost()
                heapq.heappush(heap, (new_cost, neighbor.name, path + [neighbor.name]))

    return []