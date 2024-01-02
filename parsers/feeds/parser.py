import bs4
from urllib.parse import urlparse
import requests
from misc.utils import Paper
from urllib import parse
import yaml
from misc import config, utils
from tqdm import tqdm
import os


class FeedParser:
    """Parser that retrieves the information from the provided feeds and their corresponding papers. The paper
    information refers solely to the information that is stored within the feed file."""
    def __init__(self, file_path: str, filename: str, online: bool, appending: bool) -> None:
        self.file_path = file_path
        self.appending = appending
        self.online = online
        self.existing_papers = {}
        self.feed_file_path = f"{config.result_feed_folder}/{filename}"

        config_params = yaml.safe_load(open(config.config_file))
        self.springer_key = config_params.get("springer_api_key")
        self.elsevier_key = config_params.get("elsevier_api_key")

        self.soup_content = self.load_content()

        self.papers = []
        self.current_paper = None

    def load_content(self) -> bs4.BeautifulSoup:
        """Load the existing xml file of Google Scholar alert."""
        if self.online:
            try:
                content = requests.get(self.file_path, proxies=config.proxies, verify=config.verify_ssl).content.decode("utf-8")
            except requests.exceptions.InvalidSchema:
                raise ValueError(f"{self.file_path} is no valid URL.")
        else:
            with open(self.file_path, "r", encoding="utf-8") as file:
                content = file.read()
        return bs4.BeautifulSoup(content, features="xml")

    def load_existing_items(self) -> None:
        """Load the existing entries of the provided atom feed file."""
        print("Getting already existing items.")
        if os.path.isfile(self.feed_file_path):
            with open(self.feed_file_path, "r", encoding="utf-8") as file:
                content = file.read()
            soup = bs4.BeautifulSoup(content, features="xml")
            titles, all_authors, abstracts, links = utils.decode_xml_soup(soup)
            self.existing_papers = {link: Paper(title, authors, abstract, link, parsed=True) for
                                    title, authors, abstract, link in zip(titles, all_authors, abstracts, links)}

    def get_papers(self) -> list[Paper]:
        """Retrieve the data of all papers found in the xml file."""
        if self.appending:
            self.load_existing_items()

        print("Getting data from entries.")
        entries = self.soup_content.find_all("entry")
        already_parsed_papers = set()
        for entry in tqdm(entries):
            content = entry.find("content")
            soup = bs4.BeautifulSoup(content.text, "html.parser")

            paper_entries = soup.find_all("a", {"class": "gse_alrt_title"})
            authors_str = soup.find_all("div", attrs={"style": "color:#006621;line-height:18px"})
            all_authors = list(map(lambda x: x.text.split("-")[0].strip().split(","), authors_str))

            for paper_entry, authors in zip(paper_entries, all_authors):
                gs_url = paper_entry["href"]

                # convert Google Scholar url to general url. Sometimes the paper url is not available, then skip it
                try:
                    url = parse.parse_qs(parse.urlparse(gs_url).query)["url"][0]
                except KeyError:
                    continue

                domain = urlparse(url).netloc
                core_domain = ".".join(domain.split(".")[-2:])

                if url in self.existing_papers:  # check if already exists in old file
                    paper = self.existing_papers[url]
                    paper.domain = core_domain
                    self.papers.append(paper)

                elif url in already_parsed_papers:  # check if already parsed
                    continue
                else:
                    title = paper_entry.text
                    abstract = ""

                    self.current_paper = Paper(title, authors, abstract, url, core_domain)
                    self.papers.append(self.current_paper)
                    already_parsed_papers.add(url)

        return self.papers
