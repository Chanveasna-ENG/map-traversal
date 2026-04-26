import re
import json
from a_star import a_star
from graph import Node # Ensure Node is imported for the helper


def export_json(building, graph, room_registry, filename="school_map.json"):
    nodes = {}
    export_data = {}

    for node_id, node in graph.nodes.items():
        # Convert the list of Node objects into a list of Node IDs
        nodes[node_id] = {
            "x": node.x,
            "y": node.y,
            "z": node.z,
            "edges": node.edges
        }

    export_data = {
        "building": building,
        "nodes": nodes,
        "rooms": room_registry
    }
    json_string = json.dumps(export_data, indent=4)

    # 2. Use Regex to find lists of numbers and squash them into one line
    # This looks for patterns like [ 1, 0, 100 ] and removes the newlines/extra spaces
    json_string = re.sub(
        r'\[\s+((?:\d+,\s*)*\d+)\s+\]', 
        lambda m: "[" + m.group(1).replace("\n", "").replace(" ", "") + "]", 
        json_string
    )
    with open(filename, 'w') as f:
        f.write(json_string)


def flood_fill(building, room_registry, target, target_id, name, invalid=(1,300)):
    """
    Fills a bounded area in the building array with a new room ID.
    Uses a Stack (Depth-First Search) to evaluate neighbors.
    
    target: tuple of (x, y, z) representing the starting coordinate.
    target_id: integer representing the new room (e.g., 301).
    name: string for the human-readable room name.
    """
    start_x, start_y, start_z = target
    
    # 1. Guard Clauses
    # Ensure the starting point is valid before processing
    original_val = building[start_z][start_y][start_x]
    
    # Do not fill walls or other object, or areas already marked with this target_id
    if original_val in range(*invalid) or original_val == target_id:
        print(f"Cannot start flood fill for {name} on an invalid tile.")
        return
        
    # 2. Setup the Stack and Constraints
    stack = [(start_x, start_y, start_z)]
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)] # 4-Way
    
    max_z = len(building)
    max_y = len(building[0])
    max_x = len(building[0][0])
    
    # 3. The Fill Loop
    while stack:
        cx, cy, cz = stack.pop()
        
        # Check boundaries to prevent out-of-index errors
        if not (0 <= cz < max_z and 0 <= cy < max_y and 0 <= cx < max_x):
            continue
            
        curr_val = building[cz][cy][cx]
        
        # # Stop filling if we hit a wall, a teleporter, or a tile we already changed
        # if curr_val == 1 or curr_val >= 100 or curr_val == target_id:
        #     continue
        if curr_val in range(*invalid) or curr_val == target_id:
            continue

        # Change the pixel to the new room ID
        building[cz][cy][cx] = target_id
        
        # Push all valid 4-way neighbors onto the stack
        for dx, dy in directions:
            stack.append((cx + dx, cy + dy, cz))
            
    # 4. Update the Room Registry
    # The initial click target acts as the anchor point
    room_registry[target_id] = {
        "name": name,
        "anchor_node": f"{start_x},{start_y},{start_z}"
    }
    print(f"Successfully created '{name}' (ID: {target_id}) at anchor {start_x},{start_y},{start_z}")


def _merge_path_into_tree(path, essential_nodes):
    """
    Helper function to take a calculated A* path and merge its nodes 
    and edges into the essential_nodes dictionary as clean copies.
    """
    for i in range(len(path)):
        current_node = path[i]
        
        # If we haven't seen this node yet, add a clean version
        if current_node.id not in essential_nodes:
            essential_nodes[current_node.id] = Node(current_node.id, current_node.x, current_node.y, current_node.z)
        
        # If there is a next step in the path, record that specific edge
        if i < len(path) - 1:
            next_node = path[i+1]
            
            # We need the original cost to move between these two
            original_cost = current_node.edges[next_node.id]
            
            # Ensure bidirectional flow just in case the frontend needs it
            if next_node.id not in essential_nodes:
                essential_nodes[next_node.id] = Node(next_node.id, next_node.x, next_node.y, next_node.z)
            
            # Add the edge to our clean nodes
            essential_nodes[current_node.id].edges[next_node.id] = original_cost
            essential_nodes[next_node.id].edges[current_node.id] = original_cost


def bake_kiosk_tree(original_graph, room_registry, kiosk_id):
    """
    Takes the full dense graph and strips away everything except 
    the shortest paths from the Kiosk to every registered room.
    """
    kiosk_node = original_graph.nodes.get(kiosk_id)
    if not kiosk_node:
        print(f"Error: Kiosk node {kiosk_id} not found in graph.")
        return None

    # We will store only the nodes and edges that are actually used
    essential_nodes = {}
    
    print(f"Baking routes from Kiosk ({kiosk_id})...")

    # 1. Trace the path to every single room
    for room_id, room_data in room_registry.items():
        anchor_id = room_data["anchor_node"]
        anchor_node = original_graph.nodes.get(anchor_id)
        
        if not anchor_node:
            print(f"Warning: Anchor {anchor_id} for Room {room_id} not found.")
            continue

        # Run your existing A* algorithm
        path = a_star(original_graph, kiosk_node, anchor_node)
        
        if path:
            # Delegate the node duplication and edge linking to the helper
            _merge_path_into_tree(path, essential_nodes)

    # 2. Replace the massive node dictionary with our tiny pruned one
    original_graph.nodes = essential_nodes
    
    # Calculate how much bloat we removed
    print(f"Baking complete! Reduced graph to {len(original_graph.nodes)} essential nodes.")
    
    return original_graph