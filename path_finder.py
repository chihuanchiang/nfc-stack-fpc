import heapq
import math
import pcbnew
from pcbnew import wxPoint
from typing import List, Tuple, Iterator

DIAGONAL = math.sqrt(2)
RECT_SHAPES = {
    pcbnew.PAD_SHAPE_RECT,
    pcbnew.PAD_SHAPE_ROUNDRECT,
    pcbnew.PAD_SHAPE_CHAMFERED_RECT,
}

# Suppress warnings at type hinting
class Graph:
    pass

class Node:

    def __init__(self, parent: Graph, x: int, y: int):
        self.parent: Graph = parent
        self.x: int = x
        self.y: int = y
        self.cost_so_far: float = float('inf')
        self.previous: Node = None
        self.is_wall: bool = False

    def init_neighbors(self) -> None:
        # W E N S NW SE SW NE
        direction = [
            (self.x - 1, self.y), (self.x + 1, self.y), (self.x, self.y - 1), (self.x, self.y + 1),
            (self.x - 1, self.y - 1), (self.x + 1, self.y + 1), (self.x - 1, self.y + 1), (self.x + 1, self.y - 1),
        ]
        self.adj: List[Node] = [self.parent.node[dir[0]][dir[1]] for dir in direction if self.parent.in_bounds(dir[0], dir[1])]

    def get_neighbors(self):
        return [n for n in self.adj if (not n.is_wall or self.is_wall)]

    def __eq__(self, other):
        return self.cost_so_far == other.cost_so_far

    def __lt__(self, other):
        return self.cost_so_far < other.cost_so_far


class Graph:

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.node: List[Node] = [[Node(self, x, y) for y in range(height)] for x in range(width)]

        for n in self._all_nodes():
            n.init_neighbors()

    def _all_nodes(self) -> Iterator[Node]:
        for col in self.node:
            for n in col:
                yield n

    def in_bounds(self, x: int, y: int) -> bool:
        return (0 <= x < self.width) and (0 <= y < self.height)

    def cost(self, start: Node, end: Node) -> float:
        return 2 if (start.x != end.x) and (start.y != end.y) else 1

    def reset_nodes(self) -> None:
        for n in self._all_nodes():
            n.cost_so_far = float('inf')
            n.previous = None

    def reset_walls(self) -> None:
        for n in self._all_nodes():
            n.is_wall = False

    def set_wall_rect(self, x1: int, x2: int, y1: int, y2: int, state: bool) -> None:
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                if self.in_bounds(x, y):
                    self.node[x][y].is_wall = state

    def set_wall_square(self, x: int, y: int, size: int, state: bool) -> None:
        r = int(size / 2)
        self.set_wall_rect(int(x - r), int(x + r), int(y - r), int(y + r), state)

    def set_wall_diamond(self, x: int, y: int, w: int, h: int, state: bool) -> None:
        for i in range(-w, w + 1):
            for j in range(-h, h + 1):
                if h * abs(i) + w * abs(j) <= w * h:
                    _x = x + i
                    _y = y + j
                    if self.in_bounds(_x, _y):
                        self.node[_x][_y].is_wall = state

    def set_wall_oct(self, x: int, y: int, size: int, state: bool) -> None:
        r = int(size / 2)
        for i in range(-r, r + 1):
            for j in range(-r, r + 1):
                if abs(i) + abs(j) < DIAGONAL * r:
                    _x = x + i
                    _y = y + j
                    if self.in_bounds(_x, _y):
                        self.node[_x][_y].is_wall = state
                        
    def add_wall_rect(self, x1: int, x2: int, y1: int, y2: int) -> None:
        self.set_wall_rect(x1, x2, y1, y2, True)

    def sub_wall_rect(self, x1: int, x2: int, y1: int, y2: int) -> None:
        self.set_wall_rect(x1, x2, y1, y2, False)

    def add_wall_square(self, x: int, y: int, size: int) -> None:
        self.set_wall_square(x, y, size, True)

    def sub_wall_square(self, x: int, y: int, size: int) -> None:
        self.set_wall_square(x, y, size, False)

    def add_wall_diamond(self, x: int, y: int, w: int, h: int) -> None:
        self.set_wall_diamond(x, y, w, h, True)

    def sub_wall_diamond(self, x: int, y: int, w: int, h: int) -> None:
        self.set_wall_diamond(x, y, w, h, False)

    def add_wall_oct(self, x: int, y: int, size: int) -> None:
        self.set_wall_oct(x, y, size, True)

    def sub_wall_oct(self, x: int, y: int, size: int) -> None:
        self.set_wall_oct(x, y, size, False)


