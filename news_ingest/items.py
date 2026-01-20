import scrapy


class NewsItem(scrapy.Item):
    source = scrapy.Field()
    url = scrapy.Field()
    canonical_url = scrapy.Field()

    title = scrapy.Field()
    teaser = scrapy.Field()

    published_at = scrapy.Field()  # ISO string (UTC wenn möglich)
    fetched_at = scrapy.Field()  # ISO string (UTC)

    language = scrapy.Field()
    section = scrapy.Field()  # optional

    full_text = scrapy.Field()  # optional (wenn öffentlich erreichbar)
    content_hash = scrapy.Field()
