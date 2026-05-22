import scrapy


class NewsItem(scrapy.Item):
    source = scrapy.Field()
    url = scrapy.Field()
    canonical_url = scrapy.Field()

    title = scrapy.Field()
    teaser = scrapy.Field()

    published_at = scrapy.Field()
    fetched_at = scrapy.Field()

    language = scrapy.Field()
    section = scrapy.Field()

    full_text = scrapy.Field()
    content_hash = scrapy.Field()

    profile = scrapy.Field()
