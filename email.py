import os, requests, logging

def send_email_if_configured(posts):
    domain = os.environ.get("MAILGUN_DOMAIN")
    key = os.environ.get("MAILGUN_API_KEY")
    if not (domain and key):
        return
    # Send a simple daily digest to yourself to verify pipeline
    to_email = os.environ.get("DIGEST_TO","you@example.com")
    subject = f"[ACS] Digest ({len(posts)} posts)"
    body = "\n\n".join([p["content"][:500] for p in posts[:5]])
    requests.post(f"https://api.mailgun.net/v3/{domain}/messages",
                  auth=("api", key),
                  data={"from": f"ACS <digest@{domain}>",
                        "to": [to_email],
                        "subject": subject,
                        "text": body})
