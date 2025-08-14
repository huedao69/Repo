import os, requests, base64, logging

def publish_wordpress(post:dict):
    base = os.environ.get("WORDPRESS_BASE_URL")
    user = os.environ.get("WORDPRESS_USERNAME")
    app_pw = os.environ.get("WORDPRESS_APP_PASSWORD")
    if not all([base,user,app_pw]):
        logging.info("WordPress not configured; skipping.")
        return
    auth = base64.b64encode(f"{user}:{app_pw}".encode()).decode()
    status = post.get("status","pending")
    title = post.get("title") or (post["content"].split("\n",1)[0][:60])
    data = {"title": "Auto: " + title[:60],
            "content": post["content"],
            "status": status}
    r = requests.post(f"{base}/wp-json/wp/v2/posts",
                      headers={"Authorization": f"Basic {auth}"},
                      json=data, timeout=45)
    r.raise_for_status()
    logging.info(f"WP posted id={r.json().get('id')} status={status}")
