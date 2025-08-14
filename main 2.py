"""
app.main
- Schedules the end-to-end pipeline:
  1) crawl -> 2) process -> 3) generate -> 4) publish
"""
import os, json, time, logging, argparse
from datetime import datetime
import schedule
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from .scraper.crawl import crawl_all
from .pipeline.clean import clean_all
from .pipeline.generate import generate_all
from .publishers.dispatch import publish_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
load_dotenv()

def job_once():
    logging.info("Job start")
    raw_paths = crawl_all()
    items = clean_all(raw_paths)
    posts = generate_all(items)
    publish_all(posts)
    logging.info("Job done")

def schedule_loop():
    # Run immediately at start
    job_once()
    # Then every 2 hours
    schedule.every(2).hours.do(job_once)
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run single pass")
    args = parser.parse_args()
    if args.once:
        job_once()
    else:
        schedule_loop()
