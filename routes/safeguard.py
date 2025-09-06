import re
import math
from collections import Counter
from statistics import median
from flask import request, jsonify
from routes import app  # shared Flask app from routes/__init__.py


# ----------------------------
# Challenge 1: Reverse transforms
# ----------------------------

VOWELS = set("aeiouAEIOU")

def is_letter(ch):
    return ("A" <= ch <= "Z") or ("a" <= ch <= "z")

def is_consonant(ch):
    return is_letter(ch) and ch not in VOWELS

def inv_mirror_words(s: str) -> str:
    # self-inverse
    return " ".join(w[::-1] for w in s.split(" "))

def inv_encode_mirror_alphabet(s: str) -> str:
    # Atbash (self-inverse)
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(chr(ord('Z') - (ord(ch) - ord('A'))))
        elif "a" <= ch <= "z":
            out.append(chr(ord('z') - (ord(ch) - ord('a'))))
        else:
            out.append(ch)
    return "".join(out)

def inv_toggle_case(s: str) -> str:
    # self-inverse
    return s.swapcase()

def inv_swap_pairs(s: str) -> str:
    # self-inverse; operate per word
    def swap_word(w):
        chars = list(w)
        out = []
        i = 0
        while i < len(chars) - 1:
            out.append(chars[i + 1])
            out.append(chars[i])
            i += 2
        if i < len(chars):
            out.append(chars[i])
        return "".join(out)
    return " ".join(swap_word(w) for w in s.split(" "))

def inv_encode_index_parity(s: str) -> str:
    # Inverse of: even indices first, then odd indices (0-based), per word
    def inv_word(w):
        n = len(w)
        evens_len = (n + 1) // 2
        evens = list(w[:evens_len])
        odds = list(w[evens_len:])
        out = [''] * n
        ei = 0
        oi = 0
        for i in range(n):
            if i % 2 == 0:
                out[i] = evens[ei]
                ei += 1
            else:
                out[i] = odds[oi]
                oi += 1
        return "".join(out)
    return " ".join(inv_word(w) for w in s.split(" "))

def inv_double_consonants(s: str) -> str:
    # Undo doubling: collapse pairs of identical consonants
    def inv_word(w):
        out = []
        i = 0
        while i < len(w):
            ch = w[i]
            if i + 1 < len(w) and ch == w[i + 1] and is_consonant(ch):
                out.append(ch)
                i += 2
            else:
                out.append(ch)
                i += 1
        return "".join(out)
    return " ".join(inv_word(w) for w in s.split(" "))

# Map function names to inverse functions
INVERSES = {
    "mirror_words": inv_mirror_words,
    "encode_mirror_alphabet": inv_encode_mirror_alphabet,
    "toggle_case": inv_toggle_case,
    "swap_pairs": inv_swap_pairs,
    "encode_index_parity": inv_encode_index_parity,
    "double_consonants": inv_double_consonants,
}

def parse_transform_list(s: str):
    """
    Input format example:
      "[encode_mirror_alphabet(x), double_consonants(x), mirror_words(x), swap_pairs(x), encode_index_parity(x)]"
    We'll extract function names in order.
    """
    return re.findall(r'([a-z_]+)\s*\(', s)


def solve_challenge_one(block: dict) -> str:
    # Reverse the given transformations (apply inverses in reverse order).
    trans_str = block.get("transformations", "") or ""
    cipher = block.get("transformed_encrypted_word", "") or ""
    funcs = parse_transform_list(trans_str)
    # apply inverses in reverse order
    s = cipher
    for fname in reversed(funcs):
        inv = INVERSES.get(fname)
        if inv is None:
            # if unknown, treat as identity (robustness)
            continue
        s = inv(s)
    return s


