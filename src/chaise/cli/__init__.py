"""
CouchDB management tool
"""

import argparse


parser = argparse.ArgumentParser(
    prog="chaise",
    description=__doc__,
)


def main():
    _ = parser.parse_args()


if __name__ == "__main__":
    main()
