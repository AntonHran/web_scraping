import json
from time import time

import requests
from bs4 import BeautifulSoup, Tag


base_url: str = "https://quotes.toscrape.com"


def recur_pages_getter(url: str, pages=None) -> list:
    if pages is None:
        pages: list = []
    pages.append(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    page = soup.select("nav ul[class=pager] li[class=next] a")
    if page:
        return recur_pages_getter(base_url + page[0]["href"], pages=pages)
    return pages


def get_quotes_data(urls: list) -> list:
    quotes_: list = []
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select("div[class=quote]")
        for el in content:
            result: dict = {}
            quote: Tag = el.find("span", class_="text")
            author: Tag = el.find("small", class_="author")
            tags: list[Tag] = el.find("div", class_="tags").find_all("a", class_="tag")
            tags_: list[str] = [tag.text for tag in tags]
            result.update({"tags": tags_, "author": author.text, "quote": quote.text})
            quotes_.append(result)
    return quotes_


def get_links(urls: list) -> list:
    authors_links: list = []
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select("div[class=quote]")
        for el in content:
            about_author: str = el.find("a")["href"]
            if about_author not in authors_links:
                authors_links.append(about_author)
    return authors_links


def get_authors_data(author_urls: list):
    urls: list = [base_url + author_url for author_url in author_urls]
    authors_: list = []
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.select("div[class=author-details]")
        result: dict = {}
        for el in content:
            author: Tag = el.find("h3", class_="author-title")
            born_date: Tag = el.find("span", class_="author-born-date")
            born_location: Tag = el.find("span", class_="author-born-location")
            description: str = el.find("div", class_="author-description").text
            description: str = description.split(".More:")[0].replace("\n", "").strip()
            result.update(
                {
                    "full_name": author.text,
                    "born_date": born_date.text,
                    "born_location": born_location.text,
                    "description": description,
                }
            )
        authors_.append(result)
    return authors_


def write_json(data: list | dict, name: str) -> None:
    with open(name + ".json", "w", encoding="utf-8") as fw:
        json.dump(data, fw, ensure_ascii=False, indent=4)


def main() -> None:
    start = time()
    site_pages: list = recur_pages_getter(base_url)
    quotes: list = get_quotes_data(site_pages)
    print(time() - start)
    start = time()
    a_links: list = get_links(site_pages)
    print(time() - start)
    start = time()
    authors: list = get_authors_data(a_links)
    print(time() - start)
    start = time()
    write_json(quotes, "quotes")
    write_json(authors, "authors")
    print(time() - start)


if __name__ == "__main__":
    main()
