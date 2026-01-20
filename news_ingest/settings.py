BOT_NAME = "news_ingest"

SPIDER_MODULES = ["news_ingest.spiders"]
NEWSPIDER_MODULE = "news_ingest.spiders"

ROBOTSTXT_OBEY = True

# Polite Crawling
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0

RETRY_TIMES = 3
COOKIES_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en;q=0.8",
}

# HTTP Cache spart Traffic und reduziert Block-Risiko
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_IGNORE_HTTP_CODES = [301, 302, 303, 307, 308]

ITEM_PIPELINES = {
    "news_ingest.pipelines.NormalizePipeline": 200,
    "news_ingest.pipelines.DedupePipeline": 300,
    "news_ingest.pipelines.JsonlExportPipeline": 900,
}

LOG_LEVEL = "INFO"
