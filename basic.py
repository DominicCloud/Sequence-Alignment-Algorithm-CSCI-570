import sys
import time
import platform

# ---------------------------------------------------------------------------
# Hardcoded penalties (δ and α)
# ---------------------------------------------------------------------------
DELTA = 30

ALPHA = {
    'A': {'A': 0,   'C': 110, 'G': 48,  'T': 94},
    'C': {'A': 110, 'C': 0,   'G': 118, 'T': 48},
    'G': {'A': 48,  'C': 118, 'G': 0,   'T': 110},
    'T': {'A': 94,  'C': 48,  'G': 110, 'T': 0},
}


# ---------------------------------------------------------------------------
# String generation
# ---------------------------------------------------------------------------
def generate_string(base, indices):
    """
    Starting from `base`, repeatedly insert the current string into itself
    right after position `idx` (0-indexed) for each idx in `indices`.
    Each step doubles the string length.
    """
    s = base
    for idx in indices:
        s = s[:idx + 1] + s + s[idx + 1:]
    return s


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------
def parse_input(filepath):
    """
    File format:
        s0          <- base string for X (alphabetic)
        n1          <- insertion index (integer)
        ...         <- more indices
        t0          <- base string for Y (alphabetic)
        m1          <- insertion index (integer)
        ...         <- more indices

    Lines that are purely alphabetic belong to a base string;
    lines that are purely digits belong to the index list.
    """
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    s0 = lines[i];  i += 1

    s_indices = []
    while i < len(lines) and lines[i].isdigit():
        s_indices.append(int(lines[i]))
        i += 1

    t0 = lines[i];  i += 1

    t_indices = []
    while i < len(lines) and lines[i].isdigit():
        t_indices.append(int(lines[i]))
        i += 1

    X = generate_string(s0, s_indices)
    Y = generate_string(t0, t_indices)
    return X, Y


# ---------------------------------------------------------------------------
# Memory helper  (measured in KB using RSS)
# ---------------------------------------------------------------------------
def process_memory_kb():
    """
    On Linux/macOS (including the grading server): uses the stdlib `resource`
    module — no external packages needed.
    On Windows (local dev): falls back to `psutil` if installed, else 0.
    """
    try:
        import resource  # stdlib, available on Linux / macOS
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux  → ru_maxrss is in KB
        # macOS  → ru_maxrss is in bytes
        if platform.system() == 'Darwin':
            return usage / 1024.0
        return float(usage)
    except ImportError:
        # Windows fallback
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024.0
        except ImportError:
            return 0.0


# ---------------------------------------------------------------------------
# Basic DP sequence alignment  –  O(m·n) time and space
# ---------------------------------------------------------------------------
def sequence_alignment(X, Y):
    """
    Returns (cost, aligned_X, aligned_Y, memory_kb).

    Memory is sampled *inside* this function while the DP table is still
    allocated, as required by the project spec.
    """
    m, n = len(X), len(Y)

    # ---- Build DP table ----
    # dp[i][j] = min cost to align X[0..i-1] with Y[0..j-1]
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i * DELTA
    for j in range(n + 1):
        dp[0][j] = j * DELTA

    for i in range(1, m + 1):
        xi = X[i - 1]
        for j in range(1, n + 1):
            cost_match = ALPHA[xi][Y[j - 1]] + dp[i - 1][j - 1]
            cost_gap_y = DELTA + dp[i - 1][j]   # X[i] aligned with gap
            cost_gap_x = DELTA + dp[i][j - 1]   # Y[j] aligned with gap
            dp[i][j] = min(cost_match, cost_gap_y, cost_gap_x)

    cost = dp[m][n]

    # Sample memory while the DP table is still in scope
    mem_kb = process_memory_kb()

    # ---- Traceback ----
    align_x = []
    align_y = []
    i, j = m, n

    while i > 0 and j > 0:
        xi, yj = X[i - 1], Y[j - 1]
        if dp[i][j] == ALPHA[xi][yj] + dp[i - 1][j - 1]:
            align_x.append(xi)
            align_y.append(yj)
            i -= 1
            j -= 1
        elif dp[i][j] == DELTA + dp[i - 1][j]:
            # X[i] aligned with a gap in Y
            align_x.append(xi)
            align_y.append('_')
            i -= 1
        else:
            # Y[j] aligned with a gap in X
            align_x.append('_')
            align_y.append(yj)
            j -= 1

    # Exhaust remaining characters
    while i > 0:
        align_x.append(X[i - 1])
        align_y.append('_')
        i -= 1
    while j > 0:
        align_x.append('_')
        align_y.append(Y[j - 1])
        j -= 1

    align_x = ''.join(reversed(align_x))
    align_y = ''.join(reversed(align_y))

    return cost, align_x, align_y, mem_kb


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 basic.py <input_file> <output_file>")

    input_path  = sys.argv[1]
    output_path = sys.argv[2]

    X, Y = parse_input(input_path)

    start_time = time.time()
    cost, align_x, align_y, mem_kb = sequence_alignment(X, Y)
    end_time = time.time()

    time_ms = (end_time - start_time) * 1000.0

    with open(output_path, 'w') as f:
        f.write(f"{cost}\n")
        f.write(f"{align_x}\n")
        f.write(f"{align_y}\n")
        f.write(f"{time_ms}\n")
        f.write(f"{mem_kb}\n")


if __name__ == "__main__":
    main()
