import os, logging
from typing import List, Dict
from .wordpress import publish_wordpress

def publish_all(posts:List[Dict]):
    for p in posts:
        try:
            publish_wordpress(p)
        except Exception as ex:
            logging.warning(f"Publish skip: {ex}")