# ----------------------------
# Challenge 2: Coordinate pattern → number
# ----------------------------
def solve_challenge_two(coords):
    """
    Robust numeric extraction:
    1) Normalize points (float) to tuples.
    2) Remove gross outliers by radius-to-centroid using MAD.
    3) Compute all pairwise distances among remaining points.
    4) Find the dominant spacing (mode-ish) via binning → return rounded int.
       This tends to reveal simple, significant structure (e.g., grid step, diameter).
    If too few points or degenerate, fall back to rounded distance from min->max (bounding-box diagonal).
    """
    if not coords:
        return 0

    pts = []
    for xy in coords:
        try:
            x = float(xy[0]); y = float(xy[1])
            pts.append((x, y))
        except Exception:
            continue
    if len(pts) == 0:
        return 0

    # Centroid
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    radii = [math.hypot(x - cx, y - cy) for x, y in pts]
    if len(radii) >= 3:
        med = median(radii)
        mad = median([abs(r - med) for r in radii]) or 1.0
        keep = []
        for (p, r) in zip(pts, radii):
            # threshold 3 * MAD (~robust)
            if abs(r - med) <= 3 * mad:
                keep.append(p)
        pts = keep if len(keep) >= 3 else pts

    if len(pts) < 2:
        return 0

    # Pairwise distances
    dists = []
    for i in range(len(pts)):
        x1, y1 = pts[i]
        for j in range(i + 1, len(pts)):
            x2, y2 = pts[j]
            dists.append(round(math.hypot(x2 - x1, y2 - y1), 6))

    if not dists:
        return 0

    # Bin to find dominant spacing
    bin_size = max(0.1, (max(dists) - min(dists)) / 50.0)
    bins = Counter(int(d / bin_size) for d in dists)
    k, _ = bins.most_common(1)[0]
    dominant = (k + 0.5) * bin_size  # bin center
    # The "simple yet significant" is an integer parameter
    return int(round(dominant))


# ----------------------------
# Challenge 3: Log parsing & cipher decryption
# ----------------------------
def parse_log_entry(s: str):
    parts = [p.strip() for p in s.split("|")]
    out = {}
    for part in parts:
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().upper()] = v.strip()
    return out

def rot_n(s: str, n: int):
    out = []
    n = n % 26
    for ch in s:
        if "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 - n) % 26 + 65))
        elif "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 - n) % 26 + 97))
        else:
            out.append(ch)
    return "".join(out)

def railfence3_decrypt(ct: str):
    # Standard 3-rail rail fence decryption
    n = len(ct)
    # pattern indices for zigzag rails
    pattern = []
    rail = 0
    dir = 1
    for i in range(n):
        pattern.append(rail)
        rail += dir
        if rail == 0 or rail == 2:
            dir *= 1
        if rail == 2:
            dir = -1
        elif rail == 0:
            dir = 1
    # Count chars per rail
    counts = [pattern.count(0), pattern.count(1), pattern.count(2)]
    idx = 0
    rails = []
    for c in counts:
        rails.append(list(ct[idx:idx+c]))
        idx += c
    # Reconstruct
    pos = [0, 0, 0]
    out = []
    for r in pattern:
        out.append(rails[r][pos[r]])
        pos[r] += 1
    return "".join(out)

def build_keyword_alphabet(keyword: str):
    seen = set()
    key_up = []
    for ch in keyword.upper():
        if "A" <= ch <= "Z" and ch not in seen:
            seen.add(ch); key_up.append(ch)
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            key_up.append(ch)
    # cipher alphabet (encryption) = key_up; plaintext = ABC...
    return "".join(key_up)

def keyword_decrypt(ct: str, keyword: str):
    # monoalphabetic substitution; alphabet built from keyword
    cipher_alpha = build_keyword_alphabet(keyword)
    plain_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    inv = {c: p for c, p in zip(cipher_alpha, plain_alpha)}
    out = []
    for ch in ct:
        if "A" <= ch <= "Z":
            out.append(inv[ch])
        elif "a" <= ch <= "z":
            out.append(inv[ch.upper()].lower())
        else:
            out.append(ch)
    return "".join(out)

