import re
import json

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