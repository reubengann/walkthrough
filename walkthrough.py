import argparse
from datetime import datetime
from pathlib import Path
import sys
from zipfile import ZipFile
from watchfiles import Change, watch

from src.parse_document import parse_document
from src.compose_html import make_html_from_doc


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
    build_p = subp.add_parser(
        "build", help="Build and package walkthrough for distribution"
    )
    build_p.add_argument("infile")
    build_p.add_argument("-o", "--outfile")
    init_p = subp.add_parser("init", help="start a new walkthrough")
    init_p.add_argument(
        "game_name",
        help="Short name to call the game (no spaces or special characters)",
    )
    init_p.add_argument("outfolder")
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
            doc = parse_document(infile.read_text(encoding="utf-8"))
            outfile.write_text(make_html_from_doc(doc))
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
            doc = parse_document(infile.read_text(encoding="utf-8"))
            outfile.write_text(make_html_from_doc(doc))
            print(f"Watching {infile}. Press Ctrl+C to stop.")
            try:
                for changes in watch(infile.parent):
                    for change, file in changes:
                        if (
                            Path(file).resolve() == infile.resolve()
                            and change == Change.modified
                        ):
                            print(f"[{datetime.now()}] Recompiling.")
                            doc = parse_document(infile.read_text(encoding="utf-8"))
                            outfile.write_text(make_html_from_doc(doc))
            except KeyboardInterrupt:
                pass
            return 0
        case "build":
            infile = Path(args.infile)
            if not infile.exists():
                print(f"Cannot find file {infile}")
                return 1
            if args.outfile is not None:
                outfile_html = Path(args.outfile)
            else:
                outfile_html = infile.parent / f"{infile.stem}.html"
            preexisting = outfile_html.exists()
            if args.outfile is not None:
                outfile_zip = Path(args.outfile)
            else:
                outfile_zip = infile.parent / f"{infile.stem}.zip"
            print(f"Compiling {infile} to {outfile_zip}")
            doc = parse_document(infile.read_text(encoding="utf-8"))
            for img in doc.images:
                if not (infile.parent / img).exists():
                    print(f"Referenced image {infile.parent / img} does not exist")
                    return 1
            outfile_html.write_text(make_html_from_doc(doc))
            with ZipFile(outfile_zip, "w") as zfile:
                zfile.write(outfile_html, outfile_html.name)
                for img in doc.images:
                    if (infile.parent / img).exists():
                        zfile.write(infile.parent / img, img)
                    else:
                        print(f"Referenced image {infile.parent / img} does not exist")
                        return 1
            if not preexisting:
                outfile_html.unlink()
            return 0
        case "init":
            game_name: str = args.game_name
            outfolder: str = args.outfolder
            outpath = Path(outfolder) / f"{game_name}.txt"
            if outpath.exists():
                print(f"file {outpath} already exists!")
                return 1
            lines = [
                f"\\game_short_name{{{game_name}}} ",
                "\\version{1}",
                "\\declare{collectible_short_name}{Collectible Long Name}{Collectible Plural}"
                "\\title{Your Game's name}\n",
                "\\section{Introduction}\n" "Some introduction to the game\n",
                "\\section{Level 1}\n",
                "Walk straight ahead and collect the [collectible_short_name|Cool collectible].\n",
            ]
            outpath.write_text("\n".join(lines))
            return 0
        case _:
            parser.print_help()
            return 1


if __name__ == "__main__":
    sys.exit(main())
