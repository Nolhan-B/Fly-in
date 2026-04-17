from __future__ import annotations

import math
import pygame
from parser import DroneMap, Zone, ZoneType
from simulation import Simulation, Drone

MARGIN = 100
FPS = 3
ZONE_R = 40
DRONE_R = 13
PANEL_H = 90

BG_COLOR = (15, 15, 25)
PANEL_COLOR = (28, 28, 45)
CONN_COLOR = (80, 80, 120)
CONN_CAP_COL = (180, 180, 80)
DRONE_COLOR = (220, 60, 60)
TEXT_DARK = (10, 10, 10)
TEXT_LIGHT = (220, 220, 220)
TEXT_DIM = (110, 110, 130)
FINISH_COLOR = (80, 220, 120)

TYPE_COLORS: dict[ZoneType, tuple[int, int, int]] = {
    ZoneType.NORMAL:     (190, 210, 255),
    ZoneType.RESTRICTED: (255, 185,  80),
    ZoneType.PRIORITY:   (140, 240, 160),
    ZoneType.BLOCKED:    (55,  55,  55),
}

TYPE_LABEL: dict[ZoneType, str] = {
    ZoneType.NORMAL:     "",
    ZoneType.RESTRICTED: "RES",
    ZoneType.PRIORITY:   "PRI",
    ZoneType.BLOCKED:    "BLK",
}


def _parse_color(name: str | None) -> tuple[int, int, int] | None:
    """Try to parse a color name via pygame, return None on failure."""
    if name is None:
        return None
    try:
        c = pygame.Color(name)
        return (c.r, c.g, c.b)
    except ValueError:
        return None


def _zone_fill(zone: Zone) -> tuple[int, int, int]:
    """Return the fill colour for a zone circle."""
    parsed = _parse_color(zone.color)
    if parsed:
        r, g, b = parsed
        return (min(r + 40, 255), min(g + 40, 255), min(b + 40, 255))
    return TYPE_COLORS.get(zone.zone_type, (200, 200, 200))


def _world_to_screen(
    x: int, y: int, min_x: int, min_y: int, cell: int
) -> tuple[int, int]:
    """Convert map coordinates to screen pixels."""
    return (MARGIN + (x - min_x) * cell, MARGIN + (y - min_y) * cell)


def _midpoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    """Return the midpoint between two screen positions."""
    return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)


def _draw_centered(
    surf: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    cx: int,
    cy: int,
) -> None:
    """Render text centered at (cx, cy)."""
    lbl = font.render(text, True, color)
    surf.blit(lbl, lbl.get_rect(center=(cx, cy)))


