#!/usr/bin/env python3
"""
Maze with Keys and Doors - shortest path via BFS over (row, col, key_mask).

Input  (stdin, first line): T  -> number of key/door types (1..6)
Option 1: python maze_keys.py --csv maze.csv  --out solved.csv   (T line on stdin)
Option 2: python maze_keys.py --n 12 --seed 7 --out solved.csv   (random maze)

Output 1: shortest path length (or -1) printed to stdout.
Output 2: CSV where path cells that were plain '.' become 'x'.
          S, E, keys (a-d,f,g) and doors (A-D,F,G) on the path keep their letters, so
          they stay identifiable. Use --save-maze to also write the maze itself.
"""
import argparse
import csv
import random
import sys
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


# 'E' is the exit, so it cannot also be the door of key 'e'. The sixth type
# therefore uses 'g'/'G' (types: a b c d f g  ->  doors A B C D F G).
KEYS = 'abcdfg'


def is_key(ch):
    return ch in KEYS


def is_door(ch):
    return ch.lower() in KEYS and ch.isupper()


def bit(ch):
    return KEYS.index(ch.lower())


def solve(grid):
    """Return (length, path) where path is a list of (r, c); (-1, None) if unsolvable."""
    n = len(grid)
    start = end = None
    for r in range(n):
        for c in range(n):
            if grid[r][c] == 'S':
                start = (r, c)
            elif grid[r][c] == 'E':
                end = (r, c)
    if start is None or end is None:
        raise ValueError("grid needs exactly one S and one E")

    s0 = (start[0], start[1], 0)
    parent = {s0: None}
    q = deque([s0])
    while q:
        cur = q.popleft()
        r, c, mask = cur
        if (r, c) == end:
            path = []
            while cur is not None:
                path.append((cur[0], cur[1]))
                cur = parent[cur]
            path.reverse()
            return len(path) - 1, path
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n):
                continue
            ch = grid[nr][nc]
            if ch == '#':
                continue
            nmask = mask
            if is_door(ch):
                if not (mask >> bit(ch)) & 1:
                    continue
            elif is_key(ch):
                nmask |= 1 << bit(ch)
            nxt = (nr, nc, nmask)
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)
    return -1, None


def generate(n, t, rng, wall_density=0.25, max_tries=2000):
    """Random n x n maze with t keys + t doors that is guaranteed solvable.
    Prefers mazes whose shortest path actually passes through a door."""
    if n < 4 or n * n < 2 + 2 * t + 4:
        raise ValueError("grid too small for that many keys/doors")
    fallback = None
    for _ in range(max_tries):
        grid = [['#' if rng.random() < wall_density else '.' for _ in range(n)]
                for _ in range(n)]
        cells = [(r, c) for r in range(n) for c in range(n)]
        picks = rng.sample(cells, 2 + 2 * t)
        sr, sc = picks[0]
        er, ec = picks[1]
        grid[sr][sc] = 'S'
        grid[er][ec] = 'E'
        for i in range(t):
            kr, kc = picks[2 + 2 * i]
            dr, dc = picks[3 + 2 * i]
            grid[kr][kc] = KEYS[i]
            grid[dr][dc] = KEYS[i].upper()
        length, path = solve(grid)
        if length < 0:
            continue
        if fallback is None:
            fallback = grid
        if any(is_door(grid[r][c]) for r, c in path):
            return grid
    if fallback is not None:
        return fallback
    # last resort: open an empty corridor so a solution always exists
    grid = [['.'] * n for _ in range(n)]
    grid[0][0], grid[n - 1][n - 1] = 'S', 'E'
    for i in range(t):
        grid[0][1 + i] = KEYS[i]
    return grid


def read_csv(path):
    with open(path, newline='') as f:
        rows = [[(x.strip() or '.') for x in row] for row in csv.reader(f) if row]
    n = len(rows)
    if any(len(r) != n for r in rows):
        raise ValueError("CSV must be an N x N grid")
    return rows


def write_csv(path, grid):
    with open(path, 'w', newline='') as f:
        csv.writer(f).writerows(grid)


def mark_path(grid, path):
    out = [row[:] for row in grid]
    for r, c in path:
        if out[r][c] == '.':
            out[r][c] = 'x'
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', help='read the grid from this CSV (Option 1)')
    ap.add_argument('--n', type=int, default=10, help='size for random maze (Option 2)')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--out', default='solved.csv')
    ap.add_argument('--save-maze', help='also write the (generated) maze to this CSV')
    args = ap.parse_args()

    t = int(sys.stdin.readline().strip())
    if not 1 <= t <= 6:
        sys.exit("T must be between 1 and 6")

    if args.csv:
        grid = read_csv(args.csv)
    else:
        grid = generate(args.n, t, random.Random(args.seed))
        if args.save_maze:
            write_csv(args.save_maze, grid)

    length, path = solve(grid)
    print(length)
    if path:
        write_csv(args.out, mark_path(grid, path))


if __name__ == '__main__':
    main()