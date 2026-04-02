#!/usr/bin/env python3
"""Hadoop Streaming mapper: emits (filename, 1) for each line read from stdin.
"""
import os
import sys


def main():
    current_file = os.environ.get(
        "mapreduce_map_input_file",
        os.environ.get("map_input_file", "UNKNOWN"),
    )
    for _ in sys.stdin:
        print("{}\t{}".format(current_file, 1))


if __name__ == "__main__":
    main()
