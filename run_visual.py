"""Pygame visualizer for the Fly-in drone simulation."""

import math
import pygame
from parser import DroneMap, Zone, ZoneType
from simulation import Simulation, Drone

# ── Display constants ──────────────────────────────────────────────────────────
CELL        = 110       # pixels per map unit
MARGIN      = 80        # border around the grid
FPS         = 2         # turns per second for auto-play
ZONE_R      = 32        # zone circle radius
DRONE_R     = 10        # drone dot radius
PANEL_H     = 70        # bottom panel height

# Colours
BG_COLOR      = ( 22,  22,  35)
PANEL_COLOR   = ( 38,  38,  55)
CONN_COLOR    = (100, 100, 130)
CONN_CAP_COL  = (200, 200, 100)   # capacity label on connections
DRONE_COLOR   = (220,  60,  60)
TEXT_DARK     = ( 15,  15,  15)
TEXT_LIGHT    = (220, 220, 220)
TEXT_DIM      = (120, 120, 140)
FINISH_COLOR  = ( 80, 220, 120)

TYPE_COLORS: dict[ZoneType, tuple[int,int,int]] = {
    ZoneType.NORMAL:     (190, 210, 255),
    ZoneType.RESTRICTED: (255, 185,  80),
    ZoneType.PRIORITY:   (140, 240, 160),
    ZoneType.BLOCKED:    ( 55,  55,  55),
}

TYPE_LABEL: dict[ZoneType, str] = {
    ZoneType.NORMAL:     "",
    ZoneType.RESTRICTED: "RES",
    ZoneType.PRIORITY:   "PRI",
    ZoneType.BLOCKED:    "BLK",
}

FONT_SIZE   = 12
FONT_SMALL  = 10


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_color(name: str | None) -> tuple[int,int,int] | None:
    if name is None:
        return None
    try:
        c = pygame.Color(name)
        return (c.r, c.g, c.b)
    except ValueError:
        return None


def _zone_fill(zone: Zone) -> tuple[int,int,int]:
    parsed = _parse_color(zone.color)
    if parsed:
        r, g, b = parsed
        return (min(r + 55, 255), min(g + 55, 255), min(b + 55, 255))
    return TYPE_COLORS.get(zone.zone_type, (200, 200, 200))


def _world_to_screen(x: int, y: int, min_x: int, min_y: int) -> tuple[int,int]:
    return (MARGIN + (x - min_x) * CELL,
            MARGIN + (y - min_y) * CELL)