def run_visual(drone_map: DroneMap) -> None:
    """Open a pygame window and step through the simulation visually."""
    pygame.init()
    pygame.font.init()

    font = pygame.font.SysFont("monospace", 14)
    font_small = pygame.font.SysFont("monospace", 11)
    font_bold = pygame.font.SysFont("monospace", 15, bold=True)
    font_big = pygame.font.SysFont("monospace", 26, bold=True)

    xs = [z.x for z in drone_map.zones.values()]
    ys = [z.y for z in drone_map.zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    max_w, max_h = 1400, 900 - PANEL_H
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)
    cell = min(
        (max_w - 2 * MARGIN),
        (max_h - 2 * MARGIN),
        200,
    )
    cell = max(cell, 80)

    width = 2 * MARGIN + span_x * cell + ZONE_R * 2
    height = 2 * MARGIN + span_y * cell + ZONE_R * 2 + PANEL_H

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fly-in — Drone Visualizer")
    clock = pygame.time.Clock()

    pos: dict[str, tuple[int, int]] = {
        name: _world_to_screen(z.x, z.y, min_x, min_y, cell)
        for name, z in drone_map.zones.items()
    }

    sim = Simulation(drone_map)
    turn = 0
    finished = False
    auto_play = False

    def draw_frame() -> None:
        """Render the current simulation state to screen."""
        screen.fill(BG_COLOR)

        # connections
        for conn in drone_map.connections:
            if conn.zone_a not in pos or conn.zone_b not in pos:
                continue
            pa, pb = pos[conn.zone_a], pos[conn.zone_b]
            pygame.draw.line(screen, CONN_COLOR, pa, pb, 2)
            if conn.max_link_capacity > 1:
                mx, my = _midpoint(pa, pb)
                _draw_centered(
                               screen,
                               font_small,
                               f"×{conn.max_link_capacity}",
                               CONN_CAP_COL, mx, my
                               )

        for name, zone in drone_map.zones.items():
            cx, cy = pos[name]
            fill = _zone_fill(zone)
            pygame.draw.circle(screen, fill, (cx, cy), ZONE_R)

            if zone.is_start:
                border_c, border_w = (60, 220, 80), 4
            elif zone.is_end:
                border_c, border_w = (220, 60, 60), 4
            else:
                border_c, border_w = (80, 80, 110), 2
            pygame.draw.circle(screen, border_c, (cx, cy), ZONE_R, border_w)

            # name
            _draw_centered(screen, font, name[:10], TEXT_DARK, cx, cy - 10)

            # type badge
            type_lbl = TYPE_LABEL.get(zone.zone_type, "")
            if type_lbl:
                _draw_centered(
                               screen,
                               font_small,
                               type_lbl,
                               (80, 40, 10),
                               cx, cy + 4
                               )
                _draw_centered(
                                screen,
                                font_small,
                                f"d:{zone.max_drones}",
                                TEXT_DARK, cx, cy + 16
                               )
            else:
                _draw_centered(
                               screen,
                               font_small,
                               f"d:{zone.max_drones}", TEXT_DARK, cx, cy + 8
                               )

        # drones
        zone_groups: dict[str, list[Drone]] = {}
        for d in sim.drones:
            zone_groups.setdefault(d.current_zone, []).append(d)

        for zone_name, drones in zone_groups.items():
            cx, cy = pos[zone_name]
            n = len(drones)
            for i, d in enumerate(drones):
                angle = (2 * math.pi * i / max(n, 1)) - math.pi / 2
                radius = 0 if n == 1 else ZONE_R + DRONE_R + 4
                dx = int(radius * math.cos(angle))
                dy = int(radius * math.sin(angle))
                pygame.draw.circle(screen, DRONE_COLOR,
                                   (cx + dx, cy + dy), DRONE_R)
                _draw_centered(screen, font_small, str(d.id),
                               (255, 255, 255), cx + dx, cy + dy)

        panel_y = height - PANEL_H
        pygame.draw.rect(screen, PANEL_COLOR, (0, panel_y, width, PANEL_H))
        pygame.draw.line(
                         screen,
                         (70, 70, 100),
                         (0, panel_y),
                         (width, panel_y),
                         1)

        done = sum(1 for d in sim.drones if d.current_zone == sim.end_zone)

        if finished:
            msg = (f"DONE   Turns: {turn}"

                   f"   Drones: {done}/{drone_map.nb_drones}")
            surf = font_big.render(msg, True, FINISH_COLOR)
            screen.blit(
                        surf,
                        surf.get_rect(
                            center=(width // 2, panel_y + PANEL_H // 2)
                            )
                        )
        else:
            line1 = (f"Turn: {turn}   "
                     f"Arrived: {done}/{drone_map.nb_drones}")
            line2 = "SPACE = next turn   A = auto-play   Q = quit"
            screen.blit(font_bold.render(line1, True, (230, 230, 100)),
                        (14, panel_y + 10))
            screen.blit(font.render(line2, True, TEXT_DIM),
                        (14, panel_y + 36))

        pygame.display.flip()

    def step() -> None:
        """Advance the simulation by one turn."""
        nonlocal turn, finished
        if finished:
            return

        turn_moves: list[str] = []

        for d in sim.drones:
            if d.current_zone == sim.end_zone:
                continue

            current_zone_obj = sim.zones.get(d.current_zone)
            if (
                current_zone_obj
                and current_zone_obj.zone_type == ZoneType.RESTRICTED
            ):
                if d.turns_waiting == 0:
                    d.turns_waiting = 1
                    continue
                else:
                    d.turns_waiting = 0

            if d.path_index + 1 >= len(d.path):
                continue
            next_zone = d.path[d.path_index + 1]

            if sim.can_drone_enter_zone(d.current_zone, next_zone,
                                        drone_map, turn_moves):
                d.path_index += 1
                d.current_zone = d.path[d.path_index]
                turn_moves.append(f"D{d.id}-{d.current_zone}")

        turn += 1
        # print(" ".join(turn_moves))

        if all(d.current_zone == drone_map.end_zone for d in sim.drones):
            finished = True
            print(f"\n=== FINISHED in {turn} turns ===")

    draw_frame()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if event.key == pygame.K_SPACE:
                    step()
                    draw_frame()
                if event.key == pygame.K_a:
                    auto_play = not auto_play

        if auto_play and not finished:
            step()
            draw_frame()
            clock.tick(FPS)

        clock.tick(60)
