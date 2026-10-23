"""Fixed synthetic patch-selection tasks. Candidates are trusted fixtures, never user code."""

from __future__ import annotations

import random

CASES = [
    (
        "empty-mean",
        "Fix the mean function.",
        [
            "def solve(xs):\n    return sum(xs) / len(xs) if xs else 0",
            "def solve(xs):\n    return sum(xs) / len(xs)",
            "def solve(xs):\n    return sum(xs)",
        ],
        "Empty input must return 0; otherwise return the arithmetic mean.",
        "assert solve([]) == 0; assert solve([2,4]) == 3; assert solve([2]) == 2",
    ),
    (
        "stable-unique",
        "Fix the duplicate removal function.",
        [
            "def solve(xs):\n    return list(dict.fromkeys(xs))",
            "def solve(xs):\n    return sorted(set(xs))",
            "def solve(xs):\n    return xs",
        ],
        "Remove duplicates while preserving first-occurrence order.",
        "assert solve([3,1,3,2]) == [3,1,2]; assert solve([]) == []",
    ),
    (
        "inclusive-range",
        "Fix the interval function.",
        [
            "def solve(a,b):\n    return list(range(a,b+1))",
            "def solve(a,b):\n    return list(range(a,b))",
            "def solve(a,b):\n    return list(range(b,a+1))",
        ],
        "Return every integer from a through b, inclusive.",
        "assert solve(2,4) == [2,3,4]; assert solve(3,3) == [3]",
    ),
    (
        "slug-spaces",
        "Fix the slug helper.",
        [
            "def solve(s):\n    return '-'.join(s.lower().split())",
            "def solve(s):\n    return s.lower().replace(' ', '-')",
            "def solve(s):\n    return s.strip()",
        ],
        "Collapse all whitespace, strip edges, lowercase and join words with one hyphen.",
        "assert solve('  Hello   WORLD ') == 'hello-world'; assert solve('A\\tB') == 'a-b'",
    ),
    (
        "zero-divisor",
        "Fix the division helper.",
        [
            "def solve(a,b):\n    return None if b == 0 else a/b",
            "def solve(a,b):\n    return a/b",
            "def solve(a,b):\n    return 0 if b == 0 else a/b",
        ],
        "Return None for a zero divisor. Preserve normal division otherwise.",
        "assert solve(1,0) is None; assert solve(3,2) == 1.5",
    ),
    (
        "clamp-negative",
        "Fix the clamp helper.",
        [
            "def solve(x):\n    return max(0,min(10,x))",
            "def solve(x):\n    return min(10,x)",
            "def solve(x):\n    return max(0,x)",
        ],
        "Clamp to the closed interval from zero to ten, including negative inputs.",
        "assert solve(-2) == 0; assert solve(15) == 10; assert solve(4) == 4",
    ),
    (
        "case-insensitive",
        "Fix the equality helper.",
        [
            "def solve(a,b):\n    return a.casefold() == b.casefold()",
            "def solve(a,b):\n    return a.lower() == b.lower()",
            "def solve(a,b):\n    return a == b",
        ],
        "Unicode caseless comparison must treat German sharp-s and SS as equal.",
        "assert solve('Straße','STRASSE'); assert not solve('abc','def')",
    ),
    (
        "missing-value",
        "Fix the dictionary lookup.",
        [
            "def solve(d,k):\n    return d.get(k, 'missing')",
            "def solve(d,k):\n    return d.get(k) or 'missing'",
            "def solve(d,k):\n    return d[k]",
        ],
        "Only absent keys return 'missing'. Existing falsy values must be preserved.",
        "assert solve({'x':0},'x') == 0; assert solve({},'x') == 'missing'",
    ),
]


def tasks(seed: int = 7301) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for name, prompt, candidates, contract, checks in CASES:
        indexed = list(enumerate(candidates))
        rng.shuffle(indexed)
        context = "\n".join(
            ["[INFO] collecting synthetic project metadata"] * 30
            + ["[INFO] no external dependencies"] * 20
            + [
                f"[FAIL] {prompt}",
                f"[ASSERT] {contract}",
                f"[SOURCE] {candidates[1]}",
                f"[ASSERT] {checks}",
            ]
        )
        out.append(
            {
                "id": name,
                "prompt": prompt,
                "context": context,
                "candidates": [code for _, code in indexed],
                "checks": checks,
                "correct_index": next(
                    i for i, (original, _) in enumerate(indexed) if original == 0
                ),
            }
        )
    return out
