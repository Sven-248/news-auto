import scrapy
import feedparser
from datetime import datetime, timezone

from news_ingest.items import NewsItem
from news_ingest.sources import SOURCES


class RssSpider(scrapy.Spider):
    name = "rss"

    def __init__(self, source=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.only_source = source  # optional: nur eine Quelle crawlen

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

    def parse_rss(self, response):
        feed = feedparser.parse(response.text)

        for entry in getattr(feed, "entries", []):
            url = getattr(entry, "link", None)
            if not url:
                continue

            # section aus feed url ableiten
            rss_url = response.meta.get("rss_url") or ""
            section = rss_url.rsplit("/", 1)[-1].replace(".rss", "").strip() or None

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

            # Leichter Weg: Volltext zu holen – wenn paywalled/blocked => full_text bleibt ggf. kurz/leer.
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

        # sehr einfache Extraktion: <article> <p>
        paragraphs = response.xpath("//article//p//text()").getall()
        text = " ".join([p.strip() for p in paragraphs if p and p.strip()])

        # fallback, falls article-tag fehlt: alle p-tags
        if not text:
            paragraphs = response.xpath("//p//text()").getall()
            text = " ".join([p.strip() for p in paragraphs if p and p.strip()])

        item["full_text"] = text or None
        yield item

    @staticmethod
    def _best_summary(entry):
        # feedparser: summary oder content:encoded
        summary = getattr(entry, "summary", None)
        if summary:
            return summary

        content = getattr(entry, "content", None)
        if content and isinstance(content, list) and len(content) > 0:
            value = content[0].get("value")
            return value

        return None