class Grid:

    def __init__(self, x1: int, x2: int, y1: int, y2: int, size: int):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        # In pcbnew unit (nm)
        self.origin: wxPoint = wxPoint(x1, y1)
        self.width: int = x2 - x1
        self.height: int = y2 - y1
        self.size: int = size
        # In grid unit
        self.cols: int = int(self.width / size)
        self.rows: int = int(self.height / size)
        self.graph = Graph(self.cols, self.rows)

    def grid_to_pcb(self, x: int, y: int) -> wxPoint:
        return self.origin + wxPoint(x * self.size, y * self.size)

    def pcb_to_grid(self, pos: wxPoint) -> Tuple[int, int]:
        rel_pos = pos - self.origin
        return (int(rel_pos.x / self.size), int(rel_pos.y / self.size))

    def get_node(self, pos: wxPoint) -> Node:
        (x, y) = self.pcb_to_grid(pos)
        return self.graph.node[x][y]

    def set_wall_pad(self, pad: pcbnew.PAD, clearance: int, state: bool) -> None:
        (x, y) = self.pcb_to_grid(pad.GetPosition())
        size = int((pad.GetSizeX() + 2 * clearance) / self.size)
        if pad.GetShape() in RECT_SHAPES:
            self.graph.set_wall_square(x, y, size, state)
        else:
            self.graph.set_wall_oct(x, y, size, state)

    def add_wall_pad(self, pad: pcbnew.PAD, clearance: int) -> None:
        self.set_wall_pad(pad, clearance, True)

    def sub_wall_pad(self, pad: pcbnew.PAD, clearance: int) -> None:
        self.set_wall_pad(pad, clearance, False)

    def add_wall_path(self, path: List[Node], width: int, height: int) -> None:
        w = int(width / self.size)
        h = int(height / self.size)
        for n in path:
            self.graph.add_wall_diamond(n.x, n.y, w, h)


class PriorityQueue:

    def __init__(self):
        self.elements: List[Tuple[float, Node]] = []

    def empty(self) -> bool:
        return not bool(self.elements)

    def push(self, item: Node, priority: float) -> None:
        heapq.heappush(self.elements, (priority, item))

    def pop(self) -> Node:
        return heapq.heappop(self.elements)[1]


def heuristic(src: Node, dst: Node) -> float:
    dx = abs(src.x - dst.x)
    dy = abs(src.y - dst.y)
    return dx + dy + (DIAGONAL - 2) * min(dx, dy)


def a_star_search(graph: Graph, src: Node, dst: Node) -> None:
    frontier = PriorityQueue()
    frontier.push(src, 0)
    src.cost_so_far = 0

    while not frontier.empty():
        current = frontier.pop()
        if current == dst:
            break

        for next in current.get_neighbors():
            new_cost = current.cost_so_far + graph.cost(current, next)
            if new_cost < next.cost_so_far:
                next.cost_so_far = new_cost
                priority = new_cost + heuristic(next, dst)
                frontier.push(next, priority)
                next.previous = current


def is_turn(start: Node, mid: Node, end: Node) -> bool:
    return not ((start.x - mid.x == mid.x - end.x) and (start.y - mid.y == mid.y - end.y))


def find_path(graph: Graph, src: Node, dst: Node) -> List[Node]:
    a_star_search(graph, src, dst)
    path = []
    curr = dst
    while curr:
        path.append(curr)
        curr = curr.previous
    path.reverse()
    return path


def get_vertices(path: List[Node]) -> List[Node]:
    vertices = [path[0]]
    for i in range(1, len(path) - 1):
        if is_turn(path[i - 1], path[i], path[i + 1]):
            vertices.append(path[i])
    vertices.append(path[-1])
    return vertices


def print_graph(graph: Graph, dst: Node) -> None:
    matrix = [[0 for y in range(graph.height)] for x in range(graph.width)]
    current = dst
    while current:
        matrix[current.x][current.y] = 1
        current = current.previous
    matrix[dst.x][dst.y] = 2

    for x in range(graph.width):
        for y in range(graph.height):
            if graph.node[x][y].is_wall:
                matrix[x][y] = 3            
    
    # Print header
    for x in range(graph.width):
        print(x // 10, end=' ')
    print()
    for x in range(graph.width):
        print(x % 10, end=' ')
    print()
    
    # Print matrix
    for y in range(graph.height):
        for x in range(graph.width):
            print(matrix[x][y] if matrix[x][y] > 0 else ' ', end=' ')
        print(y)


def main():
    graph = Graph(40, 20)
    src = graph.node[0][0]
    dst = graph.node[35][4]
    graph.add_wall_rect(10, 14, 0, 7)
    graph.add_wall_square(23, 6, 5)
    graph.sub_wall_square(23, 6, 2)
    graph.add_wall_diamond(30, 9, 2, 4)
    graph.add_wall_oct(7, 18, 7)
    graph.sub_wall_oct(7, 18, 4)
    a_star_search(graph, src, dst)
    print_graph(graph, dst)


if __name__ == "__main__":
    main()