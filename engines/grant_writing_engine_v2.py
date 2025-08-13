"""
GHOSTEAM GRANT WRITING PLATFORM - ENGINE V2.0
Enhanced with Real-World Learning Data from SAFE Grant Analysis
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

@dataclass
class FunderProfile:
    """Funder-specific preferences and constraints"""
    name: str
    typical_funding_range: Tuple[int, int]
    geographic_focus: str
    budget_style_preference: str  # "lean", "comprehensive", "contractor_focused"
    language_tone_preference: str  # "conservative", "ambitious", "technical"
    overhead_tolerance: float
    preferred_scope_scaling: str  # "focused", "moderate", "expansive"
    timeline_preference: str  # "standard", "extended", "accelerated"

@dataclass
class OrganizationProfile:
    """Organization capacity and service area constraints"""
    name: str
    current_service_areas: List[str]
    annual_budget: int
    staff_capacity: int
    proven_partnerships: Dict[str, str]  # partner_name: cost_structure
    historical_performance_metrics: Dict[str, float]
    expansion_risk_tolerance: str  # "low", "medium", "high"

class GrantWritingEngineV2:
    """
    Enhanced Grant Writing Engine with Real-World Learning Integration
    Incorporates SAFE grant gap analysis for improved accuracy
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.funder_profiles = self._load_funder_profiles()
        self.cost_database = self._load_cost_database()
        self.learning_patterns = self._load_learning_patterns()
        
    def _load_funder_profiles(self) -> Dict[str, FunderProfile]:
        """Load funder preference profiles"""
        return {
            "region_16_opioid_council": FunderProfile(
                name="Pikes Peak Region 16 Opioid Council",
                typical_funding_range=(70000, 90000),
                geographic_focus="El Paso County, Colorado",
                budget_style_preference="lean",
                language_tone_preference="conservative",
                overhead_tolerance=0.10,
                preferred_scope_scaling="focused",
                timeline_preference="standard"
            ),
            "weld_regional_opioid_council": FunderProfile(
                name="Weld Regional Opioid Council",
                typical_funding_range=(180000, 250000),
                geographic_focus="Weld County, Colorado",
                budget_style_preference="comprehensive",
                language_tone_preference="technical",
                overhead_tolerance=0.15,
                preferred_scope_scaling="moderate",
                timeline_preference="standard"
            )
        }
    
    def _load_cost_database(self) -> Dict[str, Dict]:
        """Load real partnership and service costs"""
        return {
            "polaris_pathways_training": {
                "cost_per_person": 650,
                "description": "COPA-approved peer specialist training",
                "duration": "60 hours over 8 weeks",
                "included": ["materials", "certification", "ongoing_support"]
            },
            "peer_specialist_hourly": {
                "cost_per_hour": 25,
                "description": "Certified peer specialist event staffing",
                "minimum_hours": 4,
                "travel_included": False
            },
            "translation_services": {
                "cost_per_hour": 50,
                "description": "Professional Spanish translation",
                "minimum_hours": 10,
                "includes_cultural_adaptation": True
            },
            "safe_app_platform": {
                "annual_cost": 1200,
                "nonprofit_discount": 0.30,
                "description": "Technology platform with 30% nonprofit discount",
                "features": ["participant_tracking", "resource_sharing", "outcome_measurement"]
            },
            "naloxone_kits": {
                "cost_per_kit": 10,
                "description": "Community naloxone distribution",
                "bulk_discount_threshold": 100,
                "bulk_discount_rate": 0.15
            }
        }
    
    def _load_learning_patterns(self) -> Dict[str, Dict]:
        """Load patterns from real grant analysis"""
        return {
            "budget_calibration": {
                "overestimate_factor": 3.03,  # Our demo was 3x too high
                "correct_scaling": {
                    "personnel_percentage": 0.57,  # Winner used 57% vs our 65%
                    "contractor_percentage": 0.31,  # Winner used 31% contractors
                    "operations_percentage": 0.10,  # Winner used 10% vs our 20%
                    "travel_percentage": 0.03,  # Winner separated travel costs
                }
            },
            "scope_scaling": {
                "participant_ratio": 0.86,  # Winner: 30 vs our 35 (30/35 = 0.86)
                "event_ratio": 0.50,  # Winner: 4 vs our 8 (4/8 = 0.50)
                "event_budget_ratio": 0.67,  # Winner: $500-1000 vs our $1000-1500
                "staffing_ratio": 0.625,  # Winner: 2.5 FTE vs our 4 FTE
            },
            "language_patterns": {
                "word_density_reduction": 0.40,  # Reduce verbosity by 40%
                "geographic_references": {
                    "correct_frequency": 20,  # "El Paso County" mentioned 20+ times
                    "incorrect_pattern": "expansion_language"
                },
                "funding_language": {
                    "preferred": ["request", "focused", "measurable", "realistic"],
                    "avoid": ["investment", "comprehensive", "transformative", "revolutionary"]
                }
            },
            "geographic_validation": {
                "same_county_risk": "low",
                "adjacent_county_risk": "medium",
                "new_county_risk": "high",
                "multi_county_risk": "very_high"
            }
        }
    
    def calibrate_budget(self, funder_id: str, org_profile: OrganizationProfile, 
                        initial_scope: Dict) -> Dict:
        """
        Calibrate budget based on funder capacity and real-world patterns
        
        Key Learning: Our demo was 3x overestimated - apply calibration factor
        """
        funder = self.funder_profiles.get(funder_id)
        if not funder:
            raise ValueError(f"Unknown funder: {funder_id}")
            
        # Get target budget range
        target_min, target_max = funder.typical_funding_range
        target_budget = (target_min + target_max) / 2
        
        # Apply learning patterns for budget structure
        patterns = self.learning_patterns["budget_calibration"]["correct_scaling"]
        
        calibrated_budget = {
            "total_budget": int(target_budget),
            "personnel": int(target_budget * patterns["personnel_percentage"]),
            "contractors": int(target_budget * patterns["contractor_percentage"]),
            "operations": int(target_budget * patterns["operations_percentage"]),
            "travel": int(target_budget * patterns["travel_percentage"]),
            "indirect": int(target_budget * funder.overhead_tolerance)
        }
        
        # Validate budget components
        calibrated_budget = self._validate_budget_components(calibrated_budget, funder)
        
        self.logger.info(f"Budget calibrated for {funder.name}: ${calibrated_budget['total_budget']:,}")
        return calibrated_budget
    
    def validate_geographic_scope(self, org_profile: OrganizationProfile, 
                                 proposed_areas: List[str]) -> Dict:
        """
        Validate geographic expansion against organizational capacity
        
        Key Learning: We proposed wrong county (Weld vs El Paso) - major error
        """
        validation_result = {
            "approved_areas": [],
            "flagged_areas": [],
            "risk_assessment": {},
            "recommendations": []
        }
        
        for area in proposed_areas:
            if area in org_profile.current_service_areas:
                validation_result["approved_areas"].append(area)
                validation_result["risk_assessment"][area] = "low"
            else:
                # Assess expansion risk
                risk_level = self._assess_expansion_risk(org_profile, area)
                validation_result["risk_assessment"][area] = risk_level
                
                if risk_level in ["high", "very_high"]:
                    validation_result["flagged_areas"].append(area)
                    validation_result["recommendations"].append(
                        f"Consider focusing on established service area ({org_profile.current_service_areas[0]}) instead of expanding to {area}"
                    )
                else:
                    validation_result["approved_areas"].append(area)
        
        return validation_result
    
    def scale_program_scope(self, budget: int, funder_id: str, 
                           initial_targets: Dict) -> Dict:
        """
        Scale program scope to realistic capacity based on budget
        
        Key Learning: Winner optimized for realistic delivery vs maximum impact
        """
        funder = self.funder_profiles.get(funder_id)
        scaling_patterns = self.learning_patterns["scope_scaling"]
        
        # Apply learned scaling ratios
        scaled_scope = {
            "participants": int(initial_targets.get("participants", 35) * scaling_patterns["participant_ratio"]),
            "events": int(initial_targets.get("events", 8) * scaling_patterns["event_ratio"]),
            "staffing_fte": initial_targets.get("staffing_fte", 4.0) * scaling_patterns["staffing_ratio"],
            "event_budget_per": int(initial_targets.get("event_budget_per", 1250) * scaling_patterns["event_budget_ratio"])
        }
        
        # Validate scope against budget constraints
        scaled_scope = self._validate_scope_feasibility(scaled_scope, budget, funder)
        
        # Add capacity warnings
        scaled_scope["capacity_warnings"] = []
        if scaled_scope["participants"] > 30:
            scaled_scope["capacity_warnings"].append("Consider reducing participants to 30 for focused delivery")
        if scaled_scope["events"] > 4:
            scaled_scope["capacity_warnings"].append("Consider reducing events to 4 for quality over quantity")
            
        return scaled_scope
    
    def optimize_language_tone(self, content: str, funder_id: str) -> str:
        """
        Optimize language tone based on funder preferences
        
        Key Learning: Conservative, realistic language wins over ambitious framing
        """
        funder = self.funder_profiles.get(funder_id)
        language_patterns = self.learning_patterns["language_patterns"]
        
        # Apply word density reduction (40% less verbose)
        content = self._reduce_word_density(content, language_patterns["word_density_reduction"])
        
        # Replace ambitious language with conservative alternatives
        replacements = {
            "transformative": "measurable",
            "revolutionary": "evidence-based",
            "comprehensive": "focused",
            "investment": "request",
            "groundbreaking": "proven",
            "innovative": "effective"
        }
        
        for ambitious_word, conservative_word in replacements.items():
            content = re.sub(rf'\b{ambitious_word}\b', conservative_word, content, flags=re.IGNORECASE)
        
        # Ensure conservative tone
        if funder.language_tone_preference == "conservative":
            content = self._apply_conservative_framing(content)
            
        return content
    
    def synchronize_timeline(self, grant_period_start: str, grant_period_end: str) -> Dict:
        """
        Synchronize project timeline with actual grant period
        
        Key Learning: We used wrong dates (2026 vs 2025) - must match RFP exactly
        """
        try:
            start_date = datetime.strptime(grant_period_start, "%Y-%m-%d")
            end_date = datetime.strptime(grant_period_end, "%Y-%m-%d")
        except ValueError:
            # Try alternative date formats
            for fmt in ["%m/%d/%Y", "%B %Y", "%Q %Y"]:
                try:
                    start_date = datetime.strptime(grant_period_start, fmt)
                    end_date = datetime.strptime(grant_period_end, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Unable to parse grant period dates")
        
        # Calculate project phases
        total_days = (end_date - start_date).days
        quarter_days = total_days // 4
        
        timeline = {
            "grant_period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "total_months": total_days // 30
            },
            "phases": {
                "q1": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": (start_date + timedelta(days=quarter_days)).strftime("%Y-%m-%d"),
                    "focus": "Foundation Building"
                },
                "q2": {
                    "start": (start_date + timedelta(days=quarter_days)).strftime("%Y-%m-%d"),
                    "end": (start_date + timedelta(days=quarter_days*2)).strftime("%Y-%m-%d"),
                    "focus": "Program Implementation"
                },
                "q3": {
                    "start": (start_date + timedelta(days=quarter_days*2)).strftime("%Y-%m-%d"),
                    "end": (start_date + timedelta(days=quarter_days*3)).strftime("%Y-%m-%d"),
                    "focus": "Program Expansion"
                },
                "q4": {
                    "start": (start_date + timedelta(days=quarter_days*3)).strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "focus": "Evaluation and Sustainability"
                }
            },
            "reporting_schedule": self._generate_reporting_schedule(start_date, end_date)
        }
        
        return timeline
    
    def generate_cost_breakdown(self, scope: Dict, funder_id: str) -> Dict:
        """
        Generate realistic cost breakdown using real partnership costs
        
        Key Learning: Use actual costs (Polaris $650/person) vs estimated costs
        """
        cost_breakdown = {
            "personnel": {},
            "contractors": {},
            "operations": {},
            "travel": {},
            "totals": {}
        }
        
        # Personnel costs (based on winning pattern: 57% of budget)
        participants = scope.get("participants", 30)
        events = scope.get("events", 4)
        
        # Use real costs from database
        training_cost = self.cost_database["polaris_pathways_training"]["cost_per_person"] * participants
        event_staffing_cost = (self.cost_database["peer_specialist_hourly"]["cost_per_hour"] * 
                              4 * events * 5)  # 4 peers x 4 events x 5 hours
        
        cost_breakdown["contractors"]["polaris_pathways_training"] = {
            "description": f"Peer specialist training for {participants} participants",
            "unit_cost": 650,
            "quantity": participants,
            "total": training_cost
        }
        
        cost_breakdown["contractors"]["event_staffing"] = {
            "description": f"Peer specialist staffing for {events} events",
            "unit_cost": 25,
            "hours": events * 4 * 5,
            "total": event_staffing_cost
        }
        
        # Technology platform
        platform_cost = int(self.cost_database["safe_app_platform"]["annual_cost"] * 
                           (1 - self.cost_database["safe_app_platform"]["nonprofit_discount"]))
        
        cost_breakdown["operations"]["technology_platform"] = {
            "description": "SAFE App platform (30% nonprofit discount)",
            "annual_cost": platform_cost,
            "total": platform_cost
        }
        
        # Calculate totals
        contractor_total = sum(item["total"] for item in cost_breakdown["contractors"].values())
        operations_total = sum(item["total"] for item in cost_breakdown["operations"].values())
        
        cost_breakdown["totals"] = {
            "contractors": contractor_total,
            "operations": operations_total,
            "grand_total": contractor_total + operations_total
        }
        
        return cost_breakdown
    
    def _assess_expansion_risk(self, org_profile: OrganizationProfile, new_area: str) -> str:
        """Assess risk level for geographic expansion"""
        current_areas = org_profile.current_service_areas
        
        # Simple risk assessment based on geographic proximity
        # In real implementation, this would use geographic data
        if any(area in new_area or new_area in area for area in current_areas):
            return "low"  # Same or adjacent area
        elif len(current_areas) == 1 and org_profile.expansion_risk_tolerance == "low":
            return "high"  # Conservative organization expanding
        else:
            return "medium"
    
    def _validate_budget_components(self, budget: Dict, funder: FunderProfile) -> Dict:
        """Validate budget components against funder preferences"""
        total = budget["total_budget"]
        
        # Check overhead tolerance
        if budget["indirect"] / total > funder.overhead_tolerance:
            budget["indirect"] = int(total * funder.overhead_tolerance)
            budget["warnings"] = ["Indirect costs reduced to meet funder tolerance"]
        
        # Ensure components sum correctly
        component_sum = sum(budget[key] for key in ["personnel", "contractors", "operations", "travel"])
        if component_sum != budget["total_budget"] - budget["indirect"]:
            # Adjust operations to balance
            budget["operations"] = budget["total_budget"] - budget["indirect"] - budget["personnel"] - budget["contractors"] - budget["travel"]
        
        return budget
    
    def _validate_scope_feasibility(self, scope: Dict, budget: int, funder: FunderProfile) -> Dict:
        """Validate scope feasibility against budget and funder preferences"""
        # Apply budget-based constraints
        if funder.preferred_scope_scaling == "focused":
            if scope["participants"] > 30:
                scope["participants"] = 30
                scope["scaling_note"] = "Participants limited to 30 for focused delivery"
            if scope["events"] > 4:
                scope["events"] = 4
                scope["scaling_note"] = "Events limited to 4 for quality focus"
        
        return scope
    
    def _reduce_word_density(self, content: str, reduction_factor: float) -> str:
        """Reduce word density by removing unnecessary qualifiers"""
        # Remove excessive adjectives and adverbs
        verbose_patterns = [
            r'\b(very|extremely|incredibly|absolutely|completely|totally)\s+',
            r'\b(comprehensive|extensive|significant|substantial)\s+',
            r'\s+(approach|strategy|methodology|framework)\b',
        ]
        
        for pattern in verbose_patterns:
            content = re.sub(pattern, ' ', content, flags=re.IGNORECASE)
        
        # Remove redundant phrases
        redundant_phrases = [
            "in order to",
            "it should be noted that",
            "it is important to",
            "we are pleased to"
        ]
        
        for phrase in redundant_phrases:
            content = content.replace(phrase, "")
        
        # Clean up extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _apply_conservative_framing(self, content: str) -> str:
        """Apply conservative, evidence-based framing"""
        # Replace superlative claims with measured statements
        conservative_replacements = {
            r"will dramatically": "will",
            r"will significantly": "will",
            r"major impact": "positive impact",
            r"groundbreaking": "proven",
            r"cutting-edge": "established",
            r"state-of-the-art": "effective"
        }
        
        for pattern, replacement in conservative_replacements.items():
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        return content
    
    def _generate_reporting_schedule(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Generate quarterly reporting schedule"""
        total_months = ((end_date.year - start_date.year) * 12 + 
                       end_date.month - start_date.month)
        
        reports = []
        for quarter in range(1, (total_months // 3) + 2):
            report_date = start_date + timedelta(days=90 * quarter)
            if report_date <= end_date:
                reports.append({
                    "quarter": quarter,
                    "due_date": report_date.strftime("%Y-%m-%d"),
                    "type": "Progress Report",
                    "focus": f"Q{quarter} outcomes and metrics"
                })
        
        # Add final report
        reports.append({
            "quarter": "Final",
            "due_date": (end_date + timedelta(days=30)).strftime("%Y-%m-%d"),
            "type": "Final Report",
            "focus": "Complete program evaluation and sustainability plan"
        })
        
        return reports

def main():
    """Test the enhanced grant writing engine"""
    engine = GrantWritingEngineV2()
    
    # Test organization profile
    safe_org = OrganizationProfile(
        name="SAFE (Sober Activities for Everyone)",
        current_service_areas=["El Paso County"],
        annual_budget=485000,
        staff_capacity=8,
        proven_partnerships={
            "Polaris Pathways": "$650/person training",
            "Serenity Connection Center": "Event partnership",
            "SafeSide Recovery": "Referral network"
        },
        historical_performance_metrics={
            "satisfaction_rate": 0.8276,
            "completion_rate": 0.75,
            "event_attendance": 47
        },
        expansion_risk_tolerance="medium"
    )
    
    # Test budget calibration
    calibrated_budget = engine.calibrate_budget(
        "region_16_opioid_council", 
        safe_org, 
        {"participants": 35, "events": 8}
    )
    print("Calibrated Budget:", json.dumps(calibrated_budget, indent=2))
    
    # Test geographic validation
    geo_validation = engine.validate_geographic_scope(
        safe_org, 
        ["El Paso County", "Weld County"]
    )
    print("Geographic Validation:", json.dumps(geo_validation, indent=2))
    
    # Test scope scaling
    scaled_scope = engine.scale_program_scope(
        81753,  # Actual winning budget
        "region_16_opioid_council",
        {"participants": 35, "events": 8, "staffing_fte": 4.0, "event_budget_per": 1250}
    )
    print("Scaled Scope:", json.dumps(scaled_scope, indent=2))

if __name__ == "__main__":
    main()
