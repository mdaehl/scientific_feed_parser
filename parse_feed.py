import argparse
from parsers.feeds import feed
from misc import generator, config
import os
import yaml
import bs4


def parse_feed(file_path: str, result_file_name: str, append: bool, online: bool) -> None:
    """Execute parse feeding."""
    if not online and not os.path.isfile(file_path):
        raise FileNotFoundError(f"Could not fine the file with path {file_path}")
    else:
        feed_parser = feed.FeedParser(file_path, result_file_name, online, append)
        papers = feed_parser.get_papers()
        generator.create_atom_feed(papers, result_file_name=result_file_name)


def remove_duplicates(targets: list[str]) -> None:
    """Remove duplicates across the given feeds."""
    id_sets = set()
    for target in targets:
        # read out existing ids
        with open(f"{config.result_feed_folder}/{target}", "r", encoding="utf-8") as f:
            text = f.read()
        entries = bs4.BeautifulSoup(text, features="xml").select("entry >id")
        ids = set(map(lambda x: x.text, entries))
        # get duplicates
        duplicates = id_sets.intersection(ids)
        soup = bs4.BeautifulSoup(text, features="xml")
        # update id list
        id_sets = id_sets.union(ids)

        # remove entry if a duplicate is found
        if duplicates:
            for duplicate in duplicates:
                print(duplicate)
                duplicate_entry = soup.find("id", string=duplicate).parent
                duplicate_entry.extract()

            # rewrite the affected files
            with open(f"{config.result_feed_folder}/{target}", "w", encoding="utf-8") as f:
                f.write(soup.text)


def main(args: argparse.Namespace) -> None:
    """Main method to coordinate parse feeding execution."""
    use_config = args.use_config

    if use_config:
        configs = yaml.safe_load(open(config.config_file))["pairings"]
        sources = list(map(lambda x: x.get("source"), configs))
        targets = list(map(lambda x: x.get("target"), configs))
        onlines = list(map(lambda x: x.get("online"), configs))
        appends = list(map(lambda x: x.get("append"), configs))
        for source, target, append, online in zip(sources, targets, appends, onlines):
            parse_feed(source, target, append, online)
        remove_duplicates(targets)
    else:
        file_path = args.source
        result_file_name = args.target
        append = args.append
        online = args.online
        parse_feed(file_path, result_file_name, append, online)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--use_config", "-u", type=bool, default=False,
                            help="Use mapping of feeds from config file.")
    arg_parser.add_argument("--source", "-s", help="Path to xml feeds (source) file.")
    arg_parser.add_argument("--target", "-t", default="feed",
                            help="Name of the result feed file (target) without extension.")
    arg_parser.add_argument("--online", "-o", type=bool, default=False, help="Is the file online stored.")
    arg_parser.add_argument("-a", "--append", type=bool, default=True, help="Append new entries to current feed file")
    input_args = arg_parser.parse_args()
    main(input_args)
