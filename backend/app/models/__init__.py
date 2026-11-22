"""Importing this package registers every model on Base.metadata (needed by create_all)."""

from app.models.application import Application
from app.models.draft import ApplicationDraft
from app.models.family import Family
from app.models.legal_parameter import LegalParameter
from app.models.rule import Rule, RuleHistory

__all__ = ["Application", "ApplicationDraft", "Family", "LegalParameter", "Rule", "RuleHistory"]
