#!/usr/bin/env python3
"""
publisher.py - Official LinkedIn REST API Integration for Purna's Editorial System.
Uses official OAuth 2.0 with w_member_social and openid/profile scopes.
Supports:
- Text-only posts (high reach default)
- Single-image posts (/rest/images)
- Native Multi-Slide PDF Document Carousels (/rest/documents)
- Automated First Comment posting (/rest/socialActions/{urn}/comments)
- Strict deduplication against publishing_log.json and editorial-history.json
Zero browser automation. 100% compliant with LinkedIn's Developer Terms.
"""

import os
import sys
import re
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
EDITORIAL_HISTORY_FILE = LINKEDIN_DIR / "editorial-history.json"

DEFAULT_REDIRECT_URI = "http://localhost:3000/auth/callback"
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_IMAGES_INIT_URL = "https://api.linkedin.com/rest/images?action=initializeUpload"
LINKEDIN_DOCUMENTS_INIT_URL = "https://api.linkedin.com/rest/documents?action=initializeUpload"
LINKEDIN_SOCIAL_ACTIONS_URL = "https://api.linkedin.com/rest/socialActions"
LINKEDIN_V2_SOCIAL_ACTIONS_URL = "https://api.linkedin.com/v2/socialActions"
LINKEDIN_VERSION_CANDIDATES = ["202604", "202603", "202601", "202511"]
LINKEDIN_VERSION = "202604"


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


def is_already_published(candidate_id=None, topic=None):
    """
    Checks publishing_log.json to prevent duplicate publishing of the same candidate_id or topic.
    Returns: (already_published: bool, existing_entry: dict or None)
    """
    if not PUBLISHING_LOG_FILE.exists():
        return False, None
    try:
        with open(PUBLISHING_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
        norm_topic = (topic or "").strip().lower()
        for entry in logs:
            if candidate_id is not None and str(entry.get("candidate_id")) == str(candidate_id):
                return True, entry
            if norm_topic and entry.get("topic", "").strip().lower() == norm_topic:
                return True, entry
    except Exception:
        pass
    return False, None


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
    expires_in = token_data.get("expires_in", 5184000)  # Default 60 days

    creds["access_token"] = access_token
    creds["expires_at"] = int(time.time()) + int(expires_in)
    save_credentials(creds)

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

    suffix = img_file.suffix.lower()
    content_type = "image/png" if suffix == ".png" else "image/jpeg"
    if suffix == ".svg":
        png_counterpart = img_file.with_suffix(".png")
        if png_counterpart.exists():
            img_file = png_counterpart
            content_type = "image/png"
        else:
            return None

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


def upload_document(pdf_path, access_token=None, member_urn=None):
    """
    Uploads a multi-page PDF Carousel via LinkedIn's official Documents REST API (/rest/documents).
    Returns: 'urn:li:document:{id}'
    """
    creds = load_credentials()
    token = access_token or creds.get("access_token")
    urn = member_urn or creds.get("member_urn")

    if not token or not urn:
        raise ValueError("Missing access token or member URN for document upload.")

    doc_file = Path(pdf_path)
    if not doc_file.exists():
        raise FileNotFoundError(f"PDF document not found: {pdf_path}")

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
            init_resp = requests.post(LINKEDIN_DOCUMENTS_INIT_URL, headers=init_headers, json=init_payload)
            if init_resp.status_code in (200, 201):
                init_data = init_resp.json().get("value", {})
                break
            elif init_resp.status_code == 426:
                last_err = init_resp.text
                continue
            else:
                raise RuntimeError(f"Document Upload Init failed ({init_resp.status_code}): {init_resp.text}")

    if not init_data:
        raise RuntimeError(f"Document Upload Init failed (all versions rejected): {last_err}")

    upload_url = init_data.get("uploadUrl")
    document_urn = init_data.get("document")

    if HAS_REQUESTS:
        with open(doc_file, "rb") as f:
            upload_resp = requests.put(
                upload_url,
                data=f,
                headers={"Content-Type": "application/pdf"}
            )
        if upload_resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"Document binary upload failed ({upload_resp.status_code}): {upload_resp.text}")

        return document_urn

    return None


