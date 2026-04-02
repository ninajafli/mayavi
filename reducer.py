#!/usr/bin/env python3
"""Hadoop Streaming reducer: sums line counts per file.
"""
import sys


def main():
    current_file = None
    current_count = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        filepath, count_str = parts
        try:
            count = int(count_str)
        except ValueError:
            continue

        if filepath == current_file:
            current_count += count
        else:
            if current_file is not None:
                print('"{}": {}'.format(current_file, current_count))
            current_file = filepath
            current_count = count

    if current_file is not None:
        print('"{}": {}'.format(current_file, current_count))


if __name__ == "__main__":
    main()
