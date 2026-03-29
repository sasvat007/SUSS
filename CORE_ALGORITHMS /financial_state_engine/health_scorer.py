"""
Health Scoring module for Financial State Engine.

Generates overall financial health score (0-100) and human-readable reasoning.
"""

from typing import Optional
from .models import HealthScoreBreakdown
from .metrics import (
    score_runway_component,
    score_obligation_pressure_component,
    score_receivable_quality_component,
    score_buffer_sufficiency_component,
    get_limiting_factor
)
from .utils import clamp


def compute_health_score(
    runway_days: Optional[int],
    pressure_ratio: float,
    quality_score: float,
    buffer_days: float,
    runway_weight: float = 0.40,
    pressure_weight: float = 0.35,
    quality_weight: float = 0.15,
    buffer_weight: float = 0.10
) -> tuple[int, HealthScoreBreakdown]:
    """
    Compute financial health score as weighted combination of components.
    
    Health Score = (40% × Runway) + (35% × Pressure) + (15% × Quality) + (10% × Buffer)
    
    Args:
        runway_days: Days until buffer breach (or None if stable)
        pressure_ratio: Obligation pressure ratio
        quality_score: Receivable quality (0.0-1.0)
        buffer_days: Buffer sufficiency in days
        runway_weight: Weight for runway component (default 0.40)
        pressure_weight: Weight for pressure component (default 0.35)
        quality_weight: Weight for quality component (default 0.15)
        buffer_weight: Weight for buffer component (default 0.10)
        
    Returns:
        Tuple of (health_score: int, breakdown: HealthScoreBreakdown)
    """
    # Calculate component scores
    runway_score = score_runway_component(runway_days)
    pressure_score = score_obligation_pressure_component(pressure_ratio)
    quality_component_score = score_receivable_quality_component(quality_score)
    buffer_score = score_buffer_sufficiency_component(buffer_days)
    
    # Verify weights sum to 1.0 (or close to it)
    total_weight = runway_weight + pressure_weight + quality_weight + buffer_weight
    if abs(total_weight - 1.0) > 0.001:
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    # Compute weighted score
    weighted_score = (
        runway_weight * runway_score +
        pressure_weight * pressure_score +
        quality_weight * quality_component_score +
        buffer_weight * buffer_score
    )
    
    # Clamp to 0-100 and round
    health_score = int(round(clamp(weighted_score, 0.0, 100.0)))
    
    # Create breakdown
    breakdown = HealthScoreBreakdown(
        runway_score=runway_score,
        obligation_pressure_score=pressure_score,
        receivable_quality_score=quality_component_score,
        buffer_sufficiency_score=buffer_score,
        runway_weight=runway_weight,
        pressure_weight=pressure_weight,
        quality_weight=quality_weight,
        buffer_weight=buffer_weight
    )
    
    return health_score, breakdown


