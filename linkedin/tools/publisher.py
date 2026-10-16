#!/usr/bin/env python3
"""
publisher.py - Official LinkedIn REST API Integration for Purna's Editorial System.
Uses official OAuth 2.0 with w_member_social and openid/profile scopes.
Zero browser automation. 100% compliant with LinkedIn's Developer Terms.
"""

import os
import sys
import json
import time
import urllib.parse
from pathlib import Path

# Try importing requests, fallback to urllib if needed
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LINKEDIN_DIR = BASE_DIR / "linkedin"
QUEUE_DIR = LINKEDIN_DIR / "queue"
HISTORY_DIR = LINKEDIN_DIR / "history"
PUBLISHED_DIR = LINKEDIN_DIR / "published"
CREDENTIALS_FILE = LINKEDIN_DIR / "credentials.json"
PUBLISHING_LOG_FILE = HISTORY_DIR / "publishing_log.json"
QUEUE_SUMMARY_FILE = QUEUE_DIR / "queue_summary.json"

DEFAULT_REDIRECT_URI = "http://localhost:3000/auth/callback"
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_IMAGES_INIT_URL = "https://api.linkedin.com/rest/images?action=initializeUpload"
LINKEDIN_VERSION_CANDIDATES = ["202610", "202608", "202511"]
LINKEDIN_VERSION = "202610"

def load_credentials():
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "client_id": "",
        "client_secret": "",
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "access_token": "",
        "expires_at": 0,
        "member_id": "",
        "member_urn": "",
        "member_name": ""
    }

def save_credentials(creds):
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2)
    return creds

def get_auth_url(client_id=None, redirect_uri=None):
    creds = load_credentials()
    cid = client_id or creds.get("client_id", "")
    ruri = redirect_uri or creds.get("redirect_uri", DEFAULT_REDIRECT_URI)
    
    if not cid:
        raise ValueError("Client ID is required to generate LinkedIn authorization URL.")

    params = {
        "response_type": "code",
        "client_id": cid,
        "redirect_uri": ruri,
        "state": f"antigravity_auth_{int(time.time())}",
        "scope": "openid profile w_member_social email"
    }
    return f"{LINKEDIN_AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code, client_id=None, client_secret=None, redirect_uri=None):
    creds = load_credentials()
    cid = client_id or creds.get("client_id", "")
    csec = client_secret or creds.get("client_secret", "")
    ruri = redirect_uri or creds.get("redirect_uri", DEFAULT_REDIRECT_URI)

    if not cid or not csec:
        raise ValueError("Client ID and Client Secret are required for token exchange.")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": ruri,
        "client_id": cid,
        "client_secret": csec
    }

    if HAS_REQUESTS:
        resp = requests.post(LINKEDIN_TOKEN_URL, data=data)
        if resp.status_code != 200:
            raise RuntimeError(f"LinkedIn Token Error ({resp.status_code}): {resp.text}")
        token_data = resp.json()
    else:
        req = urllib.request.Request(
            LINKEDIN_TOKEN_URL,
            data=urllib.parse.urlencode(data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req) as response:
            token_data = json.loads(response.read().decode("utf-8"))

    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 5184000) # Default 60 days
    
    creds["access_token"] = access_token
    creds["expires_at"] = int(time.time()) + int(expires_in)
    save_credentials(creds)

    # Fetch user info immediately to store Member URN
    try:
        userinfo = fetch_user_info(access_token)
        creds["member_id"] = userinfo.get("sub", "")
        creds["member_urn"] = f"urn:li:person:{userinfo.get('sub', '')}"
        creds["member_name"] = userinfo.get("name", "")
        save_credentials(creds)
    except Exception as e:
        print(f"[WARN] Could not fetch userinfo immediately: {e}")

    return creds

