from fake_useragent import UserAgent
import requests
from misc import config
import bs4
import re


def get_ieee_url(url: str) -> str:
    """The url style differs if the document is freely available, because in this case the link in the Google Scholar
    notification directly points to the pdf instead of the landing page."""
    if "abstract" in url:
        # not free
        doc_id = url.split('/')[-2]
    else:
        # free
        match = re.search(r"/(?P<id>\d*)\.pdf", url)
        doc_id = match.group("id")

    ieee_url = f"https://ieeexplore.ieee.org/abstract/document/{doc_id}"
    return ieee_url


def get_data(url: str) -> tuple[str, list[str], str]:
    """Get paper information from elsevier based on the provided link. Currently, still based on webscraping instead of
    the API."""
    # TODO add API support for more robustness keep in mind 10 calls per sec + 200 calls per day
    user_agent = UserAgent()
    headers = {"User-Agent": user_agent.firefox}

    ieee_url = get_ieee_url(url)
    content = requests.get(ieee_url, proxies=config.proxies, headers=headers).content.decode("utf-8")
    soup = bs4.BeautifulSoup(content, features="lxml")

    abstract = soup.find("meta", property="og:description")["content"]
    title = soup.find("meta", property="og:title")["content"]
    authors = soup.find("meta", attrs={"name": "parsely-author"})["content"]
    authors = authors.split(";")
    return title, authors, abstract
