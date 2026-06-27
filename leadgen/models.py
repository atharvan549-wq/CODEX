from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class CampaignConfig:
    niche: str
    location: str
    budget: float
    min_quality: int
    limit: int = 10

    def validate(self) -> None:
        if not self.niche.strip():
            raise ValueError("Niche is required.")
        if not self.location.strip():
            raise ValueError("Location is required.")
        if self.budget < 0:
            raise ValueError("Budget must be zero or greater.")
        if not 0 <= self.min_quality <= 100:
            raise ValueError("Lead quality must be between 0 and 100.")
        if not 1 <= self.limit <= 50:
            raise ValueError("Lead limit must be between 1 and 50.")


@dataclass(slots=True)
class LeadCandidate:
    name: str
    niche: str
    location: str
    website: str | None = None
    description: str = ""
    source: str = "mock"


@dataclass(slots=True)
class EnrichedLead(LeadCandidate):
    email: str | None = None
    phone: str | None = None
    company_size: int | None = None
    estimated_monthly_budget: float | None = None
    social_url: str | None = None
    intent_signals: list[str] = field(default_factory=list)
    enrichment_notes: str = ""


@dataclass(slots=True)
class LeadScore:
    total: int
    quality: str
    reasons: list[str]
    components: dict[str, int]


@dataclass(slots=True)
class OutreachDraft:
    subject: str
    body: str
    personalization_notes: list[str]


@dataclass(slots=True)
class StoredLead:
    id: int
    campaign_id: int
    lead: EnrichedLead
    score: LeadScore
    outreach: OutreachDraft
    status: str
    created_at: str


def lead_from_row(row: dict[str, Any]) -> EnrichedLead:
    return EnrichedLead(
        name=row["name"],
        niche=row["niche"],
        location=row["location"],
        website=row["website"],
        description=row["description"],
        source=row["source"],
        email=row["email"],
        phone=row["phone"],
        company_size=row["company_size"],
        estimated_monthly_budget=row["estimated_monthly_budget"],
        social_url=row["social_url"],
        intent_signals=row["intent_signals"].split("|") if row["intent_signals"] else [],
        enrichment_notes=row["enrichment_notes"],
    )
