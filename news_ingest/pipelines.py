import hashlib
import json
import os
from dateutil import parser as dateparser
from datetime import timezone
from w3lib.url import canonicalize_url
from scrapy.exceptions import DropItem


class NormalizePipeline:
    def process_item(self, item, spider):
        # URL normalisieren
        if item.get("url"):
            item["url"] = canonicalize_url(item["url"])
        if item.get("canonical_url"):
            item["canonical_url"] = canonicalize_url(item["canonical_url"])

        # published_at in ISO + UTC (wenn parsebar)
        pub = item.get("published_at")
        if pub:
            try:
                dt = dateparser.parse(pub)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                item["published_at"] = dt.astimezone(timezone.utc).isoformat()
            except Exception:
                # wenn nicht parsebar, einfach lassen
                pass

        # content hash (für Dedupe)
        text_for_hash = (
            (item.get("title") or "")
            + "\n"
            + (item.get("full_text") or item.get("teaser") or "")
        )
        item["content_hash"] = hashlib.sha256(
            text_for_hash.strip().encode("utf-8")
        ).hexdigest()

        return item


class DedupePipeline:
    """
    Leichte Variante: Dedup nur pro Lauf (in-memory).
    Später persistent machen (DB UNIQUE Index / Redis Set).
    """

    def __init__(self):
        self.seen = set()

    def process_item(self, item, spider):
        key = item.get("canonical_url") or item.get("url") or item.get("content_hash")
        if key in self.seen:
            raise DropItem("duplicate")
        self.seen.add(key)
        return item


class JsonlExportPipeline:
    def open_spider(self, spider):
        os.makedirs("data", exist_ok=True)
        self.first = True
        self.f = open("data/news.json", "w", encoding="utf-8")
        self.f.write("[\n")

    def close_spider(self, spider):
        self.f.write("\n]\n")
        self.f.close()

    def process_item(self, item, spider):
        obj = dict(item)

        # defensive: nie kaputtes JSON schreiben
        for k, v in obj.items():
            if v is None:
                obj[k] = None

        if not self.first:
            self.f.write(",\n")
        self.f.write(json.dumps(obj, ensure_ascii=False))
        self.first = False

        return item
