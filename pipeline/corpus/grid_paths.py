def grid_paths(rows, cols):
    if rows <= 0 or cols <= 0:
        return 0
    if rows == 1 or cols == 1:
        return 1
    return grid_paths(rows - 1, cols) + grid_paths(rows, cols - 1)
