from .external_apis import MockEnrichmentProvider, MockLeadSource, TemplateOutreachGenerator
from .models import CampaignConfig, StoredLead
from .scoring import score_lead
from .storage import LeadRepository


class LeadGenerationPipeline:
    def __init__(self, repository: LeadRepository | None = None) -> None:
        self.repository = repository or LeadRepository()
        self.lead_source = MockLeadSource()
        self.enrichment = MockEnrichmentProvider()
        self.outreach = TemplateOutreachGenerator()

    def run(self, config: CampaignConfig) -> list[StoredLead]:
        config.validate()
        campaign_id = self.repository.create_campaign(config)
        candidates = self.lead_source.search(config)
        saved_ids: list[int] = []
        for candidate in candidates:
            enriched = self.enrichment.enrich(candidate, config)
            score = score_lead(enriched, config)
            if score.total < config.min_quality:
                continue
            draft = self.outreach.generate(enriched, config)
            saved_ids.append(self.repository.save_lead(campaign_id, enriched, score, draft))
        return [lead for lead in self.repository.list_leads() if lead.id in saved_ids]
