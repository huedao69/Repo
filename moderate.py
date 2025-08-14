import os, re, json, yaml
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def _client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def _load_safety_cfg()->Dict:
    import pathlib
    cfg_path = pathlib.Path(__file__).with_name("../config/safety.yaml").resolve()
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def keyword_screen(text:str, blacklist)->Dict:
    hits = []
    low = text.lower()
    for kw in blacklist or []:
        if kw.lower() in low:
            hits.append(kw)
    return {"hits": hits, "ok": len(hits) == 0}

def ai_policy_screen(title:str, body:str)->Dict:
    client = _client()
    msg = f"""Bạn là bộ lọc kiểm duyệt nội dung tiếng Việt.
Phân loại bài sau thành: OK, REVIEW, BLOCK.
- OK: an toàn, có dẫn nguồn.
- REVIEW: rủi ro/nhạy cảm/chưa rõ nguồn.
- BLOCK: vi phạm (kích động, khiêu dâm, bạo lực, lừa đảo, chính trị nhạy cảm...).

Chỉ trả JSON: {{"decision":"OK/REVIEW/BLOCK", "reasons":[...]}}.

Tiêu đề: {title}
Nội dung: {body[:3500]}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"Chỉ trả JSON hợp lệ."},
                  {"role":"user","content":msg}],
        temperature=0.0,
    )
    raw = resp.choices[0].message.content.strip()
    try:
        if raw.startswith("```"):
            raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
    except Exception:
        data = {"decision":"REVIEW","reasons":["parse_error"]}
    return data

def moderate_post(post:Dict)->Dict:
    cfg = _load_safety_cfg()
    text = post.get("content","")
    citation_ok = True
    if cfg.get("require_citations"):
        citation_ok = ("http://" in text) or ("https://" in text)
    kw = keyword_screen(text, cfg.get("blacklist", []))
    ai = ai_policy_screen(post.get("title",""), text)
    decision = "OK"
    reasons = []
    if not citation_ok:
        decision = "REVIEW"; reasons.append("missing_citation")
    if not kw["ok"]:
        decision = "REVIEW"; reasons.append("blacklist_hits:" + ",".join(kw["hits"]))
    if ai.get("decision") == "BLOCK":
        decision = "BLOCK"
    elif ai.get("decision") == "REVIEW" and decision == "OK":
        decision = "REVIEW"
    reasons += ai.get("reasons", [])
    return {"decision": decision, "reasons": reasons}
