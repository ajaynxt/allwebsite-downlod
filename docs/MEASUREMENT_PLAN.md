# Measurement plan

## Funnel

| Stage | Event or signal | Decision use |
|---|---|---|
| Discovery | Search impressions, clicks, CTR, landing page | Query/title relevance |
| Intent | `link_analyzed` | Link form usefulness |
| Success | `direct_download_sent` | End-to-end product reliability |
| Support | `upi_id_copied` plus payment reconciliation | Voluntary support clarity |
| Reliability | 4xx/5xx, extraction failures, preparation time | Platform and capacity work |

The front end dispatches privacy-neutral `atoz:analytics` browser events and calls `gtag` only if the owner later loads an approved analytics configuration. Never send submitted media URLs, file names or UPI transaction data to analytics.
