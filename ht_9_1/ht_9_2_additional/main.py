import json
from time import time

import scrapy
from itemadapter import ItemAdapter
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field


class QuoteItem(Item):
    tags = Field()
    author = Field()
    quote = Field()


class AuthorItem(Item):
    full_name = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class DataPipeline:
    quotes: list = []
    authors: list = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'full_name' in adapter.keys():
            self.authors.append({
                'full_name': adapter['full_name'],
                'born_date': adapter['born_date'],
                'born_location': adapter['born_location'],
                'description': adapter['description']
            })
        if 'quote' in adapter.keys():
            self.quotes.append({
                'tags': adapter['tags'],
                'author': adapter['author'],
                'quote': adapter['quote']
            })
        return item

    def close_spider(self, spider):
        with open("authors+.json", "w", encoding="utf-8") as fw:
            json.dump(self.authors, fw, ensure_ascii=False, indent=4)
        with open("quotes+.json", "w", encoding="utf-8") as fw:
            json.dump(self.quotes, fw, ensure_ascii=False, indent=4)


class QuotesSpider(scrapy.Spider):
    name: str = "authors"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["http://quotes.toscrape.com/"]
    custom_settings = {'ITEM_PIPELINES': {DataPipeline: 300}}

    def parse(self, response, *_):
        for quote in response.xpath("/html//div[@class='quote']"):
            tags = quote.xpath("div[@class='tags']/a/text()").extract()
            author = quote.xpath("span/small/text()").extract()
            q = quote.xpath("span[@class='text']/text()").get().strip()
            yield QuoteItem(tags=tags, author=author, quote=q)
            yield response.follow(url=self.start_urls[0] + quote.xpath('span/a/@href').get(),
                                  callback=self.nested_parse_author)

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    def nested_parse_author(self, response, *_):
        author = response.xpath('/html//div[@class="author-details"]')
        full_name = author.xpath('h3[@class="author-title"]/text()').get().strip()
        born_date = author.xpath('p/span[@class="author-born-date"]/text()').get().strip()
        born_location = author.xpath('p/span[@class="author-born-location"]/text()').get().strip()
        description = author.xpath('div[@class="author-description"]/text()').get().strip()
        yield AuthorItem(full_name=full_name, born_date=born_date, born_location=born_location, description=description)


def main():
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()


if __name__ == '__main__':
    start = time()
    main()
    print(time() - start)
