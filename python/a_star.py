
import math
def heuristic(current_node, goal_node):
    dx = current_node.x - goal_node.x
    dy = current_node.y - goal_node.y
    dz = (current_node.z - goal_node.z) * 10 # Multiplier compensates for floor height
    return math.sqrt(dx**2 + dy**2 + dz**2)

import heapq

def a_star(graph, start_node, goal_node):
    """
    Executes the A* pathfinding algorithm.
    Returns a list of Node objects representing the shortest path, 
    or None if no path exists.
    """
    # Priority queue stores tuples: (f_score, unique_id, node)
    # The unique_id (using id()) prevents Python from crashing if two nodes 
    # have the exact same f_score, as it won't try to compare the Node objects directly.
    open_set = []
    heapq.heappush(open_set, (0, id(start_node), start_node))
    
    # Dictionary to reconstruct the winning path later
    came_from = {}
    
    # g_score: The exact, known cost from the start node to the current node.
    g_score = {start_node: 0}
    
    # f_score: g_score + estimated cost to the goal (heuristic).
    f_score = {start_node: heuristic(start_node, goal_node)}
    
    # A fast-lookup set to check if a node is currently in the priority queue
    open_set_hash = {start_node}
    
    while open_set:
        # 1. Get the node with the absolute lowest f_score
        current_tuple = heapq.heappop(open_set)
        current = current_tuple[2]
        open_set_hash.remove(current)
        
        # 2. Check if we found the destination
        if current == goal_node:
            # We arrived! Now walk backwards to build the final path list
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start_node)
            return path[::-1] # Reverse the list so it goes from Start -> Goal
            
        # 3. Explore all valid connected edges (neighbors)
        for neighbor_id, move_cost in current.edges.items():
            
            # Fetch the actual Node object on the fly!
            neighbor = graph.nodes[neighbor_id]

            # Calculate what the g_score WOULD be if we took this path
            tentative_g_score = g_score[current] + move_cost
            
            # If this is the fastest way we've ever reached this neighbor...
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                
                # ...save this route!
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal_node)
                
                # If we haven't already queued this neighbor for exploration, add it
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score[neighbor], id(neighbor), neighbor))
                    open_set_hash.add(neighbor)
                    
    # If the while loop completely empties the queue and we never hit the goal, 
    # it means the destination is physically trapped behind walls.
    return None
