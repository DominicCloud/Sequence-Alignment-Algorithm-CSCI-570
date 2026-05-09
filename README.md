# CSCI-570 Final Project — Sequence Alignment

Implementation of two sequence alignment algorithms:

- **Basic** (`basic.py`): Dynamic programming, O(mn) time and space
- **Efficient** (`efficient.py`): DP + Divide-and-Conquer, O(mn) time, O(m+n) space

## Usage

```bash
./basic.sh input.txt output.txt
./efficient.sh input.txt output.txt
```

## Output format

Each output file contains 5 lines:
1. Alignment cost (integer)
2. First string alignment (A/C/T/G/_ characters)
3. Second string alignment (A/C/T/G/_ characters)
4. Time in milliseconds (float)
5. Memory in kilobytes (float)
