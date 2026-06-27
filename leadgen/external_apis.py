from __future__ import annotations

import hashlib
from dataclasses import asdict
from urllib.parse import quote_plus

from .models import CampaignConfig, EnrichedLead, LeadCandidate, OutreachDraft


class ExternalApiError(RuntimeError):
    """Raised when an upstream lead, enrichment, or message provider fails."""


class MockLeadSource:
    """Collects deterministic sample leads.

    Production swap: call Google Places, Apollo, Yelp Fusion, a CRM export, or another
    consent-friendly source here. Keep the returned `LeadCandidate` shape stable and
    wrap provider exceptions in `ExternalApiError` so the API layer can return a safe
    error response.
    """

    def search(self, config: CampaignConfig) -> list[LeadCandidate]:
        base_names = [
            "Northstar", "Brightpath", "Summit", "Evergreen", "Bluebird",
            "Crescent", "Keystone", "Juniper", "Harbor", "Maple",
        ]
        suffix = config.niche.rstrip("s").title()
        location_slug = quote_plus(config.location.lower())
        niche_slug = quote_plus(config.niche.lower())
        leads: list[LeadCandidate] = []
        for idx, name in enumerate(base_names[: config.limit], start=1):
            leads.append(
                LeadCandidate(
                    name=f"{name} {suffix}",
                    niche=config.niche,
                    location=config.location,
                    website=f"https://example.com/{location_slug}/{niche_slug}/{idx}",
                    description=(
                        f"{name} serves {config.location} customers in the "
                        f"{config.niche} market and is evaluating growth channels."
                    ),
                    source="mock-lead-source",
                )
            )
        return leads


class MockEnrichmentProvider:
    """Adds firmographic and contact attributes to collected leads.

    Production swap: call enrichment APIs such as Clearbit, People Data Labs, Hunter,
    BuiltWith, or your CRM. Recommended additions include retry/backoff, rate limit
    tracking, per-provider timeouts, and field provenance metadata.
    """

    def enrich(self, candidate: LeadCandidate, config: CampaignConfig) -> EnrichedLead:
        seed = int(hashlib.sha256(candidate.name.encode("utf-8")).hexdigest(), 16)
        size = 5 + seed % 95
        estimated_budget = float(500 + seed % 9000)
        domain = candidate.website.split("/")[2] if candidate.website else "example.com"
        signals = ["active local market", "service page detected"]
        if estimated_budget >= config.budget * 0.75:
            signals.append("budget-fit signal")
        if seed % 2 == 0:
            signals.append("recent hiring activity")
        if seed % 3 == 0:
            signals.append("paid ads detected")
        return EnrichedLead(
            **asdict(candidate),
            email=f"growth@{domain}",
            phone=f"+1-555-{1000 + seed % 9000}",
            company_size=size,
            estimated_monthly_budget=estimated_budget,
            social_url=f"https://linkedin.com/company/{quote_plus(candidate.name.lower())}",
            intent_signals=signals,
            enrichment_notes="Mock enrichment generated from deterministic lead attributes.",
        )


class TemplateOutreachGenerator:
    """Prepares personalized outreach drafts.

    Production swap: call an LLM or engagement platform here. Preserve compliance
    controls: identify the sender, avoid deceptive claims, include opt-out language,
    and review generated copy before sending.
    """

    def generate(self, lead: EnrichedLead, config: CampaignConfig) -> OutreachDraft:
        strongest_signal = lead.intent_signals[0] if lead.intent_signals else "growth opportunity"
        subject = f"Idea for {lead.name}'s {config.location} growth"
        body = (
            f"Hi {lead.name} team,\n\n"
            f"I noticed your work in {config.niche} around {config.location}, especially the "
            f"{strongest_signal} signal. We help similar teams prioritize the highest-fit "
            f"prospects, enrich account data, and prepare relevant outreach without adding "
            f"manual research time.\n\n"
            f"Based on your public profile, a focused campaign around {config.niche.lower()} "
            f"buyers could fit your approximate monthly growth budget. Would it be useful if "
            f"I shared a short lead-quality plan for {lead.name}?\n\n"
            "Best,\nYour Growth Team\n\n"
            "P.S. If this is not relevant, reply 'no thanks' and I will not follow up."
        )
        return OutreachDraft(
            subject=subject,
            body=body,
            personalization_notes=[
                f"Referenced niche: {config.niche}",
                f"Referenced location: {config.location}",
                f"Used signal: {strongest_signal}",
            ],
        )
