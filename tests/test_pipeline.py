import tempfile
import unittest

from leadgen.models import CampaignConfig
from leadgen.pipeline import LeadGenerationPipeline
from leadgen.storage import LeadRepository


class LeadGenerationPipelineTest(unittest.TestCase):
    def test_pipeline_collects_enriches_scores_and_stores_leads(self):
        with tempfile.NamedTemporaryFile() as database:
            repository = LeadRepository(database.name)
            pipeline = LeadGenerationPipeline(repository)
            leads = pipeline.run(
                CampaignConfig(
                    niche="Dental clinics",
                    location="Austin, TX",
                    budget=2500,
                    min_quality=60,
                    limit=5,
                )
            )

            self.assertGreater(len(leads), 0)
            self.assertTrue(all(lead.score.total >= 60 for lead in leads))
            self.assertTrue(all(lead.lead.email for lead in leads))
            self.assertTrue(all(lead.outreach.body for lead in leads))
            self.assertEqual(len(repository.list_leads()), len(leads))

    def test_validation_rejects_invalid_quality(self):
        with self.assertRaises(ValueError):
            CampaignConfig("Dental clinics", "Austin, TX", 2500, 101).validate()


if __name__ == "__main__":
    unittest.main()
