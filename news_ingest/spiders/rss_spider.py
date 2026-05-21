import scrapy
import feedparser
from datetime import datetime, timezone

from news_ingest.items import NewsItem
from news_ingest.sources import SOURCES


class RssSpider(scrapy.Spider):
    name = "rss"

    def __init__(self, source=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.only_source = source  # optional: crawl only a single source

    def start_requests(self):
        for source, cfg in SOURCES.items():
            if self.only_source and source != self.only_source:
                continue

            for rss_url in cfg.get("rss", []):
                yield scrapy.Request(
                    rss_url,
                    callback=self.parse_rss,
                    meta={
                        "source": source,
                        "language": cfg.get("language"),
                        "rss_url": rss_url,
                    },
                )

    def infer_section_from_rss_url(self, rss_url: str) -> str | None:
        url = rss_url.lower()

        if "politik" in url or "inland" in url or "ausland" in url:
            return "politik"
        if "wirtschaft" in url:
            return "wirtschaft"
        if "gesellschaft" in url:
            return "gesellschaft"
        if "wissen" in url:
            return "wissen"
        if "technologie" in url or "tech" in url or "it" in url:
            return "technologie"
        if "nachrichten" in url or "index" in url:
            return "nachrichten"

        return None

    def parse_rss(self, response):
        feed = feedparser.parse(response.text)

        for entry in getattr(feed, "entries", []):
            url = getattr(entry, "link", None)
            if not url:
                continue

            # derive section from the feed URL
            rss_url = response.meta.get("rss_url") or ""
            section = self.infer_section_from_rss_url(rss_url)

            item = NewsItem(
                source=response.meta["source"],
                url=url,
                title=getattr(entry, "title", None),
                teaser=self._best_summary(entry),
                published_at=getattr(entry, "published", None)
                or getattr(entry, "updated", None),
                fetched_at=datetime.now(timezone.utc).isoformat(),
                language=response.meta.get("language"),
                section=section,
            )

            # easy way: fetch full text — if paywalled/blocked => full_text may remain short/empty
            yield scrapy.Request(
                url,
                callback=self.parse_article,
                meta={"item": item},
                dont_filter=True,
            )

    def parse_article(self, response):
        item = response.meta["item"]

        # canonical
        item["canonical_url"] = response.xpath("//link[@rel='canonical']/@href").get()

        # easy extraction: <article> <p>
        paragraphs = response.xpath("//article//p//text()").getall()
        text = " ".join([p.strip() for p in paragraphs if p and p.strip()])

        # fallback, if article-tag missing: all p-tags
        if not text:
            paragraphs = response.xpath("//p//text()").getall()
            text = " ".join([p.strip() for p in paragraphs if p and p.strip()])

        item["full_text"] = text or None
        yield item

    @staticmethod
    def _best_summary(entry):
        # feedparser: summary or content:encoded
        summary = getattr(entry, "summary", None)
        if summary:
            return summary

        content = getattr(entry, "content", None)
        if content and isinstance(content, list) and len(content) > 0:
            value = content[0].get("value")
            return value

        return None
