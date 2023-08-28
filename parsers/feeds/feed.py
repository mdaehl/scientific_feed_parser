import bs4
import re
from urllib.parse import urlparse
from misc.utils import Paper
from parsers.feeds.api import arxiv, springer, elsevier
import yaml
from misc import config
from tqdm import tqdm


class FeedParser:
    def __init__(self, file_path):
        self.file_path = file_path

        config_params = yaml.safe_load(open(config.config_file))
        self.springer_key = config_params.get("springer_api_key")
        self.elsevier_key = config_params.get("elsevier_api_key")

        self.soup_content = self.load_content()

        self.papers = []
        self.current_paper = None

    def load_content(self):
        with open(self.file_path, "r") as file:
            content = file.read()
        return bs4.BeautifulSoup(content, "xml")

    def get_papers(self):
        # TODO compare with old feeds
        print("Getting data from entries.")
        entries = self.soup_content.find_all("entry")
        for entry in tqdm(entries):
            content = entry.find("content")
            soup = bs4.BeautifulSoup(content.text, "html.parser")

            paper_entries = soup.find_all("a", {"class": "gse_alrt_title"})
            authors_str = soup.find_all("div", attrs={"style": "color:#006621;line-height:18px"})
            all_authors = list(map(lambda x: x.text.split("-")[0].strip().split(","), authors_str))

            for paper_entry, authors in zip(paper_entries, all_authors):
                title = paper_entry.text
                abstract = ""

                url_str = paper_entry["href"]
                match = re.search("url=(?P<url>.*?)&", url_str)
                url = match.group("url")

                self.current_paper = Paper(title, authors, abstract, url)
                self.refine_current_paper_info()
                self.papers.append(self.current_paper)

        return self.papers

    def refine_current_paper_info(self):
        url = self.current_paper.link
        domain = urlparse(url).netloc
        main_domain = ".".join(domain.split(".")[-2:])

        if main_domain == "arxiv.org":
            title, authors, abstract = arxiv.get_data(url)
            self.update_paper_entry(title, authors, abstract)
        elif main_domain in ["springer.com", "nature.com"]:
            api_key = yaml.safe_load(open(config.config_file))["springer_api_key"]
            if api_key:
                title, authors, abstract = springer.get_data(url, main_domain, api_key)
                self.update_paper_entry(title, authors, abstract)
        elif main_domain == "sciencedirect.com":
            api_key = yaml.safe_load(open(config.config_file))["elsevier_api_key"]
            if api_key:
                title, authors, abstract = elsevier.get_data(url, api_key)
                self.update_paper_entry(title, authors, abstract)
        # TODO add ieee (10 calls per sec + 200 calls per day)

    def update_paper_entry(self, title, authors, abstract):
        url = self.current_paper.link
        self.current_paper = Paper(title, authors, abstract, url)
