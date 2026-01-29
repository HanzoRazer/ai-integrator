"""Coaching module for Smart Guitar design intelligence.

This module provides design coaching capabilities for ai-integrator.
The coaching layer translates user intent into optimized parameters
for AI generation.

IMPORTANT: Coaching provides PARAMETERS, not DECISIONS.
RMOS accepts or rejects these parameters.
"""

from ai_integrator.coaching.image_coach import (
    ImageCoach,
    DesignContext,
    GuitarComponent,
    WoodType,
    FinishType,
    StyleEra,
)

__all__ = [
    "ImageCoach",
    "DesignContext",
    "GuitarComponent",
    "WoodType",
    "FinishType",
    "StyleEra",
]

