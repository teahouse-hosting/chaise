"""
CouchDB management tool
"""

import argparse
import anyio
import logging
import os

from .. import Missing
from .datafiles import find_dbs
from .client import ConstantPool


async def apply(args):
    """
    Apply the given database descriptions
    """
    session = await ConstantPool(args.server).session()

    # Ensure all the dbs exist
    for db in find_dbs(args.module):
        try:
            await session.get_db(db.name)
        except Missing:
            print(f"Creating {db.name}...")  # TODO: Logging
            await session.create_db(db.name)
        else:
            print(f"{db.name} exists")


def _arg_parser():
    async def usage():
        parser.print_usage()

    parser = argparse.ArgumentParser(
        prog="chaise",
        description=__doc__,
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging."
    )
    parser.add_argument(
        "--server",
        metavar="URL",
        help="Server URL to use (or $COUCHDB_URL)",
        default=...,
    )
    parser.set_defaults(func=usage)

    subparsers = parser.add_subparsers(title="Subcommands")

    applyp = subparsers.add_parser("apply", help=apply.__doc__)
    applyp.set_defaults(func=apply)
    applyp.add_argument("module")

    return parser


async def main():
    args = _arg_parser().parse_args()

    if args.server is ...:
        args.server = os.environ.get("COUCHDB_URL", None)
    elif not args.server:
        args.server = None

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s %(message)s",
    )

    await args.func(args)


def entry():
    anyio.run(main)
