import os, json, logging
from typing import List, Dict
from jinja2 import Template
from dotenv import load_dotenv
from openai import OpenAI

DATA_PUBLISHED = "/data/published"
PROMPT_DIR = "/app/config/prompts"

load_dotenv()

def _client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def _load_prompt(name:str)->str:
    with open(os.path.join(PROMPT_DIR, f"{name}.yaml"), "r", encoding="utf-8") as f:
        return f.read()

def call_gpt(system:str, user:str)->str:
    client = _client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0.4,
    )
    return resp.choices[0].message.content

def make_article(item:Dict)->Dict:
    system = "You are a careful editor. Summarize with citations to original URLs, no hallucinations."
    user = f"""Create a 500-800 word article in Vietnamese about the following source.
- Title: {item['title']}
- Source URL: {item['url']}
- Extracted text:
{item['text'][:4000]}
Include: 1) short headline, 2) 50-word summary, 3) body with 3-5 subheadings, 4) bullet list of key facts with the source URL, 5) SEO meta (title 60 chars, description 150 chars).
"""
    content = call_gpt(system, user)
    return {"type":"article","content":content,"source_url":item["url"]}

def generate_all(items:List[Dict])->List[Dict]:
    posts = []
    for it in items[:20]:
        try:
            posts.append(make_article(it))
        except Exception as ex:
            logging.warning(f"Gen skip {it.get('url')}: {ex}")
    return posts
