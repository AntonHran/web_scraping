import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import time

import requests
from bs4 import BeautifulSoup


base_url: str = 'https://quotes.toscrape.com'


def recur_pages_getter(url: str, pages=None):
    if pages is None:
        pages = []
    pages.append(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    page = soup.select("nav ul[class=pager] li[class=next] a")
    if page:
        return recur_pages_getter(base_url + page[0]['href'], pages=pages)
    return pages


def get_quote(url: str) -> list:
    quotes_ = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select("div[class=quote]")
    for el in content:
        dct = {}
        quote = el.find("span", class_="text")
        author = el.find("small", class_="author")
        tags = el.find("div", class_="tags").find_all("a", class_="tag")
        tags_ = [tag.text for tag in tags]
        dct.update({"tags": tags_, "author": author.text, "quote": quote.text})
        quotes_.append(dct)
    return quotes_


def get_authors_links(url) -> list:
    authors_links = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select("div[class=quote]")
    for el in content:
        about_author = el.find("a")["href"]
        authors_links.append(about_author)
    return authors_links


def get_author(url) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select("div[class=author-details]")
    dct = {}
    for el in content:
        author = el.find("h3", class_="author-title")
        born_date = el.find("span", class_="author-born-date")
        born_location = el.find("span", class_="author-born-location")
        description = el.find("div", class_="author-description")
        description = description.text.split(".More:")[0].replace("\n", "").strip()
        dct.update(
            {
                "full_name": author.text,
                "born_date": born_date.text,
                "born_location": born_location.text,
                "description": description,
            }
        )
    return dct


async def get_data_async(urls, func):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        futures = [loop.run_in_executor(pool, func, url) for url in urls]
        result = await asyncio.gather(*futures, return_exceptions=True)
        return result


async def write_json(data: list | dict | tuple, name: str) -> None:
    with open(name+'.json', 'w', encoding='utf-8') as fw:
        json.dump(data, fw, ensure_ascii=False, indent=4)


def find_origin(links: list) -> list:
    res = []
    for link in links:
        if link not in res:
            res.append(link)
    return res


def write(data: list | tuple) -> list:
    res = []
    for el in data:
        for inner_el in el:
            res.append(inner_el)
    return res


async def main_() -> None:
    start = time()
    site_pages: list = recur_pages_getter(base_url)
    quotes = write(await get_data_async(site_pages, get_quote))
    print(time() - start)
    start = time()
    a_links = write(await get_data_async(site_pages, get_authors_links))
    a_links = find_origin(a_links)
    print(time() - start)
    start = time()
    a_l = [base_url + author_l for author_l in a_links]
    authors = await get_data_async(a_l, get_author)
    print(time() - start)
    start = time()
    await write_json(quotes, "async_thread_quotes")
    await write_json(authors, 'async_thread_authors')
    print(time() - start)


if __name__ == '__main__':
    asyncio.run(main_())
