import argparse, logging, time, schedule
from .scraper.crawl import crawl_all
from .pipeline.clean import clean_all
from .pipeline.generate import generate_all
from .publishers.dispatch import publish_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def job_once():
    logging.info("Job start")
    raw = crawl_all()
    items = clean_all(raw)
    posts = generate_all(items)
    publish_all(posts)
    logging.info("Job done")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    args = p.parse_args()
    if args.once:
        job_once()
    else:
        job_once()
        schedule.every(2).hours.do(job_once)
        while True:
            schedule.run_pending()
            time.sleep(5)
