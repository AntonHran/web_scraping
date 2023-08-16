import json
import asyncio
from time import time
import platform
from typing import Callable, Any, Coroutine

import aiohttp
from bs4 import BeautifulSoup, Tag


base_url: str = 'https://quotes.toscrape.com'


async def recur_pages_getter(url: str, pages=None):
    if pages is None:
        pages: list = []
    pages.append(url)
    async with aiohttp.ClientSession() as ses:
        async with ses.get(url) as resp:
            response = await resp.text()
            soup = BeautifulSoup(response, "html.parser")
            page = soup.select("nav ul[class=pager] li[class=next] a")
            if page:
                return await recur_pages_getter(base_url + page[0]['href'], pages=pages)
    return pages


async def get_data(url: str, func: Callable) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                if resp.status == 200:
                    return await func(resp)
            except aiohttp.ClientConnectorError as err:
                print(f'Error status: {resp.status} for {url}. Connection error: {url}', str(err))


async def get_quote(resp: Any) -> list:
    quotes_: list = []
    response = await resp.text()
    soup = BeautifulSoup(response, "html.parser")
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


async def get_links(resp: Any) -> list:
    authors_links: list = []
    response = await resp.text()
    soup = BeautifulSoup(response, "html.parser")
    content = soup.select('div[class=quote]')
    for el in content:
        about_author: str = el.find('a')['href']
        if about_author not in authors_links:
            authors_links.append(about_author)
    return authors_links


async def get_author(resp: Any) -> dict:
    response = await resp.text()
    soup = BeautifulSoup(response, "html.parser")
    content = soup.select("div[class=author-details]")
    result: dict = {}
    for el in content:
        author: Tag = el.find("h3", class_="author-title")
        born_date: Tag = el.find("span", class_="author-born-date")
        born_location: Tag = el.find("span", class_="author-born-location")
        description: str = el.find("div", class_="author-description").text
        description: str = description.split("http")[0].replace('.More:', '').strip('\n').strip()
        result.update(
            {
                "full_name": author.text,
                "born_date": born_date.text,
                "born_location": born_location.text,
                "description": description,
            }
        )
    return result


def find_origin(links: list | tuple) -> list:
    res: list = []
    for link in links:
        if link not in res:
            res.append(link)
    return res


async def write_json(data, name: str) -> None:
    with open(name+'.json', 'w', encoding='utf-8') as fw:
        json.dump(data, fw, ensure_ascii=False, indent=4)


async def main_() -> None:
    start = time()
    site_pages: list = await recur_pages_getter(base_url)
    tasks: list[Coroutine] = [get_data(site_page, get_quote) for site_page in site_pages]
    quotes = await asyncio.gather(*tasks)
    quotes = [inner_q for quote_list in quotes for inner_q in quote_list]
    print(time() - start)
    start = time()
    tasks_: list[Coroutine] = [get_data(site_page, get_links) for site_page in site_pages]
    a_links = await asyncio.gather(*tasks_)
    a_links = find_origin([base_url + author_link for a_l in a_links for author_link in a_l])
    print(time() - start)
    start = time()
    tasks_1: list[Coroutine] = [get_data(a_link, get_author) for a_link in a_links]
    authors = await asyncio.gather(*tasks_1)
    print(time() - start)
    start = time()
    await write_json(quotes, "async_quotes")
    await write_json(authors, 'async_authors')
    print(time() - start)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main_())
