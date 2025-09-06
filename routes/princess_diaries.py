from bisect import bisect_right
from collections import defaultdict
import heapq
from flask import request, jsonify
from routes import app  # uses the shared Flask app created in routes/__init__.py


# ---------- Shortest paths (on needed stations only) ----------
def build_graph(subway):
    g = defaultdict(list)
    for edge in subway:
        u, v = edge["connection"]
        w = int(edge["fee"])
        # if multiple edges exist, keep all; Dijkstra will handle via min path
        g[u].append((v, w))
        g[v].append((u, w))
    return g

def dijkstra(start, graph):
    dist = {}
    pq = [(0, start)]
    dist[start] = 0
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist[u]:
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist

def all_pairs_needed_dists(needed_stations, graph):
    """Return distances[u][v] for u in needed_stations to all v (dict of dict)."""
    distances = {}
    for u in needed_stations:
        distances[u] = dijkstra(u, graph)
    return distances


# ---------- Core solver ----------
def solve_princess_diaries(payload):
    tasks_raw = payload.get("tasks", [])
    subway = payload.get("subway", [])
    s0 = int(payload.get("starting_station"))

    # Edge case: no tasks
    if not tasks_raw:
        return {"max_score": 0, "min_fee": 0, "schedule": []}

    # Normalize tasks
    tasks = []
    stations_needed = {s0}
    for t in tasks_raw:
        name = t["name"]
        start = int(t["start"])
        end = int(t["end"])
        station = int(t["station"])
        score = int(t["score"])
        tasks.append({"name": name, "start": start, "end": end, "station": station, "score": score})
        stations_needed.add(station)

    # Build graph & all needed shortest paths
    graph = build_graph(subway)
    distances = all_pairs_needed_dists(stations_needed, graph)

    # Helper to get d(u,v) safely (graph is connected as per problem)
    def d(u, v):
        if u == v:
            return 0
        return distances[u][v]

    # Weighted interval scheduling setup
    # Sort tasks by end time (stable tie-breakers: then by start, then by name)
    tasks.sort(key=lambda x: (x["end"], x["start"], x["name"]))
    n = len(tasks)

    # Precompute p[i]: index j (1..n) of the last task that finishes <= start_i; 0 if none
    ends = [tasks[i]["end"] for i in range(n)]
    p = [0] * (n + 1)  # 1-based
    for i in range(1, n + 1):
        start_i = tasks[i - 1]["start"]
        # rightmost end <= start_i
        j = bisect_right(ends, start_i) - 1
        p[i] = 0 if j < 0 else (j + 1)

    # DP arrays (1-based for tasks; 0 = empty schedule)
    # We store total fee INCLUDING return to s0, so tie-breaking is correct locally
    dp_score = [0] * (n + 1)
    dp_fee   = [0] * (n + 1)        # total fee including return to s0
    last_idx = [-1] * (n + 1)       # last selected task index for the dp state
    choice   = [0] * (n + 1)        # 0 = skip i, 1 = take i

    # For reconstruction when we take i, remember predecessor index (p[i])
    # Not strictly necessary but makes backtracking trivial.
    for i in range(1, n + 1):
        # Option A: skip i
        best_score = dp_score[i - 1]
        best_fee   = dp_fee[i - 1]
        best_last  = last_idx[i - 1]
        best_choice = 0  # skip

        # Option B: take i
        j = p[i]
        prev_score = dp_score[j]
        prev_fee   = dp_fee[j]
        prev_last  = last_idx[j]

        take_score = prev_score + tasks[i - 1]["score"]

        # Compute fee if we append task i after the schedule represented by dp[j]
        si = tasks[i - 1]["station"]

        if prev_last == -1:
            # First task in the schedule
            take_fee = d(s0, si) + d(si, s0)
        else:
            slast = tasks[prev_last - 1]["station"]
            # Remove old return slast->s0, add slast->si and si->s0
            take_fee = prev_fee - d(slast, s0) + d(slast, si) + d(si, s0)

        # Choose lexicographically: maximize score, then minimize fee
        if (take_score > best_score) or (take_score == best_score and take_fee < best_fee):
            best_score = take_score
            best_fee   = take_fee
            best_last  = i
            best_choice = 1  # take

        dp_score[i] = best_score
        dp_fee[i]   = best_fee
        last_idx[i] = best_last
        choice[i]   = best_choice

    # Reconstruct chosen tasks (indices in 1..n)
    schedule_indices = []
    i = n
    while i > 0:
        if choice[i] == 1:
            schedule_indices.append(i)
            i = p[i]
        else:
            i -= 1
    schedule_indices.reverse()

    # Produce schedule sorted by starting time (requirement)
    selected = [tasks[k - 1] for k in schedule_indices]
    selected.sort(key=lambda x: (x["start"], x["end"], x["name"]))
    schedule_names = [t["name"] for t in selected]

    return {
        "max_score": dp_score[n],
        "min_fee": int(dp_fee[n]),
        "schedule": schedule_names
    }


# ---------- Flask route ----------
@app.route("/princess-diaries", methods=["POST"], endpoint="princess_diaries_post")
def princess_diaries_post():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    try:
        payload = request.get_json()
        result = solve_princess_diaries(payload)
        return jsonify(result)
    except Exception as e:
        # Defensive: return a clear error for malformed inputs
        return jsonify({"error": str(e)}), 400
