# WORKFLOW: /li-comment (First Comment & Source Link Generator)

**Trigger Command:** `/li-comment <post draft or topic>`  
**Goal:** Generate a clean, high-value first comment containing primary sources, technical references, or extra context without cluttering the main post.

---

> [!NOTE]
> **Text-Only Posts:** If posting without an image, the GitHub repository link is included directly at the end of the post text itself (`Repo: https://github.com/...`). **Do NOT post or require a separate comment for text-only posts.**
> First comments are only used for media/image posts where keeping links out of the post caption protects algorithm distribution.

1. Extract all URLs, technical paper links, official announcements, pricing pages, and GitHub repos referenced during research.
2. Format the comment cleanly with bullet points.
3. Add a short 1-line engineering context summary for each source.

---

## FORMAT

```markdown
Sources & Technical Links:

- Official Announcement: <URL>
- Technical Report / arXiv: <URL>
- GitHub Repository: <URL>
- Official Pricing & API Docs: <URL>
```
