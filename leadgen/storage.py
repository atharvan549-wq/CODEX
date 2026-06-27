from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import CampaignConfig, EnrichedLead, LeadScore, OutreachDraft, StoredLead, lead_from_row, utc_now


class LeadRepository:
    def __init__(self, db_path: str = "leadgen.db") -> None:
        self.db_path = db_path
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True) if Path(self.db_path).parent != Path(".") else None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche TEXT NOT NULL,
                    location TEXT NOT NULL,
                    budget REAL NOT NULL,
                    min_quality INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    location TEXT NOT NULL,
                    website TEXT,
                    description TEXT,
                    source TEXT,
                    email TEXT,
                    phone TEXT,
                    company_size INTEGER,
                    estimated_monthly_budget REAL,
                    social_url TEXT,
                    intent_signals TEXT,
                    enrichment_notes TEXT,
                    score INTEGER NOT NULL,
                    quality TEXT NOT NULL,
                    score_components TEXT NOT NULL,
                    score_reasons TEXT NOT NULL,
                    outreach_subject TEXT NOT NULL,
                    outreach_body TEXT NOT NULL,
                    personalization_notes TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                );
                """
            )

    def create_campaign(self, config: CampaignConfig) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO campaigns (niche, location, budget, min_quality, created_at) VALUES (?, ?, ?, ?, ?)",
                (config.niche, config.location, config.budget, config.min_quality, utc_now()),
            )
            return int(cursor.lastrowid)

    def save_lead(self, campaign_id: int, lead: EnrichedLead, score: LeadScore, outreach: OutreachDraft) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO leads (
                    campaign_id, name, niche, location, website, description, source, email, phone,
                    company_size, estimated_monthly_budget, social_url, intent_signals, enrichment_notes,
                    score, quality, score_components, score_reasons, outreach_subject, outreach_body,
                    personalization_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id, lead.name, lead.niche, lead.location, lead.website, lead.description,
                    lead.source, lead.email, lead.phone, lead.company_size, lead.estimated_monthly_budget,
                    lead.social_url, "|".join(lead.intent_signals), lead.enrichment_notes, score.total,
                    score.quality, json.dumps(score.components), json.dumps(score.reasons), outreach.subject,
                    outreach.body, json.dumps(outreach.personalization_notes), utc_now(),
                ),
            )
            return int(cursor.lastrowid)

    def list_leads(self) -> list[StoredLead]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM leads ORDER BY score DESC, created_at DESC").fetchall()
        stored: list[StoredLead] = []
        for row in rows:
            data = dict(row)
            stored.append(
                StoredLead(
                    id=data["id"],
                    campaign_id=data["campaign_id"],
                    lead=lead_from_row(data),
                    score=LeadScore(
                        total=data["score"],
                        quality=data["quality"],
                        reasons=json.loads(data["score_reasons"]),
                        components=json.loads(data["score_components"]),
                    ),
                    outreach=OutreachDraft(
                        subject=data["outreach_subject"],
                        body=data["outreach_body"],
                        personalization_notes=json.loads(data["personalization_notes"]),
                    ),
                    status=data["status"],
                    created_at=data["created_at"],
                )
            )
        return stored
