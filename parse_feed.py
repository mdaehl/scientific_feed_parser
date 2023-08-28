import argparse
from parsers.feeds import feed
from misc import generator
import os


def main(args: argparse.Namespace) -> None:
    file_path = args.file

    if os.path.isfile(file_path):
        feed_parser = feed.FeedParser(file_path)
        papers = feed_parser.get_papers()
        generator.create_atom_feed(papers)
    else:
        raise FileNotFoundError(f"Could not fine the file with path {file_path}")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--file", "-f", help="Path to xml feeds file.")
    input_args = arg_parser.parse_args()
    main(input_args)