def generate_health_reasoning(
    health_score: int,
    runway_days: Optional[int],
    pressure_ratio: float,
    quality_score: float,
    buffer_days: float,
    total_payables: float,
    available_cash: float,
    weighted_receivables: float
) -> str:
    """
    Generate human-readable explanation of health score.
    
    Identifies limiting factors and provides context-specific guidance.
    
    Args:
        health_score: Computed health score (0-100)
        runway_days: Days until buffer breach
        pressure_ratio: Obligation pressure ratio
        quality_score: Receivable quality
        buffer_days: Buffer sufficiency in days
        total_payables: Total payables within horizon
        available_cash: Available cash after buffer
        weighted_receivables: Confidence-weighted receivables
        
    Returns:
        Human-readable reasoning string
    """
    lines = []
    
    # Overall assessment
    if health_score >= 80:
        overall = "✓ Excellent: Strong financial position"
    elif health_score >= 60:
        overall = "→ Good: Stable financial position with manageable constraints"
    elif health_score >= 40:
        overall = "⚠ Caution: Financial position requires monitoring and planning"
    elif health_score >= 20:
        overall = "⚠⚠ Warning: Tight financial position; immediate action recommended"
    else:
        overall = "🔴 Critical: Severe financial constraints; urgent action required"
    
    lines.append(overall)
    lines.append("")
    
    # Identify limiting factor
    limiting = get_limiting_factor(runway_days, pressure_ratio, quality_score, buffer_days)
    
    # Detailed analysis
    details = []
    
    # Runway analysis
    if runway_days is None:
        details.append("• Runway: Stable within forecast horizon")
    elif runway_days >= 30:
        details.append(f"• Runway: {runway_days}+ days - Good runway ahead")
    elif runway_days >= 14:
        details.append(f"• Runway: ~{runway_days} days - Adequate runway")
    elif runway_days >= 7:
        details.append(f"• Runway: ~{runway_days} days - Monitor closely")
    elif runway_days >= 2:
        details.append(f"• Runway: ~{runway_days} days - Very limited time to act")
    else:
        details.append(f"• Runway: < 2 days - CRITICAL: Cash exhaustion imminent")
    
    # Pressure ratio analysis
    if pressure_ratio <= 0.5:
        details.append(f"• Obligation Pressure: Low ({pressure_ratio:.2f}) - Comfortable position")
    elif pressure_ratio <= 1.0:
        details.append(f"• Obligation Pressure: Moderate ({pressure_ratio:.2f}) - Manageable")
    elif pressure_ratio <= 2.0:
        details.append(f"• Obligation Pressure: High ({pressure_ratio:.2f}) - Stretched thin")
    elif pressure_ratio <= 3.0:
        details.append(f"• Obligation Pressure: Very High ({pressure_ratio:.2f}) - Very tight")
    else:
        details.append(f"• Obligation Pressure: Critical ({pressure_ratio:.2f}) - Obligations exceed resources")
    
    # Quality analysis
    if quality_score >= 0.8:
        details.append(f"• Receivable Quality: High ({quality_score:.2f}) - Reliable incoming cash")
    elif quality_score >= 0.6:
        details.append(f"• Receivable Quality: Good ({quality_score:.2f}) - Mostly reliable")
    elif quality_score >= 0.4:
        details.append(f"• Receivable Quality: Moderate ({quality_score:.2f}) - Some uncertainty")
    elif quality_score > 0:
        details.append(f"• Receivable Quality: Low ({quality_score:.2f}) - Significant uncertainty")
    else:
        details.append("• Receivable Quality: None - No incoming cash forecasted")
    
    # Buffer analysis
    if buffer_days == float('inf'):
        details.append("• Buffer Sufficiency: Indefinite - No outflow")
    elif buffer_days >= 10:
        details.append(f"• Buffer Sufficiency: {buffer_days:.1f} days - Solid cushion")
    elif buffer_days >= 5:
        details.append(f"• Buffer Sufficiency: {buffer_days:.1f} days - Adequate cushion")
    elif buffer_days >= 2:
        details.append(f"• Buffer Sufficiency: {buffer_days:.1f} days - Limited cushion")
    else:
        details.append(f"• Buffer Sufficiency: {buffer_days:.1f} days - Minimal cushion")
    
    lines.extend(details)
    lines.append("")
    
    # Limiting factor identification
    limiting_descriptions = {
        "runway": "Most critical: Cash runway is limited. Prioritize revenue or delay expenses.",
        "pressure": "Most critical: Obligations exceed available resources. Consider prioritizing payments.",
        "quality": "Most critical: Receivables are uncertain. Plan conservatively based on base scenario.",
        "buffer": "Most critical: Minimum buffer is inadequate to absorb shocks. Build reserves."
    }
    
    lines.append(f"Primary Concern: {limiting_descriptions.get(limiting, 'Mixed constraints')}")
    lines.append("")
    
    # Position summary
    lines.append("Position Summary:")
    lines.append(f"  • Available Cash: ₹{available_cash:,.2f}")
    lines.append(f"  • Total Payables: ₹{total_payables:,.2f}")
    lines.append(f"  • Weighted Receivables: ₹{weighted_receivables:,.2f}")
    lines.append(f"  • Net Position: ₹{(available_cash + weighted_receivables - total_payables):,.2f}")
    
    return "\n".join(lines)


def generate_health_status_flags(
    runway_days: Optional[int],
    pressure_ratio: float,
    quality_score: float,
    buffer_days: float,
    total_payables_due_now: float
) -> dict:
    """
    Generate boolean flags indicating risk conditions.
    
    Args:
        runway_days: Days until buffer breach
        pressure_ratio: Obligation pressure ratio
        quality_score: Receivable quality
        buffer_days: Buffer sufficiency in days
        total_payables_due_now: Payables due today or overdue
        
    Returns:
        Dictionary of status flags
    """
    flags = {
        "critical_runway": runway_days is not None and runway_days < 2,
        "limited_runway": runway_days is not None and runway_days < 7,
        "high_pressure": pressure_ratio > 2.0,
        "low_receivable_quality": quality_score < 0.5,
        "insufficient_buffer": buffer_days < 2.0,
        "has_overdue": total_payables_due_now > 0,
        "critical_status": health_score < 20 if 'health_score' in locals() else False
    }
    
    return flags
