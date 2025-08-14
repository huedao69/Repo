import os, json, re, logging
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pathlib import Path

DATA_PROCESSED = "/data/processed"

def html_to_text(html:str)->str:
    soup = BeautifulSoup(html, "lxml")
    # remove script/style
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:100000]  # limit

def normalize(item:dict)->dict:
    url = item["url"]
    text = html_to_text(item["content"])
    return {
        "url": url,
        "title": item.get("meta",{}).get("title") or text[:80],
        "text": text,
        "source": urlparse(url).netloc,
        "published": item.get("meta",{}).get("published"),
    }

def clean_all(raw_paths:List[str])->List[Dict]:
    Path(DATA_PROCESSED).mkdir(parents=True, exist_ok=True)
    out = []
    for p in raw_paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                raw = json.load(f)
            norm = normalize(raw)
            out.append(norm)
        except Exception as ex:
            logging.warning(f"Clean skip {p}: {ex}")
    return out