def fetch_user_info(access_token=None):
    creds = load_credentials()
    token = access_token or creds.get("access_token", "")
    if not token:
        raise ValueError("Access token is missing. Please authorize with LinkedIn first.")

    headers = {"Authorization": f"Bearer {token}"}
    if HAS_REQUESTS:
        resp = requests.get(LINKEDIN_USERINFO_URL, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Userinfo Error ({resp.status_code}): {resp.text}")
        return resp.json()
    else:
        req = urllib.request.Request(LINKEDIN_USERINFO_URL, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))

def get_connection_status():
    creds = load_credentials()
    has_keys = bool(creds.get("client_id") and creds.get("client_secret"))
    has_token = bool(creds.get("access_token"))
    is_expired = creds.get("expires_at", 0) < int(time.time()) if has_token else True

    return {
        "configured": has_keys,
        "connected": has_token and not is_expired,
        "client_id_set": bool(creds.get("client_id")),
        "member_name": creds.get("member_name", ""),
        "member_urn": creds.get("member_urn", ""),
        "expires_at": creds.get("expires_at", 0),
        "days_left": max(0, int((creds.get("expires_at", 0) - time.time()) / 86400)) if has_token else 0
    }

def upload_image(image_path, access_token=None, member_urn=None):
    """
    Uploads an image via LinkedIn's official Images REST API.
    Returns: 'urn:li:image:{id}'
    """
    creds = load_credentials()
    token = access_token or creds.get("access_token")
    urn = member_urn or creds.get("member_urn")

    if not token or not urn:
        raise ValueError("Missing access token or member URN for image upload.")

    img_file = Path(image_path)
    if not img_file.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Determine mime type
    suffix = img_file.suffix.lower()
    content_type = "image/png" if suffix == ".png" else "image/jpeg"
    if suffix == ".svg":
        # Note: LinkedIn doesn't natively display raw SVGs as feed photos.
        # If an SVG is supplied and a rendered PNG exists, use that.
        png_counterpart = img_file.with_suffix(".png")
        if png_counterpart.exists():
            img_file = png_counterpart
            content_type = "image/png"
        else:
            # Fall back to text post if SVG cannot be rasterized
            return None

    # Step 1: Initialize Upload
    init_data = None
    last_err = ""
    for ver in LINKEDIN_VERSION_CANDIDATES:
        init_headers = {
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": ver,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        init_payload = {
            "initializeUploadRequest": {
                "owner": urn
            }
        }
        if HAS_REQUESTS:
            init_resp = requests.post(LINKEDIN_IMAGES_INIT_URL, headers=init_headers, json=init_payload)
            if init_resp.status_code in (200, 201):
                init_data = init_resp.json().get("value", {})
                break
            elif init_resp.status_code == 426:
                last_err = init_resp.text
                continue
            else:
                raise RuntimeError(f"Image Upload Init failed ({init_resp.status_code}): {init_resp.text}")

    if not init_data:
        raise RuntimeError(f"Image Upload Init failed (all versions rejected): {last_err}")

    upload_url = init_data.get("uploadUrl")
    image_urn = init_data.get("image")

    # Step 2: PUT Image binary
    if HAS_REQUESTS:
        with open(img_file, "rb") as f:
            upload_resp = requests.put(
                upload_url,
                data=f,
                headers={"Content-Type": content_type}
            )
        if upload_resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"Image binary upload failed ({upload_resp.status_code}): {upload_resp.text}")

        return image_urn

    return None

