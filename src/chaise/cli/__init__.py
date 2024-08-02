"""
CouchDB management tool
"""

import argparse
import logging

from .datafiles import find_dbs


def apply(args):
    """
    Apply the given database descriptions
    """
    print("TODO: apply")
    for db in find_dbs(args.module):
        print(db.name)


def _arg_parser():
    parser = argparse.ArgumentParser(
        prog="chaise",
        description=__doc__,
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging."
    )
    parser.add_argument(
        "--server", metavar="URL", help="Server URL to use (or $COUCHDB_URL)"
    )
    parser.set_defaults(func=lambda args: parser.print_usage())

    subparsers = parser.add_subparsers(title="Subcommands")

    applyp = subparsers.add_parser("apply", help=apply.__doc__)
    applyp.set_defaults(func=apply)
    applyp.add_argument("module")

    return parser


def main():
    args = _arg_parser().parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s %(message)s",
    )

    args.func(args)


if __name__ == "__main__":
    main()
