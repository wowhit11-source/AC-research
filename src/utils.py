import csv
import os


def save_to_csv(rows: list[dict], path: str) -> None:
    """Save list of dicts to CSV. Creates parent directory if needed. Uses UTF-8."""
    if not rows:
        return
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    headers = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
