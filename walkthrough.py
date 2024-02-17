import argparse
from datetime import datetime
from pathlib import Path
import sys
import time
from watchfiles import Change, watch

from src.compose_html import make_html_from_lines
from src.parse_document import parse_document


def main() -> int:
    parser = argparse.ArgumentParser()
    subp = parser.add_subparsers(
        dest="subparser_name",
        help="Your help message",
    )

    compile_p = subp.add_parser("compile", help="Compile walkthrough")
    compile_p.add_argument("infile")
    compile_p.add_argument("-o", "--outfile")
    watch_p = subp.add_parser("watch", help="Compile walkthrough with watching")
    watch_p.add_argument("infile")
    watch_p.add_argument("-o", "--outfile")
    parse_p = subp.add_parser("parse", help="Parse walkthrough")
    parse_p.add_argument("infile")
    args = parser.parse_args()
    match args.subparser_name:
        case "compile":
            infile = Path(args.infile)
            if not infile.exists():
                print(f"Cannot find file {infile}")
                return 1
            if args.outfile is not None:
                outfile = Path(args.outfile)
            else:
                outfile = infile.parent / f"{infile.stem}.html"
            print(f"Compiling {infile} to {outfile}")

            outfile.write_text(make_html_from_lines(infile.read_text()))
            return 0
        case "watch":
            infile = Path(args.infile)
            if not infile.exists():
                print(f"Cannot find file {infile}")
                return 1
            if args.outfile is not None:
                outfile = Path(args.outfile)
            else:
                outfile = infile.parent / f"{infile.stem}.html"
            outfile.write_text(make_html_from_lines(infile.read_text()))
            print(f"Watching {infile}. Press Ctrl+C to stop.")
            try:
                for changes in watch(infile.parent):
                    for change, file in changes:
                        if Path(file) == infile.resolve() and change == Change.modified:
                            print(f"[{datetime.now()}] Recompiling.")
                            outfile.write_text(make_html_from_lines(infile.read_text()))
            except KeyboardInterrupt:
                pass
            return 0
        case "parse":
            infile = Path(args.infile)
            if not infile.exists():
                print(f"Cannot find file {infile}")
                return 1
            parse_document(infile.read_text())
            return 0
        case _:
            parser.print_help()
            return 1


if __name__ == "__main__":
    sys.exit(main())
