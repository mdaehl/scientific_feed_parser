import json
import requests
from misc import config
import re


def get_data(url: str, api_key: str) -> tuple[str, list[str], str]:
    """Get paper information from elsevier based on the provided link."""
    match = re.search("pii/(?P<pii>.*?)&", url)
    pii = match.group("pii")

    path = f"https://api.elsevier.com/content/article/pii/{pii}?apiKey={api_key}"
    headers = {"Accept": "application/json"}

    content = requests.get(path, headers=headers, proxies=config.proxies).content
    content = json.loads(content)
    data = content["full-text-retrieval-response"]["coredata"]

    title = data["dc:title"]
    authors_item = data["dc:creator"]
    authors = list(map(lambda x: x["$"], authors_item))
    abstract = data["dc:description"]
    return title, authors, abstract
