
export type Building = Record<number, number[][]>;

export class Node {
    id: string;
    x: number;
    y: number;
    z: number;
    edges: Record<string, number>;

    constructor(nodeId: string, xPixel: number, yPixel: number, floorNum: number, edges?: Record<string, number>) {
        this.id = nodeId;
        this.x = xPixel;   // X coordinate on the display
        this.y = yPixel;   // Y coordinate on the display
        this.z = floorNum; // floor number
        this.edges = edges ? edges : {}; // Will dict node_id: Cost
    }
}

export class Graph {
    nodes: Record<string, Node>;               // Dictionary mapping node_id to Node object
    // Use Map to prevent KeyErrors when adding new teleporter groups
    teleport: Map<number, Node[]>;

    building: Building;
    rows: number;
    cols: number;

    teleportIds: [number, number];
    roomIds: [number, number];
    directions: [number, number][];
    wall: number;
    orthogonalCost: number;
    diagonalCost: number;
    stairCost: number;

    constructor(
        building: Building,
        wall: number = 1,
        teleportIdsRange: [number, number] = [100, 200],
        roomIdsRange: [number, number] = [300, 400]
    ) {
        this.nodes = {};
        this.teleport = new Map<number, Node[]>();

        this.building = building;
        this.rows = building[0].length;
        this.cols = building[0][0].length;

        this.teleportIds = teleportIdsRange;
        this.roomIds = roomIdsRange;
        this.directions = [
            [0, -1], [0, 1], [-1, 0], [1, 0],     // Orthogonal
            [-1, -1], [1, -1], [-1, 1], [1, 1]     // Diagonal
        ];
        this.wall = wall;
        this.orthogonalCost = 1;
        this.diagonalCost = 1.414; // sqrt(2)
        this.stairCost = 5; // Defined weight for traversing between floors
        this._createNodes();
        this._connectEdges();
        this._connectFloors();
    }

    // O(N) while N = all nodes represent the map on every floor
    private _createNodes(): void {
        // Pass 1: Create all nodes
        for (const zKey of Object.keys(this.building)) {
            const z = Number(zKey);
            for (let y = 0; y < this.rows; y++) {
                for (let x = 0; x < this.cols; x++) {
                    const val = this.building[z][y][x];
                    let nodeId = "";
                    if (val !== this.wall) {
                        nodeId = `${x},${y},${z}`;
                        this.nodes[nodeId] = new Node(nodeId, x, y, z);
                    }

                    // Group teleport nodes by their specific integer ID (100, 101, etc.)
                    if (val >= this.teleportIds[0] && val < this.teleportIds[1]) {
                        if (!this.teleport.has(val)) {
                            this.teleport.set(val, []);
                        }
                        this.teleport.get(val)!.push(this.nodes[nodeId]);
                    }
                }
            }
        }
    }

    private _isWalkable(node: Node, dx: number, dy: number): boolean {
        // Prevent corner clipping
        const xAxisIsWall = this.building[node.z][node.y][node.x + dx] === 1;
        const yAxisIsWall = this.building[node.z][node.y + dy][node.x] === 1;
        if (dx !== 0 && dy !== 0) {
            return !(xAxisIsWall || yAxisIsWall);
        }
        return true;
    }

    // O(N * 8) while 8 is the number of direction
    private _connectEdges(): void {
        // Pass 2: Connect the orthogonal and diagonal edges
        for (const [, currentNode] of Object.entries(this.nodes)) {
            for (const [dx, dy] of this.directions) {
                const checkX = currentNode.x + dx;
                const checkY = currentNode.y + dy;
                // Edges in this pass only connect nodes on the same floor (currentNode.z)
                const neighborId = `${checkX},${checkY},${currentNode.z}`;

                if (neighborId in this.nodes && this._isWalkable(currentNode, dx, dy)) {
                    const movementCost = (dx !== 0 && dy !== 0) ? this.diagonalCost : this.orthogonalCost;
                    currentNode.edges[neighborId] = movementCost;
                }
            }
        }
    }

    // O(M * P) while M is the number of teleport id, P = sum(k(k+1), k=1, x-1) = (x**3-x)/3 while x is number of each nodes in each teleport id.
    private _connectFloors(): void {
        // Pass 3: Complete the teleport connections across floors
        for (const [, nodes] of this.teleport) {
            // Connect every node sharing the same teleport_id to each other
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const nodeA = nodes[i];
                    const nodeB = nodes[j];

                    // Establish bidirectional connection
                    nodeA.edges[nodeB.id] = this.stairCost;
                    nodeB.edges[nodeA.id] = this.stairCost;
                }
            }
        }
    }
}
