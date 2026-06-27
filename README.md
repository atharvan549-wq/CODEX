# AI Lead Generation System

A lightweight, runnable lead generation application that collects leads for a selected niche, enriches them, stores them in SQLite, scores them for relevance, and prepares personalized outreach messages.

The app uses only Python's standard library so it can run locally without external dependencies. External search, enrichment, and AI APIs are represented behind adapter classes in `leadgen/external_apis.py`, making them easy to replace later.

## Features

- Admin controls for niche, location, monthly budget, and minimum lead quality.
- Lead collection from a configurable mock source.
- Lead enrichment with website, contact, social, size, location, and intent signals.
- SQLite persistence for campaigns, leads, scores, and outreach drafts.
- Relevance scoring based on niche match, location match, budget fit, contactability, intent, and data completeness.
- Personalized outreach generation with an explainable message rationale.
- Error handling and structured API responses.

## Quick start

```bash
python3 -m leadgen.app
```

Open <http://127.0.0.1:8000> and configure a campaign from the admin panel.

## API examples

Create and run a campaign:

```bash
curl -X POST http://127.0.0.1:8000/api/campaigns/run \
  -H 'Content-Type: application/json' \
  -d '{"niche":"Dental clinics","location":"Austin, TX","budget":2500,"min_quality":65,"limit":8}'
```

List stored leads:

```bash
curl http://127.0.0.1:8000/api/leads
```

## Connecting external APIs later

The production integration points are isolated in `leadgen/external_apis.py`:

1. Replace `MockLeadSource.search()` with a search provider such as Google Places, Apollo, Yelp Fusion, LinkedIn Sales Navigator exports, or a compliant web crawler.
2. Replace `MockEnrichmentProvider.enrich()` with Clearbit, People Data Labs, Hunter, BuiltWith, or a CRM enrichment endpoint.
3. Replace `TemplateOutreachGenerator.generate()` with an LLM call or marketing automation API.
4. Store API keys as environment variables, e.g. `GOOGLE_PLACES_API_KEY`, never in source control.
5. Keep the return shape compatible with the `LeadCandidate`, `EnrichedLead`, and `OutreachDraft` dataclasses so scoring and persistence continue to work.
6. Add rate-limit handling, retries with backoff, API usage accounting, and consent/compliance filters before enabling real outreach.

See `leadgen/external_apis.py` for method-level notes and examples.
