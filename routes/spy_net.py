from flask import request, jsonify
from routes import app  # imports the shared Flask app created in routes/__init__.py


@app.route("/investigate", methods=["POST"], endpoint="investigate_post")
def investigate_post():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    payload = request.get_json(silent=False) or {}
    networks = payload.get("networks", [])
    out = {"networks": []}

    for item in networks:
        network_id = item.get("networkId")
        edges_in = item.get("network", [])

        # Map spy names to integer ids
        id_of = {}
        names = []

        def gid(name: str) -> int:
            if name not in id_of:
                id_of[name] = len(names)
                names.append(name)
            return id_of[name]

        edges = []  # list of (u, v) in input order
        for e in edges_in:
            u = gid(e["spy1"])
            v = gid(e["spy2"])
            edges.append((u, v))

        n = len(names)
        m = len(edges)

        # Build undirected adjacency with edge indices
        adj = [[] for _ in range(n)]
        for ei, (u, v) in enumerate(edges):
            adj[u].append((v, ei))
            adj[v].append((u, ei))

        # Tarjan bridges: edges with low[v] > tin[u] are bridges; others are cycle edges.
        timer = 0
        tin = [-1] * n
        low = [0] * n
        bridges = [False] * m

        def dfs(u: int, parent_edge: int = -1):
            nonlocal timer
            tin[u] = low[u] = timer
            timer += 1
            for v, ei in adj[u]:
                if ei == parent_edge:
                    continue
                if tin[v] != -1:
                    # back edge
                    low[u] = min(low[u], tin[v])
                else:
                    dfs(v, ei)
                    low[u] = min(low[u], low[v])
                    if low[v] > tin[u]:
                        bridges[ei] = True

        for u in range(n):
            if tin[u] == -1:
                dfs(u)

        # Extra channels = edges that are NOT bridges (i.e., in at least one cycle)
        extra = [edges_in[ei] for ei in range(m) if not bridges[ei]]

        out["networks"].append({
            "networkId": network_id,
            "extraChannels": extra
        })

    return jsonify(out)
