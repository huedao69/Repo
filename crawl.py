import os, json, time, hashlib, logging, re
from typing import List, Dict
import requests, feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

DATA_RAW = "data/raw"

def _slug(url:str)->str:
    import hashlib
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def save_raw(url:str, content:str, meta:dict):
    Path(DATA_RAW).mkdir(parents=True, exist_ok=True)
    path = os.path.join(DATA_RAW, f"{_slug(url)}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"url": url, "content": content, "meta": meta, "fetched_at": time.time()}, f, ensure_ascii=False, indent=2)
    return path

def fetch_url(url:str)->str:
    headers = {"User-Agent": "ACS-Safe/1.0 (+contact@example.com)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def crawl_rss(feed_url:str)->List[str]:
    logging.info(f"Crawl RSS: {feed_url}")
    out = []
    feed = feedparser.parse(feed_url)
    for e in feed.entries[:25]:
        url = e.link
        try:
            html = fetch_url(url)
            out.append(save_raw(url, html, {"title": e.get("title"), "published": str(e.get("published"))}))
        except Exception as ex:
            logging.warning(f"Skip {url}: {ex}")
    return out

def parse_sitemap(xml:str)->List[str]:
    return re.findall(r"<loc>(.*?)</loc>", xml)

def crawl_sitemap(url:str, limit:int=60)->List[str]:
    logging.info(f"Crawl sitemap: {url}")
    out = []
    try:
        xml = fetch_url(url)
        urls = parse_sitemap(xml)[:limit]
        for u in urls:
            try:
                html = fetch_url(u)
                out.append(save_raw(u, html, {}))
            except Exception as ex:
                logging.warning(f"Skip {u}: {ex}")
    except Exception as ex:
        logging.warning(f"Sitemap skip {url}: {ex}")
    return out

def crawl_list_page(base_url:str, selector:str, limit:int=15)->List[str]:
    logging.info(f"Crawl list-page: {base_url} sel='{selector}'")
    out = []
    try:
        html = fetch_url(base_url)
        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.select(selector):
            href = a.get("href")
            if not href: continue
            abs_url = urljoin(base_url, href)
            if abs_url not in links:
                links.append(abs_url)
        for u in links[:limit]:
            try:
                article_html = fetch_url(u)
                out.append(save_raw(u, article_html, {}))
            except Exception as ex:
                logging.warning(f"Skip {u}: {ex}")
    except Exception as ex:
        logging.warning(f"List-page skip {base_url}: {ex}")
    return out

def crawl_pages(urls:List[str])->List[str]:
    out = []
    for u in urls:
        try:
            html = fetch_url(u)
            out.append(save_raw(u, html, {}))
        except Exception as ex:
            logging.warning(f"Skip {u}: {ex}")
    return out

def crawl_all()->List[str]:
    import yaml, pathlib
    cfg_path = pathlib.Path(__file__).with_name("sources.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    raw = []
    for feed in cfg.get("rss", []):
        raw += crawl_rss(feed)
    for sm in cfg.get("sitemaps", []):
        if isinstance(sm, dict):
            raw += crawl_sitemap(sm.get("url"), int(sm.get("limit", 60)))
        else:
            raw += crawl_sitemap(sm, 60)
    for lp in cfg.get("list_pages", []):
        raw += crawl_list_page(lp["url"], lp["link_selector"], int(lp.get("limit", 15)))
    raw += crawl_pages(cfg.get("pages", []))
    logging.info(f"Crawl done: {len(raw)} docs")
    return raw
