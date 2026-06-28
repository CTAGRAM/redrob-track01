"""Memory-safe streaming reader for the 100K-line JSONL candidate pool.

We never load the full 487 MB file into a single string; we yield one parsed
record at a time so peak memory stays well under the 16 GB budget.
"""

import gzip
import json


def stream_candidates(path):
    """Yield candidate dicts from a .jsonl or .jsonl.gz file, one at a time."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