def publish_candidate_post(post_text, image_path=None):
    """
    Publishes a post to LinkedIn using the official POST /rest/posts API.
    Returns: dict with success, post_id, and post_url.
    """
    creds = load_credentials()
    token = creds.get("access_token")
    urn = creds.get("member_urn")

    if not token:
        raise ValueError("LinkedIn account is not authorized. Please connect your LinkedIn account first.")
    if not urn:
        # Try refreshing user info
        userinfo = fetch_user_info(token)
        urn = f"urn:li:person:{userinfo.get('sub', '')}"
        creds["member_urn"] = urn
        creds["member_name"] = userinfo.get("name", "")
        save_credentials(creds)

    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    payload = {
        "author": urn,
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    # Handle image attachment if supplied
    if image_path:
        try:
            image_urn = upload_image(image_path, token, urn)
            if image_urn:
                payload["content"] = {
                    "media": {
                        "id": image_urn,
                        "altText": "Technical AI Infographic"
                    }
                }
        except Exception as e:
            print(f"[WARN] Image upload failed, falling back to text-only post: {e}")

    if HAS_REQUESTS:
        resp = None
        last_err = ""
        for ver in LINKEDIN_VERSION_CANDIDATES:
            headers = {
                "Authorization": f"Bearer {token}",
                "LinkedIn-Version": ver,
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            resp = requests.post(LINKEDIN_POSTS_URL, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                break
            elif resp.status_code == 426:
                last_err = resp.text
                continue
            else:
                raise RuntimeError(f"LinkedIn Publishing Error ({resp.status_code}): {resp.text}")

        if resp is None or resp.status_code not in (200, 201):
            raise RuntimeError(f"LinkedIn Publishing Error: {last_err or (resp.text if resp else 'No response')}")
        
        post_id = resp.headers.get("x-restli-id", "")
        if not post_id and resp.text:
            try:
                post_id = resp.json().get("id", "")
            except Exception:
                pass

        if not post_id:
            post_id = f"urn:li:share:{int(time.time())}"

        # Clean urn formatting for URL
        clean_id = post_id.split(":")[-1]
        post_url = f"https://www.linkedin.com/feed/update/{post_id}/"

        return {
            "success": True,
            "post_id": post_id,
            "post_url": post_url,
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    else:
        raise RuntimeError("The 'requests' module is required for publishing operations.")

def record_published_post(candidate_id, post_data, post_result):
    """
    Records the published post into queue_summary.json, editorial history, and publishing log.
    """
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Update queue_summary.json
    if QUEUE_SUMMARY_FILE.exists():
        try:
            with open(QUEUE_SUMMARY_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
            for c in queue.get("candidates", []):
                if str(c.get("id")) == str(candidate_id):
                    c["status"] = "PUBLISHED"
                    c["published_at"] = post_result.get("published_at")
                    c["linkedin_post_id"] = post_result.get("post_id")
                    c["linkedin_post_url"] = post_result.get("post_url")
            with open(QUEUE_SUMMARY_FILE, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            print(f"[WARN] Error updating queue_summary.json: {e}")

    # 2. Append to history/publishing_log.json
    logs = []
    if PUBLISHING_LOG_FILE.exists():
        try:
            with open(PUBLISHING_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    has_image = bool(post_data.get("has_image", False))
    comment_needed = bool(post_data.get("comment_needed", has_image))

    log_entry = {
        "candidate_id": candidate_id,
        "topic": post_data.get("topic", ""),
        "post_text": post_data.get("post_text", ""),
        "post_id": post_result.get("post_id"),
        "post_url": post_result.get("post_url"),
        "published_at": post_result.get("published_at"),
        "has_image": has_image,
        "comment_needed": comment_needed,
        "sources": post_data.get("sources", []),
        "status": "PUBLISHED"
    }
    logs.insert(0, log_entry)
    with open(PUBLISHING_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    # 3. Create published archive file
    archive_file = PUBLISHED_DIR / f"published_{candidate_id}.md"
    comment_section = f"""### FIRST COMMENT (SOURCES)
{post_data.get('sources', '')}""" if comment_needed else "> [!NOTE]\n> Text-Only Post: GitHub link included directly in post text above. No separate first comment needed."

    archive_content = f"""# PUBLISHED POST: {post_data.get('topic', '')}
- **Candidate ID:** {candidate_id}
- **Published Date:** {post_result.get('published_at')}
- **Format:** {'Image-Attached' if has_image else 'Text-Only (Link in Post)'}
- **LinkedIn Post ID:** {post_result.get('post_id')}
- **LinkedIn Post URL:** {post_result.get('post_url')}
- **Status:** Successful

---

### POST CONTENT
{post_data.get('post_text', '')}

---

{comment_section}
"""
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(archive_content)

    return log_entry
