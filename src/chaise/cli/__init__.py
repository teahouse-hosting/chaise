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
    for wanted in find_dbs(args.module):
        try:
            livedb = await session.get_db(wanted.name)
        except Missing:
            print(f"Creating {wanted.name}...")  # TODO: Logging
            livedb = await session.create_db(wanted.name)
        else:
            print(f"{wanted.name} exists")

        current_indexes = {(i.ddoc, i.name): i async for i in livedb.iter_indexes()}
        wanted_indexes = {
            (ddoc.name, i.name): i for ddoc in wanted.ddocs for i in ddoc.indexes
        }

        to_make = set(wanted_indexes.keys()) - set(current_indexes.keys())
        for dname, iname in to_make:
            idx = wanted_indexes[dname, iname]
            await livedb.add_index(
                ddoc=dname,
                name=iname,
                fields=idx.fields,
            )
        # TODO: Delete indexes
        # TODO: Update indexes


def _arg_parser():
    async def usage(args):
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
