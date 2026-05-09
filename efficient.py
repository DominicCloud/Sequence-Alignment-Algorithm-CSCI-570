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
# String generation  (identical to basic.py)
# ---------------------------------------------------------------------------
def generate_string(base, indices):
    s = base
    for idx in indices:
        s = s[:idx + 1] + s + s[idx + 1:]
    return s


# ---------------------------------------------------------------------------
# Input parsing  (identical to basic.py)
# ---------------------------------------------------------------------------
def parse_input(filepath):
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

    return generate_string(s0, s_indices), generate_string(t0, t_indices)


# ---------------------------------------------------------------------------
# Memory helper  (identical to basic.py)
# ---------------------------------------------------------------------------
def process_memory_kb():
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if platform.system() == 'Darwin':
            return usage / 1024.0
        return float(usage)
    except ImportError:
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024.0
        except ImportError:
            return 0.0


# ---------------------------------------------------------------------------
# Space-efficient DP: returns only the LAST ROW using O(n) space
# ---------------------------------------------------------------------------
def _last_row(X, Y):
    """
    Runs the standard sequence-alignment DP over the full X × Y grid but
    keeps only two rows at a time, discarding everything above.

    Returns a list of length len(Y)+1 where result[j] = OPT(len(X), j),
    i.e., the minimum cost to align all of X with Y[:j].

    Time:  O(|X| · |Y|)
    Space: O(|Y|)
    """
    n = len(Y)
    # Base case: aligning empty X with Y[:j] costs j * DELTA
    prev = [j * DELTA for j in range(n + 1)]

    for xi in X:
        curr = [0] * (n + 1)
        curr[0] = prev[0] + DELTA          # align xi with a gap
        for j in range(1, n + 1):
            curr[j] = min(
                ALPHA[xi][Y[j - 1]] + prev[j - 1],   # match / mismatch
                DELTA + prev[j],                       # gap in Y  (xi unmatched)
                DELTA + curr[j - 1],                   # gap in X  (Y[j] unmatched)
            )
        prev = curr

    return prev


# ---------------------------------------------------------------------------
# Base-case alignment via small DP  (used when m == 1 or n == 1)
# ---------------------------------------------------------------------------
def _small_dp_align(X, Y):
    """
    Full O(m·n) DP + traceback on a tiny subproblem.
    Called only by hirschberg() when one dimension equals 1.
    Returns (aligned_X, aligned_Y).
    """
    m, n = len(X), len(Y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i * DELTA
    for j in range(n + 1):
        dp[0][j] = j * DELTA

    for i in range(1, m + 1):
        xi = X[i - 1]
        for j in range(1, n + 1):
            dp[i][j] = min(
                ALPHA[xi][Y[j - 1]] + dp[i - 1][j - 1],
                DELTA + dp[i - 1][j],
                DELTA + dp[i][j - 1],
            )

    # Traceback
    ax, ay = [], []
    i, j = m, n
    while i > 0 and j > 0:
        xi, yj = X[i - 1], Y[j - 1]
        if dp[i][j] == ALPHA[xi][yj] + dp[i - 1][j - 1]:
            ax.append(xi); ay.append(yj); i -= 1; j -= 1
        elif dp[i][j] == DELTA + dp[i - 1][j]:
            ax.append(xi); ay.append('_'); i -= 1
        else:
            ax.append('_'); ay.append(yj); j -= 1
    while i > 0:
        ax.append(X[i - 1]); ay.append('_'); i -= 1
    while j > 0:
        ax.append('_'); ay.append(Y[j - 1]); j -= 1

    return ''.join(reversed(ax)), ''.join(reversed(ay))


# ---------------------------------------------------------------------------
# Hirschberg's divide-and-conquer alignment  –  O(m·n) time, O(m+n) space
# ---------------------------------------------------------------------------
def hirschberg(X, Y):
    """
    Recursively finds the optimal alignment of X and Y using O(m+n) space.

    Key idea
    --------
    Split X at its midpoint q = m//2.
    - Forward pass : _last_row(X[:q], Y)   → f[j] = OPT(q, j)
    - Backward pass: _last_row(rev(X[q:]), rev(Y)) reversed
                   → g[j] = OPT(|X[q:]|, |Y[j:]|)  i.e., cost of right half
    The optimal Y split j* minimises f[j] + g[j].
    Recurse on (X[:q], Y[:j*]) and (X[q:], Y[j*:]), then concatenate.

    Returns (aligned_X, aligned_Y).
    """
    m, n = len(X), len(Y)

    # ---- Base cases --------------------------------------------------------
    if m == 0:
        # All of Y must be gapped
        return '_' * n, Y

    if n == 0:
        # All of X must be gapped
        return X, '_' * m

    if m == 1 or n == 1:
        # Small enough to solve directly with the full DP
        return _small_dp_align(X, Y)

    # ---- Divide ------------------------------------------------------------
    q = m // 2

    # Forward scores: f[j] = cost to align X[:q] with Y[:j]
    f = _last_row(X[:q], Y)

    # Backward scores: g[j] = cost to align X[q:] with Y[j:]
    #
    # Proof of correctness:
    #   _last_row(rev(X[q:]), rev(Y))[k]
    #     = OPT(rev(X[q:]), rev(Y)[:k])
    #     = OPT(rev(X[q:]), rev(Y[n-k:]))
    #     = OPT(X[q:], Y[n-k:])      (reversing both strings preserves cost)
    #   → reversing the array gives index j → OPT(X[q:], Y[j:])
    g_rev = _last_row(X[q:][::-1], Y[::-1])
    g = g_rev[::-1]                  # g[j] = cost(X[q:], Y[j:])

    # ---- Find optimal Y split ----------------------------------------------
    j_star = min(range(n + 1), key=lambda j: f[j] + g[j])

    # ---- Conquer -----------------------------------------------------------
    left_x,  left_y  = hirschberg(X[:q],  Y[:j_star])
    right_x, right_y = hirschberg(X[q:],  Y[j_star:])

    return left_x + right_x, left_y + right_y


# ---------------------------------------------------------------------------
# Top-level driver for the memory-efficient solution
# ---------------------------------------------------------------------------
def sequence_alignment_efficient(X, Y):
    """
    Returns (cost, aligned_X, aligned_Y, memory_kb).

    Cost is obtained with a single space-efficient forward pass (O(n) space).
    Alignment is obtained with Hirschberg's algorithm (O(m+n) space).
    Memory is sampled after hirschberg() returns, while the aligned strings
    (the dominant O(m+n) allocation) are still in scope.
    """
    # Optimal cost via one space-efficient DP sweep
    cost = _last_row(X, Y)[len(Y)]

    # Optimal alignment via divide-and-conquer
    align_x, align_y = hirschberg(X, Y)

    # Sample RSS while aligned strings are still allocated
    mem_kb = process_memory_kb()

    return cost, align_x, align_y, mem_kb


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 efficient.py <input_file> <output_file>")

    input_path  = sys.argv[1]
    output_path = sys.argv[2]

    X, Y = parse_input(input_path)

    start_time = time.time()
    cost, align_x, align_y, mem_kb = sequence_alignment_efficient(X, Y)
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
