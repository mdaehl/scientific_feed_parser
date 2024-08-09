import argparse
from misc import config
import yaml
from parsers.feeds import feed


def main(args: argparse.Namespace) -> None:
    """Main method to coordinate parse feeding execution."""
    use_config = args.use_config
    remove_duplicates = args.remove_duplicates

    if use_config:
        configs = yaml.safe_load(open(config.config_file)).get("pairings")
        if configs:
            sources = list(map(lambda x: x.get("source"), configs))
            targets = list(map(lambda x: x.get("target"), configs))
            onlines = list(map(lambda x: x.get("online"), configs))
            appendings = list(map(lambda x: x.get("append"), configs))
        else:
            raise Warning("No pairings found in the config file.")
    else:
        sources = list(args.source)
        targets = list(args.target)
        onlines = list(args.online)
        appendings = list(args.append)

    feed_list = feed.FeedList(sources, targets, onlines, appendings)
    feed_list.build_feeds()
    if remove_duplicates:
        feed_list.remove_duplicates()
    feed_list.refine_feeds()
    feed_list.save_feeds()
    feed_list.print_update_stats()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--use_config", "-u", type=bool, default=False,
                            help="Use mapping of feeds from config file.")
    arg_parser.add_argument("--source", "-s", help="Path to xml feeds (source) file.")
    arg_parser.add_argument("--target", "-t", default="feed",
                            help="Name of the result feed file (target) without extension.")
    arg_parser.add_argument("--online", "-o", type=bool, default=False, help="Is the file online stored.")
    arg_parser.add_argument("-a", "--append", type=bool, default=True,
                            help="Append new entries to current feed file")
    arg_parser.add_argument("--remove_duplicates", "-r", type=bool, default=True,
                            help="Remove duplicates across feed list.")
    input_args = arg_parser.parse_args()
    main(input_args)
