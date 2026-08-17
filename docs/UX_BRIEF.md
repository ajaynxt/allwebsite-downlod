# UX Brief

## Product

A TO Z Link Downloader: a focused utility for analyzing one public media link and saving a permitted video or audio file.

## Audience and top tasks

Primary audience: mobile-first creators, editors, and business owners who already have a media URL.

1. Paste and validate a link.
2. Understand what media was found and select quality/output.
3. Track preparation and save the final file.

## Success event

A user reaches a `ready` job state and deliberately selects “Save file” without confusion about source quality or permission.

## Platforms and context

Responsive web, optimized first for mid-range mobile devices and then desktop. Usage can include slow networks and longer-running media jobs.

## Brand and content

Product-led editorial direction: warm paper, strong ink, restrained cobalt and coral accents, human typography, no stock-photo dependency, no fake statistics.

## Constraints

- Static same-origin frontend plus FastAPI backend
- Platform support is determined by maintained extractors and can change
- No login, permanent user library, private cookies, playlists, DRM bypass, or live downloads
- Best quality means best source quality; it does not invent resolution

## Accessibility target

WCAG 2.2 AA baseline: semantic form controls, labels, keyboard navigation, visible focus, live job status, sufficient contrast, 200% zoom/reflow, and reduced-motion support.

## Required states

Initial, invalid URL, analyzing, unsupported/private/expired link, media found, video/audio selection, missing permission, queued, downloading, processing, ready, failed, rate-limited, and expired job.

## Measurement plan

Recommended privacy-preserving events after launch: analyze success rate by extractor, job completion rate, median processing time, error reason code, and output type. Do not store full pasted URLs in analytics.
