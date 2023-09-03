import argparse
from parsers.feeds import feed
from misc import generator
import os


def main(args: argparse.Namespace) -> None:
    """Main method to execute parse feeding."""
    file_path = args.file
    result_file_name = args.filename
    append = args.file

    if os.path.isfile(file_path):
        feed_parser = feed.FeedParser(file_path, result_file_name, append)
        papers = feed_parser.get_papers()
        generator.create_atom_feed(papers)
    else:
        raise FileNotFoundError(f"Could not fine the file with path {file_path}")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--file", "-f", help="Path to xml feeds file.")
    arg_parser.add_argument("--filename", "-n", default="feed", help="Name of the result feed file without extension.")
    arg_parser.add_argument("-a", "--append", type=bool, default=True, help="Append new entries to current feed file")
    input_args = arg_parser.parse_args()
    main(input_args)
