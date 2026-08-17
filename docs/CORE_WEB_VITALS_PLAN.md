# Core Web Vitals plan

## Current safeguards

- No web-font request, framework bundle, autoplay media or third-party ad script.
- Deferred first-party JavaScript and fixed image dimensions in social metadata.
- Server-rendered crawlable content; functional UI progressively enhances it.

## Production measurement

1. Monitor field LCP, INP and CLS in Search Console after sufficient traffic.
2. Add explicit dimensions for any future in-page ad creative to prevent layout shift.
3. Keep initial third-party scripts consent-gated and delayed.
4. Compress and cache static assets at Nginx/CDN; do not cache API/job responses.
5. Re-test mobile performance whenever ads, analytics or a large hero image changes.
