"""Parser module for the Fly-in drone routing system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import sys


class ZoneType(Enum):
    """Possible types for a zone."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @staticmethod
    def from_str(value: str) -> "ZoneType":
        """Return a ZoneType from its string representation."""
        try:
            return ZoneType(value)
        except ValueError:
            raise ValueError(f"Invalid zone type: '{value}'")


@dataclass
class Zone:
    """A zone node in the drone routing graph."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False

    def movement_cost(self) -> int:
        """Return the turn cost to enter this zone."""
        return 2 if self.zone_type == ZoneType.RESTRICTED else 1


@dataclass
class Connection:
    """A bidirectional edge between two zones."""

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    def involves(self, name: str) -> bool:
        """Return True if this connection touches the given zone name."""
        return self.zone_a == name or self.zone_b == name

    def other(self, name: str) -> str:
        """Return the other zone name in this connection."""
        return self.zone_b if self.zone_a == name else self.zone_a


@dataclass
class DroneMap:
    """Complete parsed map: drones, zones and connections."""

    nb_drones: int
    zones: dict[str, Zone] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    start_zone: Optional[str] = None
    end_zone: Optional[str] = None

    def get_neighbors(self, zone_name: str) -> list[Zone]:
        """Return all non-blocked zones reachable from zone_name."""
        neighbors: list[Zone] = []
        for conn in self.connections:
            if conn.involves(zone_name):
                other = self.zones[conn.other(zone_name)]
                if other.zone_type != ZoneType.BLOCKED:
                    neighbors.append(other)
        return neighbors

_KNOWN_ZONE_KEYS = {"zone", "color", "max_drones"}
_KNOWN_CONN_KEYS = {"max_link_capacity"}
_ALL_KNOWN_KEYS = _KNOWN_ZONE_KEYS | _KNOWN_CONN_KEYS


def _parse_metadata(block: str) -> dict[str, str]:
    """Parse a metadata string like 'zone=normal color=red max_drones=2'."""
    meta: dict[str, str] = {}
    for token in block.split():
        if "=" not in token:
            raise ValueError(f"Invalid metadata token: '{token}'")
        key, _, value = token.partition("=")
        if not key or not value:
            raise ValueError(f"Malformed metadata pair: '{token}'")
        if key not in _ALL_KNOWN_KEYS:
            raise ValueError(f"Unknown metadata key: '{key}'")
        if "=" in value:
            raise ValueError(
                f"Metadata value for '{key}' looks malformed: '{value}'. "
                f"Missing space between metadata entries?"
            )
        meta[key] = value
    return meta


def _extract_metadata(lineno: int, line: str) -> tuple[str, dict[str, str]]:
    """Split a line into (body, metadata_dict).

    Metadata is the optional trailing [...] block.
    """
    if "[" not in line:
        return line, {}

    open_idx = line.index("[")
    if not line.endswith("]"):
        raise ValueError(f"Line {lineno}: metadata block is not properly closed.")

    body = line[:open_idx].strip()
    block_content = line[open_idx + 1:-1].strip()

    try:
        meta = _parse_metadata(block_content)
    except ValueError as exc:
        raise ValueError(f"Line {lineno}: {exc}") from exc

    return body, meta

def _parse_positive_int(lineno: int, value: str, field_name: str) -> int:
    """Parse a string as a positive integer or raise a clear ValueError."""
    if not value.lstrip("-").isdigit():
        raise ValueError(
            f"Line {lineno}: '{field_name}' must be an integer, got '{value}'."
        )
    result = int(value)
    if result <= 0:
        raise ValueError(
            f"Line {lineno}: '{field_name}' must be a positive integer."
        )
    return result


def _parse_int_coord(lineno: int, value: str, axis: str) -> int:
    """Parse a coordinate string (may be negative) or raise a clear ValueError."""
    stripped = value.lstrip("-")
    if not stripped.isdigit():
        raise ValueError(
            f"Line {lineno}: coordinate '{axis}' must be an integer, got '{value}'."
        )
    return int(value)

def _parse_nb_drones(lineno: int, line: str) -> int:
    """Parse the 'nb_drones: N' line and return N."""
    if not line.startswith("nb_drones:"):
        raise ValueError(
            f"Line {lineno}: first line must be 'nb_drones: <positive_integer>'."
        )
    parts = line.split(":", 1)
    value = parts[1].strip()
    return _parse_positive_int(lineno, value, "nb_drones")


def _parse_zone_line(lineno: int, line: str) -> Zone:
    """Parse a hub/start_hub/end_hub line and return a Zone."""
    body, meta = _extract_metadata(lineno, line)
    tokens = body.split()

    # Expected: ["start_hub:", "name", "x", "y"]
    if len(tokens) != 4:
        raise ValueError(
            f"Line {lineno}: zone definition expects "
            f"'<type>: <name> <x> <y> [meta]', got {len(tokens)} tokens."
        )

    prefix = tokens[0].rstrip(":")
    name = tokens[1]
    x = _parse_int_coord(lineno, tokens[2], "x")
    y = _parse_int_coord(lineno, tokens[3], "y")

    raw_type = meta.get("zone", "normal")
    try:
        zone_type = ZoneType.from_str(raw_type)
    except ValueError:
        raise ValueError(
            f"Line {lineno}: '{raw_type}' is not a valid zone type."
        )

    max_drones = _parse_positive_int(
        lineno, meta.get("max_drones", "1"), "max_drones"
    )

    return Zone(
        name=name,
        x=x,
        y=y,
        zone_type=zone_type,
        color=meta.get("color"),
        max_drones=max_drones,
        is_start=(prefix == "start_hub"),
        is_end=(prefix == "end_hub"),
    )


def _parse_connection_line(
    lineno: int, line: str, known_zones: dict[str, Zone]
) -> Connection:
    """Parse a 'connection: A-B [meta]' line and return a Connection."""
    body, meta = _extract_metadata(lineno, line)
    tokens = body.split()

    # Expected: ["connection:", "A-B"]
    if len(tokens) != 2:
        raise ValueError(
            f"Line {lineno}: connection expects 'connection: <zone1>-<zone2> [meta]'."
        )

    pair = tokens[1]
    parts = pair.split("-")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Line {lineno}: connection '{pair}' must be exactly 'zone1-zone2' "
            f"(zone names cannot contain dashes)."
        )

    zone_a, zone_b = parts[0], parts[1]

    for name in (zone_a, zone_b):
        if name not in known_zones:
            raise ValueError(
                f"Line {lineno}: connection references unknown zone '{name}'."
            )

    max_link_capacity = _parse_positive_int(
        lineno, meta.get("max_link_capacity", "1"), "max_link_capacity"
    )

    return Connection(
        zone_a=zone_a,
        zone_b=zone_b,
        max_link_capacity=max_link_capacity,
    )

class MapParser:
    """Read a .fly map file and produce a DroneMap instance."""

    _ZONE_PREFIXES = ("start_hub:", "end_hub:", "hub:")

    def __init__(self, filepath: str) -> None:
        """Store the path of the map file to parse."""
        self._filepath = filepath

    def parse(self) -> DroneMap:
        """Parse the file and return a DroneMap. Raise ValueError on any error."""
        try:
            lines = self._read_lines()
            if not lines:
                raise ValueError("File is empty or contains only comments.")
            return self._build_map(lines)
        except (ValueError, FileNotFoundError) as e:
            print("Parsing error:", e)
            sys.exit(0)

    def _read_lines(self) -> list[tuple[int, str]]:
        """Read file lines, strip comments and blank lines, keep line numbers."""
        result: list[tuple[int, str]] = []
        with open(self._filepath, encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.split("#", 1)[0].strip()
                if line:
                    result.append((lineno, line))
        return result

    def _build_map(self, lines: list[tuple[int, str]]) -> DroneMap:
        """Walk the cleaned lines and build the DroneMap step by step."""
        lineno, first = lines[0]
        nb_drones = _parse_nb_drones(lineno, first)
        drone_map = DroneMap(nb_drones=nb_drones)

        seen_connections: set[frozenset[str]] = set()

        for lineno, line in lines[1:]:
            if line.startswith("nb_drones:"):
                raise ValueError(
                    f"Line {lineno}: 'nb_drones' must appear only on the first line."
                )
            elif any(line.startswith(p) for p in self._ZONE_PREFIXES):
                zone = _parse_zone_line(lineno, line)
                self._register_zone(drone_map, zone, lineno)
            elif line.startswith("connection:"):
                conn = _parse_connection_line(lineno, line, drone_map.zones)
                key: frozenset[str] = frozenset({conn.zone_a, conn.zone_b})
                if key in seen_connections:
                    raise ValueError(
                        f"Line {lineno}: duplicate connection "
                        f"'{conn.zone_a}-{conn.zone_b}'."
                    )
                seen_connections.add(key)
                drone_map.connections.append(conn)
            else:
                raise ValueError(
                    f"Line {lineno}: unrecognized syntax: '{line}'"
                )

        self._validate(drone_map)
        return drone_map

    def _register_zone(
        self, drone_map: DroneMap, zone: Zone, lineno: int
    ) -> None:
        """Add zone to the map, enforcing uniqueness and single start/end."""
        if zone.name in drone_map.zones:
            raise ValueError(
                f"Line {lineno}: duplicate zone name '{zone.name}'."
            )
        if zone.is_start:
            if drone_map.start_zone is not None:
                raise ValueError(f"Line {lineno}: only one start_hub is allowed.")
            drone_map.start_zone = zone.name
        if zone.is_end:
            if drone_map.end_zone is not None:
                raise ValueError(f"Line {lineno}: only one end_hub is allowed.")
            drone_map.end_zone = zone.name
        drone_map.zones[zone.name] = zone

    @staticmethod
    def _validate(drone_map: DroneMap) -> None:
        """Final checks once the full file has been parsed."""
        if drone_map.start_zone is None:
            raise ValueError("Map is missing a 'start_hub' definition.")
        if drone_map.end_zone is None:
            raise ValueError("Map is missing an 'end_hub' definition.")