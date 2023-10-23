import argparse
from misc import generator
from parsers.conferences import icml, cvf, nips, ecva


def main(args: argparse.Namespace) -> None:
    """Main method to execute conference feeding."""
    conference = args.conference
    year = args.year

    if conference in ["CVPR", "WACV", "ICCV"]:
        paper_parser = cvf.CVFParser(conference, year)
    elif conference == "ECCV":
        paper_parser = ecva.ECVAParser(conference, year)
    elif conference == "ICML":
        paper_parser = icml.ICMLParser(conference, year)
    elif conference == "NIPS":
        paper_parser = nips.NIPSParser(conference, year)
    else:
        raise ValueError(f"Conference '{conference}' is not or not yet supported.")

    papers = paper_parser.get_papers()
    print("Generate and save atom feeds.")
    generator.create_atom_feed(papers, conference=conference, year=year)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--conference", "-c",
                            help="Supported conferences are: 'CVPR', 'WACV', 'ICCV', 'ECCV' and 'ICML'.")
    arg_parser.add_argument("--year", "-y", type=int, help="Year of the conference.")
    input_args = arg_parser.parse_args()
    main(input_args)
