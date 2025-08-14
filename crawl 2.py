import os, json, time, hashlib, logging, re
from typing import List, Dict
import requests, feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from pathlib import Path

DATA_RAW = "/data/raw"

def _slug(url:str)->str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def save_raw(url:str, content:str, meta:dict):
    Path(DATA_RAW).mkdir(parents=True, exist_ok=True)
    slug = _slug(url)
    path = os.path.join(DATA_RAW, f"{slug}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"url": url, "content": content, "meta": meta, "fetched_at": time.time()}, f, ensure_ascii=False, indent=2)
    return path

def fetch_url(url:str)->str:
    headers = {"User-Agent": "ACSBot/1.1 (+contact@example.com)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def crawl_rss(feed_url:str)->List[str]:
    logging.info(f"Crawling RSS: {feed_url}")
    out = []
    feed = feedparser.parse(feed_url)
    for e in feed.entries[:30]:
        url = e.link
        try:
            html = fetch_url(url)
            out.append(save_raw(url, html, {"title": e.get("title"), "published": str(e.get("published"))}))
        except Exception as ex:
            logging.warning(f"Skip {url}: {ex}")
    return out

def parse_sitemap(xml:str)->List[str]:
    urls = re.findall(r"<loc>(.*?)</loc>", xml)
    # quick filter to likely articles
    return [u for u in urls if len(u) < 300 and u.startswith("http")]

def crawl_sitemap(url:str, limit:int=50)->List[str]:
    logging.info(f"Crawling sitemap: {url}")
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

def crawl_list_page(base_url:str, link_selector:str, limit:int=15)->List[str]:
    logging.info(f"Crawling list page: {base_url} sel='{link_selector}'")
    out = []
    try:
        html = fetch_url(base_url)
        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.select(link_selector):
            href = a.get("href")
            if not href: 
                continue
            abs_url = urljoin(base_url, href)
            links.append(abs_url)
        # de-dup and trim
        seen = set()
        links2 = []
        for u in links:
            if u not in seen:
                seen.add(u)
                links2.append(u)
        for u in links2[:limit]:
            try:
                article_html = fetch_url(u)
                # try to extract title
                title = None
                t = soup.title.string if soup.title else None
                meta = {"title": title} if title else {}
                out.append(save_raw(u, article_html, meta))
            except Exception as ex:
                logging.warning(f"Skip {u}: {ex}")
    except Exception as ex:
        logging.warning(f"List-page skip {base_url}: {ex}")
    return out

def crawl_pages(urls:List[str])->List[str]:
    out = []
    for url in urls:
        try:
            html = fetch_url(url)
            out.append(save_raw(url, html, {}))
        except Exception as ex:
            logging.warning(f"Skip {url}: {ex}")
    return out

def crawl_all()->List[str]:
    import yaml, pathlib
    cfg_path = pathlib.Path(__file__).with_name("sources.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    raw_paths = []
    for feed in cfg.get("rss", []):
        raw_paths += crawl_rss(feed)
    for sm in cfg.get("sitemaps", []):
        if isinstance(sm, dict):
            raw_paths += crawl_sitemap(sm.get("url"), limit=int(sm.get("limit", 50)))
        else:
            raw_paths += crawl_sitemap(sm, limit=50)
    for lp in cfg.get("list_pages", []):
        raw_paths += crawl_list_page(lp["url"], lp["link_selector"], limit=int(lp.get("limit", 15)))
    raw_paths += crawl_pages(cfg.get("pages", []))
    logging.info(f"Crawl complete: {len(raw_paths)} docs")
    return raw_paths
