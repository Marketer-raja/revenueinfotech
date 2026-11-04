# RevenueInfoTech – technology news publication

## Publishing model: hybrid automation + human approval

1. GitHub Actions runs `scripts/fetch_news.py` every three hours and refreshes `news.json` with RSS candidates.
2. Candidate collection does **not** publish to the homepage and does not overwrite `home-news.json`.
3. Open `/newsdesk/`, connect the repository with a fine-grained GitHub token, load candidate headlines, open and verify the original source, and rewrite the summary in original language with useful context.
4. Add the reviewed item to the homepage list and press **Publish to site**. This commits `home-news.json`; your hosting provider should redeploy it.
5. Check the live homepage and correct/remove errors promptly.

## Important
- `/news/` is a noindex source directory for feed excerpts, not an original-news archive.
- Do not copy publisher feed summaries into your own editorial copy. Follow each publisher's feed, image and attribution terms.
- Only claim original testing, interviews, credentials, author biographies or expert review when they are genuine and documented.
- The current repository contains a compiled React bundle but no original React source files or package manifest. For future maintainable UI changes, restore and commit the original application source project.
- This workflow improves editorial control but does not guarantee AdSense approval. The actual AdSense rejection reason and a live-site review are still needed.

## Run the feed collector locally

```bash
python3 scripts/fetch_news.py
```
