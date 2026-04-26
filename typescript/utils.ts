import * as fs from 'fs';
import { aStar } from './a_star.js';
import { Node, Graph, Building } from './graph.js';

export type RoomRegistry = Record<number, { name: string; anchor_node: string }>;

export function exportJson(
    building: Building,
    graph: Graph,
    roomRegistry: RoomRegistry,
    filename: string = "school_map.json"
): void {
    const nodes: Record<string, { x: number; y: number; z: number; edges: Record<string, number> }> = {};

    for (const [nodeId, node] of Object.entries(graph.nodes)) {
        nodes[nodeId] = {
            x: node.x,
            y: node.y,
            z: node.z,
            edges: node.edges
        };
    }

    const exportData = {
        building: building,
        nodes: nodes,
        rooms: roomRegistry
    };
    let jsonString = JSON.stringify(exportData, null, 4);

    jsonString = jsonString.replace(
        /\[\s+((?:\d+,\s*)*\d+)\s+\]/g,
        (_match: string, group1: string) => "[" + group1.replace(/\n/g, "").replace(/ /g, "") + "]"
    );

    fs.writeFileSync(filename, jsonString);
}


export function floodFill(
    building: Building,
    roomRegistry: RoomRegistry,
    target: [number, number, number],
    targetId: number,
    name: string,
    invalid: [number, number] = [1, 300]
): void {
    const [startX, startY, startZ] = target;

    const originalVal = building[startZ][startY][startX];

    if (_inRange(originalVal, invalid) || originalVal === targetId) {
        console.log(`Cannot start flood fill for ${name} on an invalid tile.`);
        return;
    }

    const stack: [number, number, number][] = [[startX, startY, startZ]];
    const directions: [number, number][] = [[0, -1], [0, 1], [-1, 0], [1, 0]];

    const maxZ = Object.keys(building).length;
    const maxY = building[0].length;
    const maxX = building[0][0].length;

    while (stack.length > 0) {
        const [cx, cy, cz] = stack.pop()!;

        if (!(0 <= cz && cz < maxZ && 0 <= cy && cy < maxY && 0 <= cx && cx < maxX)) {
            continue;
        }

        const currVal = building[cz][cy][cx];

        if (_inRange(currVal, invalid) || currVal === targetId) {
            continue;
        }

        building[cz][cy][cx] = targetId;

        for (const [dx, dy] of directions) {
            stack.push([cx + dx, cy + dy, cz]);
        }
    }

    roomRegistry[targetId] = {
        name: name,
        anchor_node: `${startX},${startY},${startZ}`
    };
    console.log(`Successfully created '${name}' (ID: ${targetId}) at anchor ${startX},${startY},${startZ}`);
}


function _mergePathIntoTree(path: Node[], essentialNodes: Record<string, Node>): void {
    for (let i = 0; i < path.length; i++) {
        const currentNode = path[i];

        if (!(currentNode.id in essentialNodes)) {
            essentialNodes[currentNode.id] = new Node(currentNode.id, currentNode.x, currentNode.y, currentNode.z);
        }

        if (i < path.length - 1) {
            const nextNode = path[i + 1];
            const originalCost = currentNode.edges[nextNode.id];

            if (!(nextNode.id in essentialNodes)) {
                essentialNodes[nextNode.id] = new Node(nextNode.id, nextNode.x, nextNode.y, nextNode.z);
            }

            essentialNodes[currentNode.id].edges[nextNode.id] = originalCost;
            essentialNodes[nextNode.id].edges[currentNode.id] = originalCost;
        }
    }
}


export function bakeKioskTree(
    originalGraph: Graph,
    roomRegistry: RoomRegistry,
    kioskId: string
): Graph | null {
    const kioskNode = originalGraph.nodes[kioskId] ?? null;
    if (!kioskNode) {
        console.log(`Error: Kiosk node ${kioskId} not found in graph.`);
        return null;
    }

    const essentialNodes: Record<string, Node> = {};

    console.log(`Baking routes from Kiosk (${kioskId})...`);

    for (const [roomId, roomData] of Object.entries(roomRegistry)) {
        const anchorId = roomData.anchor_node;
        const anchorNode = originalGraph.nodes[anchorId] ?? null;

        if (!anchorNode) {
            console.log(`Warning: Anchor ${anchorId} for Room ${roomId} not found.`);
            continue;
        }

        const path = aStar(originalGraph, kioskNode, anchorNode);

        if (path) {
            _mergePathIntoTree(path, essentialNodes);
        }
    }

    originalGraph.nodes = essentialNodes;

    console.log(`Baking complete! Reduced graph to ${Object.keys(originalGraph.nodes).length} essential nodes.`);

    return originalGraph;
}


function _inRange(val: number, range: [number, number]): boolean {
    return val >= range[0] && val < range[1];
}