def _midpoint(a: tuple[int,int], b: tuple[int,int]) -> tuple[int,int]:
    return ((a[0]+b[0])//2, (a[1]+b[1])//2)


def _draw_text_centered(surf: pygame.Surface, font: pygame.font.Font,
                         text: str, color: tuple, cx: int, cy: int) -> None:
    lbl = font.render(text, True, color)
    surf.blit(lbl, lbl.get_rect(center=(cx, cy)))


# ── Cost tracking ──────────────────────────────────────────────────────────────

def _compute_total_cost(sim: Simulation) -> int:
    """Sum of movement_cost() for every zone each drone passed through (excl. start)."""
    total = 0
    for d in sim.drones:
        for zone_name in d.path[1:]:          # skip start zone
            total += sim.zones[zone_name].movement_cost()
    return total


# ── Main visualizer ────────────────────────────────────────────────────────────

def run_visual(drone_map: DroneMap) -> None:
    pygame.init()
    pygame.font.init()

    font       = pygame.font.SysFont("monospace", FONT_SIZE)
    font_small = pygame.font.SysFont("monospace", FONT_SMALL)
    font_bold  = pygame.font.SysFont("monospace", FONT_SIZE + 2, bold=True)
    font_big   = pygame.font.SysFont("monospace", 22, bold=True)

    xs = [z.x for z in drone_map.zones.values()]
    ys = [z.y for z in drone_map.zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width  = 2 * MARGIN + (max_x - min_x) * CELL + CELL
    height = 2 * MARGIN + (max_y - min_y) * CELL + CELL + PANEL_H

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fly-in Drone Visualizer")
    clock = pygame.time.Clock()

    pos: dict[str, tuple[int,int]] = {
        name: _world_to_screen(z.x, z.y, min_x, min_y)
        for name, z in drone_map.zones.items()
    }

    sim      = Simulation(drone_map)
    turn     = 0
    finished = False
    total_cost = 0   # accumulated as drones move

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw_frame() -> None:
        screen.fill(BG_COLOR)

        # ── Connections ──
        for conn in drone_map.connections:
            if conn.zone_a not in pos or conn.zone_b not in pos:
                continue
            pa, pb = pos[conn.zone_a], pos[conn.zone_b]
            pygame.draw.line(screen, CONN_COLOR, pa, pb, 2)

            # capacity label at midpoint
            mx, my = _midpoint(pa, pb)
            cap_txt = f"×{conn.max_link_capacity}"
            lbl = font_small.render(cap_txt, True, CONN_CAP_COL)
            # small white bg so it's readable over lines
            bg = pygame.Surface((lbl.get_width()+4, lbl.get_height()+2), pygame.SRCALPHA)
            bg.fill((22, 22, 35, 200))
            screen.blit(bg, (mx - lbl.get_width()//2 - 2, my - lbl.get_height()//2 - 1))
            screen.blit(lbl, lbl.get_rect(center=(mx, my)))

        # ── Zones ──
        for name, zone in drone_map.zones.items():
            cx, cy = pos[name]
            fill = _zone_fill(zone)
            pygame.draw.circle(screen, fill, (cx, cy), ZONE_R)

            # border
            if zone.is_start:
                border_c, border_w = (60, 220, 80), 4
            elif zone.is_end:
                border_c, border_w = (220, 60, 60), 4
            else:
                border_c, border_w = (80, 80, 110), 2
            pygame.draw.circle(screen, border_c, (cx, cy), ZONE_R, border_w)

            # zone name (line 1)
            _draw_text_centered(screen, font, name[:10], TEXT_DARK, cx, cy - 8)

            # zone type badge (line 2) — only for non-normal
            type_lbl = TYPE_LABEL.get(zone.zone_type, "")
            if type_lbl:
                _draw_text_centered(screen, font_small, type_lbl, (80, 40, 10), cx, cy + 5)
                # max_drones (line 3)
                _draw_text_centered(screen, font_small, f"d:{zone.max_drones}", TEXT_DARK, cx, cy + 16)
            else:
                # max_drones (line 2)
                _draw_text_centered(screen, font_small, f"d:{zone.max_drones}", TEXT_DARK, cx, cy + 8)

        # ── Drones ──
        zone_groups: dict[str, list[Drone]] = {}
        for d in sim.drones:
            zone_groups.setdefault(d.current_zone, []).append(d)

        for zone_name, drones in zone_groups.items():
            cx, cy = pos[zone_name]
            n = len(drones)
            for i, d in enumerate(drones):
                angle  = (2*math.pi*i / max(n,1)) - math.pi/2
                radius = 0 if n == 1 else ZONE_R + DRONE_R + 2
                dx = int(radius * math.cos(angle))
                dy = int(radius * math.sin(angle))
                pygame.draw.circle(screen, DRONE_COLOR, (cx+dx, cy+dy), DRONE_R)
                _draw_text_centered(screen, font_small, str(d.id),
                                    (255,255,255), cx+dx, cy+dy)

        # ── Bottom panel ──
        panel_y = height - PANEL_H
        pygame.draw.rect(screen, PANEL_COLOR, (0, panel_y, width, PANEL_H))
        pygame.draw.line(screen, (70,70,100), (0, panel_y), (width, panel_y), 1)

        done = sum(1 for d in sim.drones if d.current_zone == sim.end_zone)

        if finished:
            msg = f"✓ FINISHED   Turns: {turn}   Total cost: {total_cost}   Drones: {done}/{drone_map.nb_drones}"
            surf = font_big.render(msg, True, FINISH_COLOR)
            screen.blit(surf, surf.get_rect(center=(width//2, panel_y + PANEL_H//2)))
        else:
            left_txt  = f"Turn {turn}   Cost so far: {total_cost}   Arrived: {done}/{drone_map.nb_drones}"
            right_txt = "SPACE=step   A=auto   Q=quit"
            screen.blit(font_bold.render(left_txt,  True, (230,230,100)),
                        (14, panel_y + 12))
            screen.blit(font.render(right_txt, True, TEXT_DIM),
                        (14, panel_y + 34))

            # legend strip (top-right corner of panel)
            legend_items = [
                ("RES = restricted (+1 wait)", (255,185,80)),
                ("PRI = priority",              (140,240,160)),
                ("d:N = max drones  ×N = link cap", CONN_CAP_COL),
            ]
            lx = width - 10
            for i, (txt, col) in enumerate(legend_items):
                s = font_small.render(txt, True, col)
                screen.blit(s, s.get_rect(right=lx, top=panel_y + 6 + i*18))

        pygame.display.flip()

    # ── step ──────────────────────────────────────────────────────────────────
    def step() -> None:
        nonlocal turn, finished, total_cost
        if finished:
            return

        turn_moves: list[str] = []
        for d in sim.drones:
            zone_obj = sim.zones.get(d.current_zone)
            if zone_obj and zone_obj.zone_type == ZoneType.RESTRICTED:
                if d.turns_waiting == 0:
                    d.turns_waiting = 1
                    continue
                else:
                    d.turns_waiting = 0

            if d.current_zone != sim.end_zone:
                next_zone = d.path[d.path_index + 1]
                if sim.can_drone_enter_zone(d.current_zone, next_zone, drone_map, turn_moves):
                    d.path_index += 1
                    d.current_zone = d.path[d.path_index]
                    turn_moves.append(f"D{d.id}-{d.current_zone}")
                    # accumulate cost of entering the new zone
                    total_cost += sim.zones[d.current_zone].movement_cost()

        turn += 1
        print(" ".join(turn_moves))
        if all(d.current_zone == drone_map.end_zone for d in sim.drones):
            finished = True

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
                    while not finished:
                        step()
                        draw_frame()
                        clock.tick(FPS)

        clock.tick(60)