def polybius_decrypt(ct: str):
    # Expect digit pairs (1-5)(1-5), spaces preserved; I/J combined at (2,4)
    table = [
        "ABCDE",
        "FGHIJ",  # J shares cell with I
        "KLMNO",
        "PQRST",
        "UVWXY",
    ]
    # Build mapping
    mp = {}
    for r in range(5):
        for c in range(5):
            val = table[r][c]
            key = f"{r+1}{c+1}"
            mp[key] = "I" if val in ("I", "J") else val
    # Extract digit pairs
    out = []
    i = 0
    digits = re.sub(r"[^0-9]", "", ct)
    # If no digits, return original
    if len(digits) < 2:
        return ct
    while i + 1 < len(digits):
        pair = digits[i:i+2]
        out.append(mp.get(pair, "?"))
        i += 2
    return "".join(out)

def solve_challenge_three(logline: str) -> str:
    fields = parse_log_entry(logline or "")
    ctype = (fields.get("CIPHER_TYPE") or "").upper()
    payload = fields.get("ENCRYPTED_PAYLOAD") or ""

    if ctype == "ROTATION_CIPHER":
        # Default to ROT13 as per common operational use (e.g., SVERJNYY -> FIREWALL)
        return rot_n(payload, 13).upper()

    elif ctype == "RAILFENCE":
        return railfence3_decrypt(payload).upper()

    elif ctype == "KEYWORD":
        # Fixed keyword per spec
        return keyword_decrypt(payload.upper(), "SHADOW").upper()

    elif ctype == "POLYBIUS":
        return polybius_decrypt(payload).upper()

    # Unknown: best-effort try ROT13
    return rot_n(payload, 13).upper()


# ----------------------------
# Challenge 4: Final synthesis
# ----------------------------
def strengthen_keyword(base_keyword: str, extra: str) -> str:
    """
    Merge extra recovered string into front of the base keyword (deduped),
    reinforcing the cipher as per intel.
    """
    merged = "".join(dict.fromkeys((extra or "") + (base_keyword or "")))  # dedupe, keep order
    # Keep only letters
    merged = "".join(ch for ch in merged.upper() if "A" <= ch <= "Z")
    return merged or base_keyword or "SHADOW"

def final_decrypt(ciphertext: str, recovered1: str, recovered_number: int):
    """
    Vault-lock model from the intel:
      1) Base lock: Keyword substitution with 'SHADOW' strengthened by recovered1.
      2) Pressure: A global Caesar rotation by the recovered number.
    Decrypt = inverse of above in reverse order:
      a) Undo Caesar by N
      b) Undo keyword substitution
    """
    if not ciphertext:
        return ""

    # a) undo Caesar by N (rotate back)
    step = int(recovered_number or 0) % 26
    after_rot = rot_n(ciphertext, step)

    # b) undo keyword substitution (with strengthened keyword)
    strong_key = strengthen_keyword("SHADOW", recovered1)
    plain = keyword_decrypt(after_rot.upper(), strong_key)
    return plain.upper()


# ----------------------------
# Flask route
# ----------------------------
@app.route("/operation-safeguard", methods=["POST"], endpoint="operation_safeguard_post")
def operation_safeguard_post():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    try:
        payload = request.get_json()

        # Challenge 1
        ch1 = payload.get("challenge_one", {}) or {}
        ans1 = solve_challenge_one(ch1)

        # Challenge 2
        coords = payload.get("challenge_two", []) or []
        ans2 = solve_challenge_two(coords)

        # Challenge 3
        logline = payload.get("challenge_three", "") or ""
        ans3 = solve_challenge_three(logline)

        # Challenge 4
        # Accept final ciphertext in any of these keys if provided
        final_ct = (
            payload.get("final_message")
            or payload.get("challenge_four_ciphertext")
            or payload.get("ciphertext")
            or ""
        )
        if final_ct:
            ans4 = final_decrypt(final_ct, ans1, ans2)
        else:
            # If no final message provided, return a meaningful synthesis string
            ans4 = f"{ans3}::{ans2}"

        return jsonify({
            "challenge_one": ans1,
            "challenge_two": ans2,
            "challenge_three": ans3,
            "challenge_four": ans4
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
