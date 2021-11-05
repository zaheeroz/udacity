import numpy as np

from enum import Enum
from queue import PriorityQueue



def create_grid(data, drone_altitude, safety_distance):
    north_min = np.floor(np.min(data[:, 0] - data[:, 3]))
    north_max = np.ceil( np.max(data[:, 0] + data[:, 3]))

    east_min = np.floor(np.min(data[:, 1] - data[:, 4]))
    east_max = np.ceil( np.max(data[:, 1] + data[:, 4]))

    north_size = int(np.ceil(north_max - north_min))
    east_size  = int(np.ceil(east_max  - east_min))

    grid = np.zeros((north_size, east_size))

    for i in range(data.shape[0]):
        north, east, alt, d_north, d_east, d_alt = data[i, :]

        if alt + d_alt + safety_distance > drone_altitude:
            obstacle = [
                int(np.clip(north - d_north - safety_distance - north_min, 0, north_size - 1)),
                int(np.clip(north + d_north + safety_distance - north_min, 0, north_size - 1)),
                int(np.clip(east  - d_east  - safety_distance - east_min,  0, east_size  - 1)),
                int(np.clip(east  + d_east  + safety_distance - east_min,  0, east_size  - 1))
            ]

            grid[obstacle[0]:obstacle[1] + 1, obstacle[2]:obstacle[3] + 1] = 1

    return grid, int(north_min), int(east_min)



class Action(Enum):
    WEST   = ( 0, -1, 1)
    EAST   = ( 0,  1, 1)
    NORTH  = (-1,  0, 1)
    SOUTH  = ( 1,  0, 1)
    N_WEST = (-1, -1, np.sqrt(2))
    N_EAST = (-1,  1, np.sqrt(2))
    S_WEST = ( 1, -1, np.sqrt(2))
    S_EAST = ( 1,  1, np.sqrt(2))

    @property
    def cost(self):
        return self.value[2]

    @property
    def delta(self):
        return (self.value[0], self.value[1])



def valid_actions(grid, current_node):
    valid_actions = list(Action)
    n, m          = grid.shape[0] - 1, grid.shape[1] - 1
    x, y          = current_node

    if x - 1 < 0 or grid[x - 1, y    ] == 1: valid_actions.remove(Action.NORTH)
    if x + 1 > n or grid[x + 1, y    ] == 1: valid_actions.remove(Action.SOUTH)
    if y - 1 < 0 or grid[x,     y - 1] == 1: valid_actions.remove(Action.WEST)
    if y + 1 > m or grid[x,     y + 1] == 1: valid_actions.remove(Action.EAST)

    if ((x - 1 < 0) | (y - 1 < 0)) or grid[x - 1, y - 1] == 1: valid_actions.remove(Action.N_WEST)
    if ((x - 1 < 0) | (y + 1 > m)) or grid[x - 1, y + 1] == 1: valid_actions.remove(Action.N_EAST)
    if ((x + 1 > n) | (y - 1 < 0)) or grid[x + 1, y - 1] == 1: valid_actions.remove(Action.S_WEST)
    if ((x + 1 > n) | (y + 1 > m)) or grid[x + 1, y + 1] == 1: valid_actions.remove(Action.S_EAST)

    return valid_actions



def a_star(grid, h, start, goal):
    path      = []
    path_cost = 0
    queue     = PriorityQueue()
    branch    = {}
    found     = False
    visited   = set(start)

    queue.put((0, start))

    while not queue.empty():
        item         = queue.get()
        current_node = item[1]

        if current_node == start: current_cost = 0.0
        else:                     current_cost = branch[current_node][0]
            
        if current_node == goal:        
            print('[INFO] found a path')

            found = True

            break

        else:
            for action in valid_actions(grid, current_node):
                da          = action.delta
                next_node   = (current_node[0] + da[0], current_node[1] + da[1])
                branch_cost = current_cost + action.cost
                queue_cost  = branch_cost + h(next_node, goal)
                
                if next_node not in visited:                
                    visited.add(next_node)

                    branch[next_node] = (branch_cost, current_node, action)

                    queue.put((queue_cost, next_node))
             
    if found:
        n         = goal
        path_cost = branch[n][0]

        path.append(goal)

        while branch[n][1] != start:
            path.append(branch[n][1])

            n = branch[n][1]

        path.append(branch[n][1])

    else:
        print('[WARN] failed to find a path!')

    return path[::-1], path_cost



def heuristic(position, goal_position):
    return np.linalg.norm(np.array(position) - np.array(goal_position))



def point(p):
    return np.array([p[0], p[1], 1.]).reshape(1, -1)



def collinearity_check(p1, p2, p3, epsilon=1e-6):
    m   = np.concatenate((p1, p2, p3), 0)
    det = np.linalg.det(m)

    return abs(det) < epsilon



def prune_path(path):
    if path is not None:
        pruned_path = [p for p in path]
        idx         = 0

        for _ in pruned_path[:-2]:
            p1 = point(pruned_path[idx    ])
            p2 = point(pruned_path[idx + 1])
            p3 = point(pruned_path[idx + 2])

            if collinearity_check(p1, p2, p3): del pruned_path[idx + 1]
            else:                              idx += 1

    else:
        pruned_path = path

    return pruned_path