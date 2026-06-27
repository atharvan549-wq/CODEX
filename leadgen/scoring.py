from .models import CampaignConfig, EnrichedLead, LeadScore


def score_lead(lead: EnrichedLead, config: CampaignConfig) -> LeadScore:
    components: dict[str, int] = {}
    reasons: list[str] = []

    niche_match = 25 if config.niche.lower() in lead.niche.lower() or lead.niche.lower() in config.niche.lower() else 10
    components["niche_match"] = niche_match
    if niche_match >= 25:
        reasons.append("Strong niche match")

    location_match = 20 if config.location.lower() in lead.location.lower() else 8
    components["location_match"] = location_match
    if location_match >= 20:
        reasons.append("Matches target location")

    budget = lead.estimated_monthly_budget or 0
    if config.budget == 0:
        budget_fit = 15
    else:
        ratio = min(budget / config.budget, 1.5)
        budget_fit = int(max(0, min(20, ratio * 14)))
    components["budget_fit"] = budget_fit
    if budget_fit >= 14:
        reasons.append("Estimated budget fits campaign")

    contactability = sum([bool(lead.email) * 8, bool(lead.phone) * 5, bool(lead.website) * 4, bool(lead.social_url) * 3])
    components["contactability"] = int(contactability)
    if contactability >= 15:
        reasons.append("Multiple contact paths available")

    intent = min(20, len(lead.intent_signals) * 5)
    components["intent"] = intent
    if intent >= 10:
        reasons.append("Useful intent signals found")

    completeness_fields = [lead.description, lead.company_size, lead.enrichment_notes]
    completeness = sum(1 for field in completeness_fields if field) * 5
    components["data_completeness"] = completeness

    total = min(100, sum(components.values()))
    if total >= 80:
        quality = "high"
    elif total >= 60:
        quality = "medium"
    else:
        quality = "low"
    if not reasons:
        reasons.append("Limited match data available")
    return LeadScore(total=total, quality=quality, reasons=reasons, components=components)
