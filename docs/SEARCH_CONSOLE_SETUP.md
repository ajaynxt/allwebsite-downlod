# Search Console setup

1. Add the Domain property for `ajaynxt.com` using the DNS TXT method.
2. Alternatively add the URL-prefix property `https://download.ajaynxt.com/` and put only the verification token in `GOOGLE_SITE_VERIFICATION`.
3. Deploy, verify HTTPS and confirm the canonical page returns `200`.
4. Submit `https://download.ajaynxt.com/sitemap.xml`.
5. Inspect `/` and `/supported-sites`; request indexing once after the final release.
6. Check Page indexing, Manual actions, Security issues and Core Web Vitals weekly during launch.
7. Compare queries/pages over 28-day windows; do not chase daily volatility.

Sitemap submission is a discovery hint, not an indexing or ranking guarantee.
