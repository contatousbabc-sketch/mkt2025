"""
ARQV30 Enhanced v3.0 - External AI Verification Module
Independent AI verification module for content analysis and validation
"""

__version__ = "3.0.0"
__author__ = "Manus AI"
__description__ = "External AI Verification Module for ARQV30 Enhanced"

from .external_review_agent import run_external_review, ExternalReviewAgent

__all__ = ['run_external_review', 'ExternalReviewAgent']