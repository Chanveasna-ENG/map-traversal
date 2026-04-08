from collections import defaultdict

class Node:
    def __init__(self, node_id, x_pixel, y_pixel, floor_num, edges=None):
        self.id = node_id
        self.x = x_pixel # X coordinate on the display
        self.y = y_pixel # Y coordinate on the display
        self.z = floor_num # floor number
        self.edges = edges if edges else {} # Will dict node_id: Cost

class Graph:
    def __init__(self, building, wall=1, teleport_ids_range=(100, 200), room_ids_range=(300, 400)):
        self.nodes = {} # Dictionary mapping node_id to Node object
        # Use defaultdict to prevent KeyErrors when adding new teleporter groups
        self.teleport = defaultdict(list)

        self.building = building
        self.rows = len(building[0])
        self.cols = len(building[0][0])

        self.teleport_ids = range(*teleport_ids_range)
        self.room_ids = range(*room_ids_range)
        self.directions = [
            (0, -1), (0, 1), (-1, 0), (1, 0),   # Orthogonal
            (-1, -1), (1, -1), (-1, 1), (1, 1)  # Diagonal
        ]
        self.wall = wall
        self.orthogonal_cost = 1
        self.diagonal_cost = 1.414 # sqrt(2)
        self.stair_cost = 5 # Defined weight for traversing between floors
        self._create_nodes()
        self._connect_edges()
        self._connect_floors()

    # O(N) while N = all nodes represent the map on every floor
    def _create_nodes(self):
        # Pass 1: Create all nodes
        for z in self.building:
            for y in range(self.rows):
                for x in range(self.cols):
                    val = self.building[z][y][x]
                    node_id = ""
                    if val != self.wall :
                        node_id = f"{x},{y},{z}"
                        self.nodes[node_id] = Node(node_id, x, y, z) 
                    
                    # Group teleport nodes by their specific integer ID (100, 101, etc.)
                    if val in self.teleport_ids:
                        self.teleport[val].append(self.nodes[node_id])
    
    def _is_walkable(self, node, dx, dy):
        # Prevent corner clipping
        x_axis_is_wall = self.building[node.z][node.y][node.x + dx] == 1
        y_axis_is_wall = self.building[node.z][node.y + dy][node.x] == 1
        if dx != 0 and dy != 0: 
            return not (x_axis_is_wall or y_axis_is_wall)
        return True 

    # O(N * 8) while 8 is the number of direction
    def _connect_edges(self):
        # Pass 2: Connect the orthogonal and diagonal edges
        for _,current_node in self.nodes.items():
            for dx, dy in self.directions:
                check_x = current_node.x + dx
                check_y = current_node.y + dy
                # Edges in this pass only connect nodes on the same floor (current_node.z)
                neighbor_id = f"{check_x},{check_y},{current_node.z}" 
                
                if neighbor_id in self.nodes and self._is_walkable(current_node, dx, dy):
                    movement_cost = self.diagonal_cost if (dx != 0 and dy != 0) else self.orthogonal_cost
                    current_node.edges[neighbor_id] = movement_cost

    # O(M * P) while M is the number of teleport id, P = sum(k(k+1), k=1, x-1) = (x**3-x)/3 while x is number of each nodes in each teleport id.
    def _connect_floors(self):
        # Pass 3: Complete the teleport connections across floors
        for _,nodes in self.teleport.items():
            # Connect every node sharing the same teleport_id to each other
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    node_a = nodes[i]
                    node_b = nodes[j]
                    
                    # Establish bidirectional connection
                    node_a.edges[node_b.id] = self.stair_cost
                    node_b.edges[node_a.id] = self.stair_cost
