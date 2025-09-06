from math import sqrt, ceil
from flask import request, jsonify
from routes import app  # uses the shared app from routes/__init__.py


def latency_points(customer_xy, center_xy):
    """
    Award up to 30 points based on Euclidean distance.
    Tiers chosen to match the example:
      d <= 1*sqrt(2)  -> 30
      d <= 2*sqrt(2)  -> 20
      d <= 3*sqrt(2)  -> 10
      else            -> 0
    """
    dx = customer_xy[0] - center_xy[0]
    dy = customer_xy[1] - center_xy[1]
    d = sqrt(dx * dx + dy * dy)
    step = ceil(d / sqrt(2.0))  # 1,2,3,...
    pts = 30 - 10 * (step - 1)
    return max(0, pts)


@app.route("/ticketing-agent", methods=["POST"], endpoint="ticketing_agent_post")
def ticketing_agent_post():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()
    customers = data.get("customers", [])
    concerts = data.get("concerts", [])
    priority = data.get("priority", {})  # {credit_card: concert_name}

    # Precompute concert info, preserving input order (for tie-breaks)
    concert_info = []
    for c in concerts:
        name = c["name"]
        bx, by = c["booking_center_location"]
        concert_info.append((name, (int(bx), int(by))))

    result = {}

    for cust in customers:
        cname = cust["name"]
        vip = bool(cust["vip_status"])
        cx, cy = cust["location"]
        card = cust["credit_card"]

        base = 100 if vip else 0
        best_tuple = None  # (score, latency_pts, -index, concert_name)

        for idx, (concert_name, center_xy) in enumerate(concert_info):
            score = base

            # +50 if this customer's card has priority for THIS concert
            if priority.get(card) == concert_name:
                score += 50

            # 0..30 latency bonus (closer -> higher)
            lp = latency_points((int(cx), int(cy)), center_xy)
            score += lp

            # Tie-breakers:
            # 1) higher score
            # 2) if tie, higher latency points (closer)
            # 3) if tie, earlier in input order
            key = (score, lp, -idx, concert_name)
            if best_tuple is None or key > best_tuple:
                best_tuple = key

        result[cname] = best_tuple[3] if best_tuple else None

    return jsonify(result)
