# RevenueInfoTech deployment checklist

## Before replacing the repository
1. Make a backup or GitHub branch of the current live repository.
2. Extract the ZIP and open the `revenueinfotech-main` folder.
3. Copy the *contents* of that folder to the root of the same GitHub repository and branch currently connected to your hosting provider. Keep the `.github` folder.
4. Confirm `.github/workflows/update-news.yml` is present in the repository.
5. Confirm your hosting provider is still connected to that repository and production branch.

## First deployment and workflow test
1. Commit and push the updated files. Wait for Cloudflare Pages, Netlify or your current host to finish deploying.
2. In GitHub, open **Actions** → **RevenueInfoTech editorial publishing** → **Run workflow**. This manually tests the RSS candidate collection and article build.
3. Confirm the run succeeds and `news.json`, `news/index.html` and `sitemap.xml` are updated by the workflow. RSS candidates should remain unpublished.
4. Open the live homepage, `/about.html`, `/contact.html`, `/privacy-policy.html`, `/news/`, `/newsdesk/`, `/articles/`, `/robots.txt` and `/sitemap.xml`.

## Test manual editorial publication
1. Open `/newsdesk/` and connect to the same GitHub owner, repository and branch.
2. Create a fine-grained GitHub personal access token limited to this repository with **Contents: Read and write**. Do not share it or save it on a shared computer. Revoke it if it is exposed.
3. Load a candidate, open the original source and verify its date, facts and claims.
4. Write an original summary and a substantial original article, add a real author/editor byline, and use only images you own or are licensed to republish.
5. Save the item and press **Publish to site**.
6. The `home-news.json` commit should trigger the GitHub Actions workflow. Confirm the action generates `/articles/<slug>/`, updates `/articles/` and adds the article to `sitemap.xml`.
7. Wait for the hosting provider to deploy the generated commit, then open the article URL and test its canonical URL and structured data.

## Before requesting another AdSense review
- Review and remove or replace old feed-only entries in Newsdesk; they are not treated as approved articles by the updated homepage.
- Audit every preloaded sample article, author profile, benchmark, review score, product test and statistic in the compiled React bundle. Keep only material that is genuine and can be substantiated.
- Publish useful, original reporting with real bylines and source links. Do not copy or lightly rewrite RSS excerpts.
- Confirm the contact email is monitored and the privacy/consent disclosures match the analytics and advertising technologies actually enabled.
- Read the exact rejection reason in the AdSense account and address it before applying again.

The 600-character Newsdesk validation is only a publishing safeguard, not an AdSense word-count requirement. No code change can guarantee AdSense approval.
