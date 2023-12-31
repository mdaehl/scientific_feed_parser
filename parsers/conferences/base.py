from misc import utils


class Parser:
    """Base Parser, which is used to parse conferences."""
    def __init__(self, conference: str, year: int) -> None:
        self.conference = conference
        utils.check_year(year)
        self.year = year
        self.links = None
        self.base_url = utils.base_urls[self.conference]
        self.papers = []

    def get_paper_links(self, containers) -> list[str]:
        """Retrieve links from containers."""
        print("Getting paper links.")
        links = list(map(utils.get_link, containers))
        if len(links) == 0:
            raise Warning(f"No papers found at the conference {self.conference} in {self.year}")
        else:
            return links