def post_first_comment(post_urn, comment_text, access_token=None, member_urn=None, parent_comment_urn=None):
    """
    Posts a comment (or reply to a comment) on a LinkedIn post URN via LinkedIn's official v2 Social Actions API
    (/v2/socialActions/{urn}/comments), which is supported under standard w_member_social scope.
    Returns: dict with comment_posted (bool), comment_id (str), and comment_urn (str).
    """
    if not post_urn or not comment_text or not comment_text.strip():
        return {"comment_posted": False, "reason": "Empty post_urn or comment_text"}

    creds = load_credentials()
    token = access_token or creds.get("access_token")
    urn = member_urn or creds.get("member_urn")

    if not token or not urn:
        return {"comment_posted": False, "reason": "Missing token or member_urn"}

    encoded_urn = urllib.parse.quote(post_urn, safe="")
    v2_comment_url = f"{LINKEDIN_V2_SOCIAL_ACTIONS_URL}/{encoded_urn}/comments"

    payload = {
        "actor": urn,
        "object": post_urn,
        "message": {
            "text": comment_text.strip()
        }
    }
    if parent_comment_urn:
        payload["parentComment"] = parent_comment_urn

    if HAS_REQUESTS:
        # 1. Primary path: /v2/socialActions/{encoded_urn}/comments (works with w_member_social)
        headers_v2 = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(v2_comment_url, headers=headers_v2, json=payload, timeout=15)
            # If target URN is a reshare wrapper, LinkedIn returns the actual threadUrn in the 400 message; auto-resolve it!
            if resp.status_code == 400 and "actual threadUrn:" in resp.text:
                m_thread = re.search(r"actual threadUrn:\s*(urn:li:[a-zA-Z0-9:]+)", resp.text)
                if m_thread:
                    real_urn = m_thread.group(1)
                    enc_real = urllib.parse.quote(real_urn, safe="")
                    v2_real_url = f"{LINKEDIN_V2_SOCIAL_ACTIONS_URL}/{enc_real}/comments"
                    payload["object"] = real_urn
                    post_urn = real_urn
                    resp = requests.post(v2_real_url, headers=headers_v2, json=payload, timeout=15)
            if resp.status_code in (200, 201):
                data = {}
                try:
                    data = resp.json()
                except Exception:
                    pass
                comment_id = data.get("id") or resp.headers.get("x-restli-id", "")
                comment_urn = data.get("$URN") or (f"urn:li:comment:({post_urn},{comment_id})" if comment_id else "")
                return {
                    "comment_posted": True,
                    "comment_id": str(comment_id),
                    "comment_urn": comment_urn,
                    "post_urn": post_urn
                }
            last_err = f"({resp.status_code}) {resp.text}"
        except Exception as e:
            last_err = str(e)

        # 2. Fallback path: versioned /rest/socialActions
        rest_comment_url = f"{LINKEDIN_SOCIAL_ACTIONS_URL}/{encoded_urn}/comments"
        for ver in LINKEDIN_VERSION_CANDIDATES:
            headers = {
                "Authorization": f"Bearer {token}",
                "LinkedIn-Version": ver,
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            try:
                resp = requests.post(rest_comment_url, headers=headers, json=payload, timeout=15)
                if resp.status_code in (200, 201):
                    comment_id = resp.headers.get("x-restli-id", "")
                    if not comment_id and resp.text:
                        try:
                            comment_id = resp.json().get("id", "")
                        except Exception:
                            pass
                    return {
                        "comment_posted": True,
                        "comment_id": str(comment_id),
                        "comment_urn": f"urn:li:comment:({post_urn},{comment_id})" if comment_id else "",
                        "post_urn": post_urn
                    }
                elif resp.status_code == 426:
                    continue
                else:
                    break
            except Exception:
                break

        return {"comment_posted": False, "reason": last_err}

    return {"comment_posted": False, "reason": "requests module unavailable"}


def publish_candidate_post(
    post_text,
    image_path=None,
    first_comment_text=None,
    document_title="Technical Architecture Breakdown",
    candidate_id=None,
    topic=None,
    allow_repost=False
):
    """
    Publishes a post to LinkedIn using the official POST /rest/posts API.
    Supports text-only, single-image (.png/.jpg), and multi-slide PDF carousel (.pdf).
    Automatically posts first_comment_text if supplied.
    Enforces deduplication against publishing_log.json unless allow_repost=True.
    """
    if not allow_repost and (candidate_id is not None or topic):
        already_pub, existing = is_already_published(candidate_id=candidate_id, topic=topic)
        if already_pub:
            raise ValueError(
                f"Duplicate publish blocked: Candidate #{candidate_id} ('{topic}') was already published "
                f"at {existing.get('published_at')} ({existing.get('post_id')})."
            )

    creds = load_credentials()
    token = creds.get("access_token")
    urn = creds.get("member_urn")

    if not token:
        raise ValueError("LinkedIn account is not authorized. Please connect your LinkedIn account first.")
    if not urn:
        userinfo = fetch_user_info(token)
        urn = f"urn:li:person:{userinfo.get('sub', '')}"
        creds["member_urn"] = urn
        creds["member_name"] = userinfo.get("name", "")
        save_credentials(creds)

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

    media_type = "text-only"
    if image_path:
        media_p = Path(image_path)
        if media_p.suffix.lower() == ".pdf":
            try:
                doc_urn = upload_document(image_path, token, urn)
                if doc_urn:
                    payload["content"] = {
                        "media": {
                            "id": doc_urn,
                            "title": document_title
                        }
                    }
                    media_type = "pdf-carousel"
            except Exception as e:
                print(f"[WARN] PDF Carousel upload failed, falling back to text-only post: {e}")
        else:
            try:
                image_urn = upload_image(image_path, token, urn)
                if image_urn:
                    payload["content"] = {
                        "media": {
                            "id": image_urn,
                            "altText": document_title or "Technical AI Infographic"
                        }
                    }
                    media_type = "image-attached"
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

        post_url = f"https://www.linkedin.com/feed/update/{post_id}/"

        # Automatically post First Comment if provided
        comment_res = {"comment_posted": False}
        if first_comment_text and first_comment_text.strip():
            time.sleep(1.5)
            comment_res = post_first_comment(post_id, first_comment_text, token, urn)

        return {
            "success": True,
            "post_id": post_id,
            "post_url": post_url,
            "media_type": media_type,
            "first_comment": comment_res,
            "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    else:
        raise RuntimeError("The 'requests' module is required for publishing operations.")


def record_published_post(candidate_id, post_data, post_result):
    """
    Records the published post into queue_summary.json, editorial-history.json, and publishing_log.json.
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

    # 2. Update editorial-history.json so topic is marked published=true
    if EDITORIAL_HISTORY_FILE.exists():
        try:
            with open(EDITORIAL_HISTORY_FILE, "r", encoding="utf-8") as f:
                ed_hist = json.load(f)
            topic_low = (post_data.get("topic") or "").lower()
            slug = (post_data.get("slug") or "").lower()
            modified_ed = False
            for t in ed_hist.get("topics", []):
                t_id = (t.get("id") or "").lower()
                t_title = (t.get("title") or "").lower()
                if (slug and slug in t_id) or (topic_low and (t_title[:18] in topic_low or topic_low[:18] in t_title)):
                    t["published"] = True
                    t["published_at"] = post_result.get("published_at")
                    t["linkedin_post_id"] = post_result.get("post_id")
                    modified_ed = True
            if modified_ed:
                with open(EDITORIAL_HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(ed_hist, f, indent=2)
        except Exception as e:
            print(f"[WARN] Error updating editorial-history.json: {e}")

    # 3. Append to history/publishing_log.json (deduplicating by candidate_id)
    logs = []
    if PUBLISHING_LOG_FILE.exists():
        try:
            with open(PUBLISHING_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    has_image = bool(post_data.get("has_image", False))
    comment_needed = bool(post_data.get("comment_needed", has_image))
    comment_info = post_result.get("first_comment", {})

    log_entry = {
        "candidate_id": candidate_id,
        "topic": post_data.get("topic", ""),
        "post_text": post_data.get("post_text", ""),
        "post_id": post_result.get("post_id"),
        "post_url": post_result.get("post_url"),
        "published_at": post_result.get("published_at"),
        "has_image": has_image,
        "media_type": post_result.get("media_type", "image-attached" if has_image else "text-only"),
        "comment_needed": comment_needed,
        "first_comment_posted": comment_info.get("comment_posted", False),
        "first_comment_id": comment_info.get("comment_id", ""),
        "sources": post_data.get("sources", ""),
        "status": "PUBLISHED"
    }
    logs = [entry for entry in logs if str(entry.get("candidate_id")) != str(candidate_id)]
    logs.insert(0, log_entry)
    with open(PUBLISHING_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    # 4. Create published archive file
    archive_file = PUBLISHED_DIR / f"published_{candidate_id}.md"
    comment_section = f"""### FIRST COMMENT (SOURCES)
{post_data.get('sources', '')}""" if comment_needed else "> [!NOTE]\n> Text-Only Post: GitHub link included directly in post text above. No separate first comment needed."

    archive_content = f"""# PUBLISHED POST: {post_data.get('topic', '')}
- **Candidate ID:** {candidate_id}
- **Published Date:** {post_result.get('published_at')}
- **Format:** {post_result.get('media_type', 'Image-Attached' if has_image else 'Text-Only')}
- **LinkedIn Post ID:** {post_result.get('post_id')}
- **LinkedIn Post URL:** {post_result.get('post_url')}
- **First Comment Auto-Posted:** {comment_info.get('comment_posted', False)}
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
