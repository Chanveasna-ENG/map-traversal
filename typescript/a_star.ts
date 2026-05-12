
import { Node, Graph } from './graph.js';

/**
 * MinHeap implementation to replace Python's heapq.
 * Stores tuples of [fScore, tieBreaker, Node].
 * Compares by fScore first, then tieBreaker to avoid object comparison.
 */
type HeapEntry = [number, number, Node];

class MinHeap {
    private heap: HeapEntry[] = [];

    push(entry: HeapEntry): void {
        this.heap.push(entry);
        this._bubbleUp(this.heap.length - 1);
    }

    pop(): HeapEntry {
        const top = this.heap[0];
        const last = this.heap.pop()!;
        if (this.heap.length > 0) {
            this.heap[0] = last;
            this._bubbleDown(0);
        }
        return top;
    }

    get length(): number {
        return this.heap.length;
    }

    private _compare(a: HeapEntry, b: HeapEntry): number {
        if (a[0] !== b[0]) return a[0] - b[0];
        return a[1] - b[1];
    }

    private _bubbleUp(idx: number): void {
        while (idx > 0) {
            const parentIdx = Math.floor((idx - 1) / 2);
            if (this._compare(this.heap[idx], this.heap[parentIdx]) < 0) {
                [this.heap[idx], this.heap[parentIdx]] = [this.heap[parentIdx], this.heap[idx]];
                idx = parentIdx;
            } else {
                break;
            }
        }
    }

    private _bubbleDown(idx: number): void {
        const length = this.heap.length;
        while (true) {
            let smallest = idx;
            const left = 2 * idx + 1;
            const right = 2 * idx + 2;

            if (left < length && this._compare(this.heap[left], this.heap[smallest]) < 0) {
                smallest = left;
            }
            if (right < length && this._compare(this.heap[right], this.heap[smallest]) < 0) {
                smallest = right;
            }
            if (smallest !== idx) {
                [this.heap[idx], this.heap[smallest]] = [this.heap[smallest], this.heap[idx]];
                idx = smallest;
            } else {
                break;
            }
        }
    }
}

export function heuristic(currentNode: Node, goalNode: Node): number {
    const dx = currentNode.x - goalNode.x;
    const dy = currentNode.y - goalNode.y;
    const dz = (currentNode.z - goalNode.z) * 10; // Multiplier compensates for floor height
    return Math.sqrt(dx ** 2 + dy ** 2 + dz ** 2);
}

let heapCounter = 0;

export function aStar(graph: Graph, startNode: Node, goalNode: Node): Node[] | null {
    /**
     * Executes the A* pathfinding algorithm.
     * Returns a list of Node objects representing the shortest path,
     * or null if no path exists.
     */
    // Priority queue stores tuples: (f_score, unique_id, node)
    // The unique_id (using heapCounter) prevents crashes if two nodes
    // have the exact same f_score, as it won't try to compare the Node objects directly.
    heapCounter = 0;
    const openSet = new MinHeap();
    heapqPush(openSet, 0, startNode);

    // Dictionary to reconstruct the winning path later
    const cameFrom = new Map<Node, Node>();

    // g_score: The exact, known cost from the start node to the current node.
    const gScore = new Map<Node, number>();
    gScore.set(startNode, 0);

    // f_score: g_score + estimated cost to the goal (heuristic).
    const fScore = new Map<Node, number>();
    fScore.set(startNode, heuristic(startNode, goalNode));

    // A fast-lookup set to check if a node is currently in the priority queue
    const openSetHash = new Set<Node>();
    openSetHash.add(startNode);

    while (openSet.length > 0) {
        // 1. Get the node with the absolute lowest f_score
        const currentTuple = openSet.pop();
        let current = currentTuple[2];
        openSetHash.delete(current);

        // 2. Check if we found the destination
        if (current === goalNode) {
            // We arrived! Now walk backwards to build the final path list
            const path: Node[] = [];
            while (cameFrom.has(current)) {
                path.push(current);
                current = cameFrom.get(current)!;
            }
            path.push(startNode);
            return path.reverse(); // Reverse the list so it goes from Start -> Goal
        }

        // 3. Explore all valid connected edges (neighbors)
        for (const [neighborId, moveCost] of Object.entries(current.edges)) {

            // Fetch the actual Node object on the fly!
            const neighbor = graph.nodes[neighborId];

            // Calculate what the g_score WOULD be if we took this path
            const tentativeGScore = (gScore.get(current) ?? Infinity) + moveCost;

            // If this is the fastest way we've ever reached this neighbor...
            if (tentativeGScore < (gScore.get(neighbor) ?? Infinity)) {

                // ...save this route!
                cameFrom.set(neighbor, current);
                gScore.set(neighbor, tentativeGScore);
                fScore.set(neighbor, tentativeGScore + heuristic(neighbor, goalNode));

                // If we haven't already queued this neighbor for exploration, add it
                if (!openSetHash.has(neighbor)) {
                    heapqPush(openSet, fScore.get(neighbor)!, neighbor);
                    openSetHash.add(neighbor);
                }
            }
        }
    }

    // If the while loop completely empties the queue and we never hit the goal,
    // it means the destination is physically trapped behind walls.
    return null;
}

/** Helper to mirror heapq.heappush with auto-incrementing tiebreaker */
function heapqPush(heap: MinHeap, fScore: number, node: Node): void {
    heap.push([fScore, heapCounter++, node]);
}
