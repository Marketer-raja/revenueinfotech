
## Current upgrade
See AUTOMATION_SETUP.md for the hourly automation, optional AI drafts and scheduled publishing. It supersedes the previous three-hour/manual-only workflow below.
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


## Editorial publishing workflow

- RSS collection is a research queue only; it does not publish candidate feed excerpts to the homepage.
- Editors review the original source, verify the facts and write an original article in `/newsdesk/`.
- Each approved item must include a real author/editor byline and an original article body of at least 600 characters.
- Saving and publishing through Newsdesk updates `home-news.json`. The GitHub Actions workflow then generates `/articles/<slug>/` article pages, NewsArticle structured data, canonical metadata and an updated sitemap.
- The 600-character check is a basic publishing safeguard, not an AdSense approval rule. Editorial quality, accuracy, usefulness, image rights and policy compliance still require human review.

See `EDITORIAL_WORKFLOW.md` for the full process.


## Editorial publishing workflow

- RSS collection is a research queue only; it does not publish candidate feed excerpts to the homepage.
- Editors review the original source, verify the facts and write an original article in `/newsdesk/`.
- Each approved item must include a real author/editor byline and an original article body of at least 600 characters.
- Saving and publishing through Newsdesk updates `home-news.json`. The GitHub Actions workflow then generates `/articles/<slug>/` article pages, NewsArticle structured data, canonical metadata and an updated sitemap.
- The 600-character check is a basic publishing safeguard, not an AdSense approval rule. Editorial quality, accuracy, usefulness, image rights and policy compliance still require human review.

See `EDITORIAL_WORKFLOW.md` for the full process.
