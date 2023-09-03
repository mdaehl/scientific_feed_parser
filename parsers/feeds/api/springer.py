import requests
import json
from misc import config


def get_data(url: str, main_domain: str, api_key: str) -> tuple[str, list[str], str]:
    """Get paper information from springer (nature) based on the provided link."""
    if main_domain == "nature.com":
        nature_doi_preface = "10.1038"
        doi = url.split("/")[-1]
        url = f"https://api.springernature.com/metadata/json/doi/{nature_doi_preface}/{doi}?api_key={api_key}"
    else:
        doi = "/".join(url.split("/")[-2:])
        url = f"https://api.springernature.com/metadata/json/doi/{doi}?api_key={api_key}"

    content = requests.get(url, proxies=config.proxies).content
    content = json.loads(content)

    title = content["records"][0]["title"]
    abstract = content["records"][0]["abstract"]
    authors = content["records"][0]["creators"]
    authors = list(map(lambda x: x["creator"], authors))

    return title, authors, abstract
