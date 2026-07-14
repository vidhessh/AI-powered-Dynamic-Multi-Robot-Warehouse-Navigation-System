#!/usr/bin/env python3
"""
generate_map.py
Generates a static occupancy-grid map (warehouse_map.pgm + .yaml) directly
from the known geometry in worlds_warehouse.sdf. No SLAM required — this is
a geometry-derived ground-truth map. (Comparing this against a SLAM-built
map is listed as future work in the roadmap.)

Run from anywhere; writes into ../maps/ relative to this file's location,
i.e. warehouse_bot/maps/.
"""

import os
import numpy as np
from PIL import Image
import yaml

# ---- World / map parameters — MUST match worlds_warehouse.sdf ----
RESOLUTION = 0.05                       # meters/pixel
WORLD_X_MIN, WORLD_X_MAX = -12.0, 12.0  # matches wall_east / wall_west
WORLD_Y_MIN, WORLD_Y_MAX = -8.0, 8.0    # matches wall_north / wall_south
WALL_THICKNESS = 0.2

WIDTH_PX = int((WORLD_X_MAX - WORLD_X_MIN) / RESOLUTION)   # 480
HEIGHT_PX = int((WORLD_Y_MAX - WORLD_Y_MIN) / RESOLUTION)  # 320

FREE = 254
OCCUPIED = 0


def world_to_px(x, y):
    col = int((x - WORLD_X_MIN) / RESOLUTION)
    row = int((WORLD_Y_MAX - y) / RESOLUTION)  # row 0 = top = max Y
    return col, row


def draw_rect(grid, cx, cy, sx, sy):
    """Axis-aligned rect centered at (cx, cy), size (sx, sy) in meters."""
    x0, x1 = cx - sx / 2, cx + sx / 2
    y0, y1 = cy - sy / 2, cy + sy / 2
    c0, r0 = world_to_px(x0, y1)
    c1, r1 = world_to_px(x1, y0)
    c0, c1 = sorted((max(c0, 0), min(c1, WIDTH_PX - 1)))
    r0, r1 = sorted((max(r0, 0), min(r1, HEIGHT_PX - 1)))
    grid[r0:r1 + 1, c0:c1 + 1] = OCCUPIED


def draw_circle(grid, cx, cy, radius):
    col_c, row_c = world_to_px(cx, cy)
    r_px = int(radius / RESOLUTION) + 1
    for row in range(max(0, row_c - r_px), min(HEIGHT_PX, row_c + r_px + 1)):
        for col in range(max(0, col_c - r_px), min(WIDTH_PX, col_c + r_px + 1)):
            if (col - col_c) ** 2 + (row - row_c) ** 2 <= r_px ** 2:
                grid[row, col] = OCCUPIED


def main():
    grid = np.full((HEIGHT_PX, WIDTH_PX), FREE, dtype=np.uint8)

    # Walls
    draw_rect(grid, 0, 8, 24, WALL_THICKNESS)    # wall_north
    draw_rect(grid, 0, -8, 24, WALL_THICKNESS)   # wall_south
    draw_rect(grid, 12, 0, WALL_THICKNESS, 16)   # wall_east
    draw_rect(grid, -12, 0, WALL_THICKNESS, 16)  # wall_west

    # Package shelf (robot spawns in front of this, near x=-9)
    draw_rect(grid, -9, 0, 1.0, 4.0)

    # Extra shelf racks added for the multi-bot warehouse layout
    draw_rect(grid, -9, 6.5, 1.0, 3.0)   # shelf_rack_2
    draw_rect(grid, -9, -6.5, 1.0, 3.0)  # shelf_rack_3
    draw_rect(grid, 3, 6.5, 3.0, 1.0)    # shelf_rack_4 (rotated 90deg -> swapped sx/sy)

    # Static warehouse dressing
    draw_circle(grid, 10.5, 6.5, 0.3)    # barrel_1
    draw_circle(grid, 10.5, -6.5, 0.3)   # barrel_2
    # Note: pallet_1 at y=8.6 is outside the mapped area (WORLD_Y_MAX=8.0)
    # and dynamic_obstacle_1/2/3 are intentionally NOT drawn here — they move,
    # so they belong in the live obstacle_layer (from /scan), not the static map.

    # Cone obstacle field
    cones = [(-5, 3), (-4, -2), (-3, 1), (-2, -3), (-1, 2), (0, -1), (1, 3), (2, -2)]
    for cx, cy in cones:
        draw_circle(grid, cx, cy, 0.15)

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "maps"))
    os.makedirs(out_dir, exist_ok=True)

    pgm_path = os.path.join(out_dir, "warehouse_map.pgm")
    yaml_path = os.path.join(out_dir, "warehouse_map.yaml")
    preview_path = os.path.join(out_dir, "warehouse_map_preview.png")

    img = Image.fromarray(grid, mode="L")
    img.save(pgm_path)
    img.save(preview_path)

    map_yaml = {
        "image": "warehouse_map.pgm",
        "resolution": RESOLUTION,
        "origin": [WORLD_X_MIN, WORLD_Y_MIN, 0.0],
        "negate": 0,
        "occupied_thresh": 0.65,
        "free_thresh": 0.196,
    }
    with open(yaml_path, "w") as f:
        yaml.dump(map_yaml, f, default_flow_style=False)

    print(f"Map written:    {pgm_path}")
    print(f"Map yaml:       {yaml_path}")
    print(f"Preview (png):  {preview_path}")


if __name__ == "__main__":
    main()
