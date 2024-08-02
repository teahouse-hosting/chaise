"""
CouchDB management tool
"""

import argparse
import logging


def apply(args):
    """
    Apply the given database descriptions
    """
    print("TODO: apply")


def _arg_parser():
    parser = argparse.ArgumentParser(
        prog="chaise",
        description=__doc__,
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging."
    )
    parser.set_defaults(func=lambda args: parser.print_usage())

    subparsers = parser.add_subparsers(title="Subcommands")

    applyp = subparsers.add_parser("apply", help=apply.__doc__)
    applyp.set_defaults(func=apply)

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
