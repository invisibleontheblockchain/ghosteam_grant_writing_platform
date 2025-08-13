#!/usr/bin/env python3
"""
Grant Generator (V2 Engine)
Reads a source directory of materials, extracts text, and generates a complete
grant proposal using the v2 engine's calibrated budget, scope, tone, and timeline.
Outputs Markdown and JSON artifacts into generated_grants/.
"""

import argparse
import os
import sys
import json
import glob
from datetime import datetime
from typing import Dict, List

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engines.grant_writing_engine_v2 import GrantWritingEngineV2, OrganizationProfile

# Optional dependencies for document parsing
try:
    import PyPDF2  # type: ignore
except Exception:  # pragma: no cover
    PyPDF2 = None

try:
    import docx  # python-docx  # type: ignore
except Exception:  # pragma: no cover
    docx = None


def read_text_from_file(path: str) -> str:
    """Extract text from PDFs, DOCX, MD, and TXT files."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf" and PyPDF2:
            text_parts: List[str] = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    try:
                        text_parts.append(page.extract_text() or "")
                    except Exception:
                        continue
            return "\n".join(text_parts)
        elif ext in (".md", ".txt"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".docx" and docx:
            d = docx.Document(path)
            return "\n".join([p.text for p in d.paragraphs])
        else:
            return ""  # unsupported or missing parser
    except Exception:
        return ""


def read_corpus(input_dir: str) -> Dict[str, str]:
    """Read all supported files from input_dir and return a mapping of filename->text."""
    patterns = ["**/*.pdf", "**/*.md", "**/*.txt", "**/*.docx"]
    corpus: Dict[str, str] = {}
    for pattern in patterns:
        for path in glob.glob(os.path.join(input_dir, pattern), recursive=True):
            text = read_text_from_file(path)
            if text and text.strip():
                corpus[os.path.basename(path)] = text
    return corpus


def build_safe_org_profile() -> OrganizationProfile:
    """Create a default SAFE org profile for generation."""
    return OrganizationProfile(
        name="SAFE (Sober Activities for Everyone)",
        current_service_areas=["El Paso County"],
        annual_budget=485000,
        staff_capacity=8,
        proven_partnerships={
            "Polaris Pathways": "$650/person training",
            "Serenity Connection Center": "Event partnership",
            "SafeSide Recovery": "Referral network",
            "HardBeauty Foundation": "Family support services",
        },
        historical_performance_metrics={
            "satisfaction_rate": 0.8276,
            "completion_rate": 0.75,
            "event_attendance": 47,
            "participants_served": 281,
        },
        expansion_risk_tolerance="medium",
    )


def summarize_corpus(corpus: Dict[str, str], max_chars: int = 4000) -> str:
    """Make a lightweight concatenated summary from the corpus to seed narrative sections."""
    if not corpus:
        return ""
    # Take first N files lexicographically and clip to max_chars overall
    pieces: List[str] = []
    total = 0
    for fname in sorted(corpus.keys()):
        if total >= max_chars:
            break
        text = corpus[fname].strip()
        if not text:
            continue
        clip = text[: max_chars - total]
        pieces.append(f"--- {fname} ---\n{clip}")
        total += len(clip)
    return "\n\n".join(pieces)


def compose_sections(engine: GrantWritingEngineV2, funder_id: str, org: OrganizationProfile,
                      corpus_summary: str, budget: Dict, scope: Dict, timeline: Dict) -> Dict[str, str]:
    """Compose core grant sections and optimize tone via the engine."""
    funder_name = engine.funder_profiles[funder_id].name if funder_id in engine.funder_profiles else funder_id
    months = timeline.get("grant_period", {}).get("total_months", 12)
    area_str = "El Paso and Teller Counties" if funder_id == "region_16_opioid_council" else ", ".join(org.current_service_areas)

    def tone(s: str) -> str:
        return engine.optimize_language_tone(s, funder_id)

    exec_summary = f"""
Sober AF Entertainment (SAFE) respectfully requests ${budget['total_budget']:,} from {funder_name} to deliver a focused, evidence-based program serving {scope['participants']} participants across {scope['events']} events over {months} months in {area_str}.

SAFE will coordinate peer-supported sober activities, skills training, and resource navigation. The project emphasizes quality delivery, measurable outcomes, and alignment with {funder_name}'s priorities. Funds support personnel, essential contractors (e.g., Polaris Pathways peer specialist training), operations, and modest travel, with indirect costs within funder tolerance.
""".strip()

    need = f"""
Community members in our service area face barriers to sustained recovery, including limited alcohol-free social options, transportation challenges, and insufficient culturally responsive programming. The attached materials summarize local context, prior efforts, and lived-experience insights:

{corpus_summary or 'No external materials were provided; this proposal uses organizational data and validated patterns to ensure a realistic, targeted scope.'}

This project addresses isolation and relapse risk by building social connection and accessible sober events while maintaining conservative scope and verified capacity.
""".strip()

    description = f"""
Activities: Host {scope['events']} sober community events; enroll up to {scope['participants']} participants; coordinate peer specialist staffing; and provide referrals through established partners. Training costs use real rates (e.g., Polaris Pathways at $650/person). Technology platform costs reflect nonprofit discounting.

Staffing: Approximately {scope['staffing_fte']:.1f} FTE combined (program coordination, event staffing, administration).

Geography: Service area covers El Paso County with scheduled outreach in Teller County via partner sites to ensure equitable access across Region 16; cadence and locations are reflected in the timeline.

Timeline: See quarterly phases and reporting in the timeline section.
""".strip()

    goals = f"""
- Serve up to {scope['participants']} unique participants with at least 75% completing planned engagements.
- Deliver {scope['events']} sober events with pre/post brief check-ins and incident-free operations.
- Achieve ≥80% participant satisfaction based on post-event surveys.
- Establish or strengthen at least 3 operational partnerships that improve referrals and retention.
- Maintain indirect costs ≤ {int(100 * engine.funder_profiles[funder_id].overhead_tolerance)}% and adhere to budget calibration.
""".strip()

    evaluation = f"""
- Data collection: Participant sign-ins, attendance counts, brief surveys, referral tracking.
- Quarterly reviews: Compare outcomes to targets; incorporate recommendations; document lessons learned.
- Reporting: Submit progress reports per schedule; compile final evaluation summarizing outcomes and sustainability preparations.

Reporting schedule:
{json.dumps(timeline.get('reporting_schedule', []), indent=2)}
""".strip()

    budget_narrative = f"""
Total request: ${budget['total_budget']:,}
- Personnel: ${budget['personnel']:,}
- Contractors: ${budget['contractors']:,}
- Operations: ${budget['operations']:,}
- Travel: ${budget['travel']:,}
- Indirect (within tolerance): ${budget['indirect']:,}

Contracted services include peer specialist training (~$650/person) and event staffing using validated hourly rates. Operations include technology platform fees with nonprofit discounts. Structure reflects calibrated percentages observed in successful proposals.
""".strip()

    capacity = f"""
SAFE maintains proven delivery capacity with experienced staff, established partnerships (e.g., Polaris Pathways, Serenity Connection Center, SafeSide Recovery), and appropriate financial controls. Historical performance metrics include participant satisfaction near 83% and consistent event attendance. Expansion risk is managed by focusing on existing counties and verified partnerships.
""".strip()

    sustainability = f"""
The model prioritizes lean operations and tested partnerships. Sustainability strategies include diversified funding, in-kind venue support, volunteer engagement, and measured growth based on outcomes. Lessons learned inform year-two right-sizing and potential earned-revenue pilots.
""".strip()

    conclusion = f"""
This request aligns with {funder_name}'s priorities and reflects a realistic plan supported by validated costs, capacity, and scope. SAFE will deliver measurable, participant-centered outcomes within a conservative budget and clear reporting cadence.
""".strip()

    sections = {
        "Executive Summary": tone(exec_summary),
        "Statement of Need": tone(need),
        "Project Description": tone(description),
        "Goals and Objectives": tone(goals),
        "Evaluation Plan": tone(evaluation),
        "Budget Narrative": tone(budget_narrative),
        "Organizational Capacity": tone(capacity),
        "Sustainability Plan": tone(sustainability),
        "Conclusion": tone(conclusion),
    }
    return sections


def build_winning_template_md(org: OrganizationProfile, funder_id: str, sections: Dict[str, str], budget: Dict, scope: Dict, timeline: Dict) -> str:
    months = timeline.get("grant_period", {}).get("total_months", 12)
    service_areas = "El Paso and Teller Counties" if funder_id == "region_16_opioid_council" else ", ".join(org.current_service_areas)
    program_name = f"SAFE Focused Sober Activities — {service_areas}"
    funding_request = f"${budget['total_budget']:,} over {months} months"
    target_population = f"{scope.get('participants', 30)} residents in {service_areas}"

    personnel_pct = int(round(100 * budget["personnel"] / budget["total_budget"])) if budget.get("total_budget") else 0
    contractors_pct = int(round(100 * budget["contractors"] / budget["total_budget"])) if budget.get("total_budget") else 0
    operations_pct = int(round(100 * budget["operations"] / budget["total_budget"])) if budget.get("total_budget") else 0
    travel_pct = int(round(100 * budget["travel"] / budget["total_budget"])) if budget.get("total_budget") else 0
    indirect_pct = int(round(100 * budget["indirect"] / budget["total_budget"])) if budget.get("total_budget") else 0

    # Partnerships table
    partners_rows = []
    for name, contribution in org.proven_partnerships.items():
        partners_rows.append(f"| {name} | Partner | {contribution} | Existing |")
    partners_table = "\n".join([
        "| Partner Name | Role | Contribution | MOU Status |",
        "|--------------|------|--------------|------------|",
        *(partners_rows or ["| - | - | - | - |"])
    ])

    # Timeline (mapped to template cadence)
    timeline_md = []
    timeline_md.append("**Year 1** (or Grant Period)\n")
    timeline_md.append("**Month 1-2**: Program Launch")
    timeline_md.append("- [ ] Stakeholder meetings")
    timeline_md.append("- [ ] Hire/train staff")
    timeline_md.append("- [ ] Develop materials")
    timeline_md.append("- [ ] Community outreach\n")
    timeline_md.append("**Month 3-6**: Initial Implementation")
    timeline_md.append("- [ ] First events")
    timeline_md.append("- [ ] Begin peer training")
    timeline_md.append("- [ ] Establish partnerships")
    timeline_md.append("- [ ] Baseline data collection\n")
    timeline_md.append("**Month 7-9**: Full Implementation")
    timeline_md.append("- [ ] All events running")
    timeline_md.append("- [ ] Peer specialists active")
    timeline_md.append("- [ ] Mid-point evaluation")
    timeline_md.append("- [ ] Adjustments based on feedback\n")
    timeline_md.append("**Month 10-12**: Sustainability & Evaluation")
    timeline_md.append("- [ ] Final events")
    timeline_md.append("- [ ] Comprehensive evaluation")
    timeline_md.append("- [ ] Reporting")
    timeline_md.append("- [ ] Planning for continuation\n")
    timeline_block = "\n".join(timeline_md)

    # Build the markdown in the same structure as the template
    md_parts: List[str] = []

    md_parts.append("### 1. EXECUTIVE SUMMARY")
    md_parts.append(f"**Program Name**: {program_name}\n")
    md_parts.append(f"**Funding Request**: {funding_request}\n")
    md_parts.append(f"**Brief Description**: {sections.get('Executive Summary','')}\n")
    md_parts.append(f"**Target Population**: {target_population}\n")
    md_parts.append("**Key Activities**:\n- Sober community events\n- Peer specialist staffing and training\n- Resource navigation and referrals\n")
    md_parts.append("---\n\n### RFP COMPLIANCE MATRIX (Region 16 Opioid Abatement Grant)")
    md_parts.append("**Alignment with Scopes of Work (SOWs)**:")
    md_parts.append("- Selected Scopes: Community Prevention, Education, and Awareness; Recovery Supports and Transitions")
    md_parts.append("- Mapping: Sober events and outreach = community prevention/awareness; Peer specialists, navigation, and transitions support = recovery supports and transitions")
    md_parts.append("**Target Population and Equity**:")
    md_parts.append("- Coverage: El Paso and Teller Counties across age groups, identities, languages")
    md_parts.append("- Strategies: Spanish translation, rural pop-up events in Teller and Southeast El Paso, accessibility accommodations, justice-involved reentry coordination")
    md_parts.append("**Special Consideration Populations**:")
    md_parts.append("- Unhoused: Outreach via shelter/encampment partners and flexible event sites")
    md_parts.append("- Rural: Quarterly events in Teller County; partner-hosted sites; mobile access")
    md_parts.append("- Justice-involved: Coordination with detention discharge planners and reentry navigators")
    md_parts.append("**RFP Milestones and Submission Plan**:")
    md_parts.append("- Application launch: Nov 22, 2024")
    md_parts.append("- Questions deadline: Dec 13, 2024 @ 10:00 AM")
    md_parts.append("- Responses published: Jan 10, 2025")
    md_parts.append("- Application due: Jan 31, 2025 @ 10:00 AM")
    md_parts.append("- Council review: Feb 26, 2025; Presentations: Mar 26, 2025; Awards: Mar 2025")
    md_parts.append("- Program start: Target 2025-04-01; end: 2026-03-31 (timeline and reporting synchronized)")
    md_parts.append("**Evaluation Criteria Mapping (weights in brackets)**:")
    md_parts.append("- Alignment with SOW [30]: Objectives directly map to selected scopes; clear service plan across Region 16")
    md_parts.append("- Organizational Experience [10]: SAFE track record in sober events, partnerships, and recovery supports")
    md_parts.append("- Cost Proposal [10]: Budget calibrated to funder range with transparent justifications")
    md_parts.append("- Project Sustainability [25]: Diversified funding and partner/in-kind supports")
    md_parts.append("- Evaluation Proposal [25]: KPIs, data collection methods, quarterly reviews, final evaluation")

    md_parts.append("---\n\n### 2. ORGANIZATION INFORMATION")
    md_parts.append("**Organization Name**: Sober AF Entertainment\n")
    md_parts.append("**Mission Statement**: [Use standard mission from knowledge base]\n")
    md_parts.append("**Tax ID/EIN**: 83-0685262\n")
    md_parts.append("**Founded**: 2018\n")
    md_parts.append(f"**Current Operating Budget**: ${org.annual_budget:,}\n")
    md_parts.append("**Contact Information**:\n- Primary: Daniel Rumely, duke@soberafe.com, 303-888-9019\n- Secondary: Louis Piotti, lou@soberafe.com, 215-407-5123\n")
    md_parts.append("**Board & Staff Demographics**: [Update with current numbers]\n")

    md_parts.append("---\n\n### 3. NEEDS ASSESSMENT")
    md_parts.append("**Problem Statement**:\n- Limited alcohol-free social options\n- Transportation and access barriers\n- Need for culturally responsive programming\n- Alignment with local public health priorities\n")
    md_parts.append("**Supporting Data**:\n")
    need_src = sections.get("Statement of Need", "")
    md_parts.append(f"{need_src}\n")
    md_parts.append("**Root Causes**:\n- Social isolation\n- Environmental factors\n- Systemic barriers\n- Cultural considerations\n")

    md_parts.append("---\n\n### 4. PROGRAM DESCRIPTION")
    md_parts.append("**Program Overview**:\n")
    md_parts.append(f"{sections.get('Project Description','')}\n")
    md_parts.append("**Core Components**:\n")
    md_parts.append(f"1. **Sober Events/Tailgates**\n   - Number: {scope.get('events',4)} events\n   - Duration: 3-5 hours typical\n   - Expected attendance: ~{max(1, int(scope.get('participants',30)/max(1, scope.get('events',4))))} per event\n")
    md_parts.append(f"2. **Peer Support Services**\n   - Number of specialists: [Based on staffing FTE ~ {scope.get('staffing_fte',2.5):.1f}]\n   - Training: COPA-approved (Polaris Pathways at ~$650/person)\n   - Certification: Maintained and verified\n")
    md_parts.append("3. **Harm Reduction Education**\n   - Naloxone distribution target: [contextual to funder]\n   - Training sessions: [count]\n   - Educational materials: [summary]\n")
    md_parts.append("**Innovation & Uniqueness**:\n- Lived experience leadership\n- Cultural relevance focus\n- Data-driven and conservative scope\n")

    md_parts.append("---\n\n### 5. GOALS, OBJECTIVES & OUTCOMES")
    md_parts.append("**Goal 1**: Deliver focused, measurable sober activities\n- Objective 1.1: Host planned events on schedule\n  - Outcome: 100% of planned events delivered\n  - Indicator: Event logs and attendance\n- Objective 1.2: Maintain participant satisfaction ≥80%\n  - Outcome: Achieve target satisfaction\n  - Indicator: Post-event surveys\n")
    md_parts.append("**Goal 2**: Strengthen peer support and partnerships\n- Objective 2.1: Train and deploy peer specialists\n  - Outcome: Specialists active at events\n  - Indicator: Staffing rosters\n")
    md_parts.append(f"\nFrom engine:\n{sections.get('Goals and Objectives','')}\n")

    md_parts.append("---\n\n### 6. IMPLEMENTATION TIMELINE\n")
    md_parts.append(timeline_block)
    md_parts.append("\n> Engine-synchronized timeline data\n")
    md_parts.append("```json\n" + json.dumps(timeline, indent=2) + "\n```")

    md_parts.append("---\n\n### 7. TARGET POPULATION")
    md_parts.append("**Primary Population**:\n- Demographics: [students/young adults/peers]\n- Geographic location: " + service_areas + "\n- Characteristics: [in or seeking recovery]\n")
    md_parts.append("**Numbers Served**:\n- Unduplicated individuals: " + str(scope.get("participants", 30)) + "\n- Total contacts/services: [estimate]\n- By demographic category: [breakdown]\n")
    md_parts.append("**Recruitment & Outreach**:\n- Methods: events, partner referrals, social\n- Partners: see partnerships\n- Accessibility: venues, translation as needed\n")

    md_parts.append("---\n\n### 8. PARTNERSHIPS\n")
    md_parts.append("**Lead Organization**: Sober AF Entertainment\n\n**Key Partners**:\n")
    md_parts.append(partners_table + "\n")
    md_parts.append("**Letters of Support From**:\n- [List organizations]\n")

    md_parts.append("---\n\n### 9. EVALUATION PLAN")
    md_parts.append("**Evaluation Design**:\n- Process and outcome evaluation with quarterly reviews\n- Responsible: Internal with partner input\n")
    md_parts.append("**Data Collection Methods**:\n- Pre/post surveys, sign-ins, QR feedback, partner input\n- Resource distribution logs\n")
    md_parts.append("**Key Performance Indicators**:\n1. Number of events\n2. Total attendance\n3. Participant satisfaction\n4. Peer specialists trained\n5. Referrals completed\n")
    md_parts.append("**Data Management**:\n- Secure storage and regular analysis\n- Reporting aligned to funder cadence\n")
    md_parts.append("**Continuous Improvement**:\n- Monthly team reviews\n- Quarterly stakeholder reviews\n")
    md_parts.append(f"\nFrom engine:\n{sections.get('Evaluation Plan','')}\n")

    md_parts.append("---\n\n### 10. BUDGET NARRATIVE")
    md_parts.append(f"**Total Program Budget**: ${budget['total_budget']:,}\n")
    md_parts.append(f"**Personnel ({personnel_pct}% of budget)**: ${budget['personnel']:,}\n")
    md_parts.append(f"**Contractors ({contractors_pct}% of budget)**: ${budget['contractors']:,}\n")
    md_parts.append(f"**Program/Operations ({operations_pct}% of budget)**: ${budget['operations']:,}\n")
    md_parts.append(f"**Travel ({travel_pct}% of budget)**: ${budget['travel']:,}\n")
    md_parts.append(f"**Indirect Costs ({indirect_pct}%)**: ${budget['indirect']:,}\n")
    md_parts.append(f"\nFrom engine:\n{sections.get('Budget Narrative','')}\n")

    md_parts.append("---\n\n### 11. SUSTAINABILITY PLAN\n")
    md_parts.append(sections.get("Sustainability Plan", "") + "\n")

    md_parts.append("---\n\n### 12. ORGANIZATIONAL CAPACITY\n")
    md_parts.append(sections.get("Organizational Capacity", "") + "\n")

    md_parts.append("---\n\n### 13. APPENDICES")
    md_parts.append("**Standard Attachments**:\n- [ ] Budget form (funder template)\n- [ ] Board list\n- [ ] Org chart\n- [ ] Financials\n- [ ] IRS determination letter\n- [ ] Letters of support\n- [ ] Evaluation instruments\n- [ ] Staff resumes/bios\n")
    md_parts.append("**Optional Attachments**:\n- [ ] Media coverage\n- [ ] Photos\n- [ ] Testimonials\n- [ ] Research citations\n- [ ] Previous evaluation reports\n")

    return "\n".join(md_parts)


def write_outputs(out_dir: str, funder_id: str, sections: Dict[str, str], budget: Dict, scope: Dict, timeline: Dict, output_format: str = "standard") -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = os.path.join(out_dir, f"grant_{funder_id}_{ts}.md")
    json_path = os.path.join(out_dir, f"grant_{funder_id}_{ts}.json")

    with open(md_path, "w", encoding="utf-8") as f:
        if output_format == "winning_template":
            md_content = build_winning_template_md(build_safe_org_profile(), funder_id, sections, budget, scope, timeline)
            f.write(md_content)
        else:
            f.write(f"# Grant Proposal ({funder_id})\n\n")
            for title, content in sections.items():
                f.write(f"## {title}\n\n{content}\n\n")
            f.write("## Timeline\n\n")
            f.write(json.dumps(timeline, indent=2))
            f.write("\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"sections": sections, "budget": budget, "scope": scope, "timeline": timeline}, f, indent=2)

    return {"markdown": md_path, "json": json_path}


def main():
    parser = argparse.ArgumentParser(description="Generate a grant using the V2 engine from a source folder of materials.")
    parser.add_argument("--input-dir", required=False, default="", help="Path to the folder with source materials (PDF/DOCX/MD/TXT). Can be outside the repo.")
    parser.add_argument("--funder", required=True, choices=[
        "region_16_opioid_council",
        "weld_regional_opioid_council",
    ], help="Funder profile to target.")
    parser.add_argument("--start-date", required=False, default="", help="Grant period start date (YYYY-MM-DD). If omitted, defaults to first of next month.")
    parser.add_argument("--end-date", required=False, default="", help="Grant period end date (YYYY-MM-DD). If omitted, defaults to 12 months after start.")
    parser.add_argument("--out-dir", required=False, default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated_grants"),
                        help="Output directory for generated artifacts.")
    parser.add_argument("--participants", type=int, default=35, help="Initial target participants before scaling.")
    parser.add_argument("--events", type=int, default=8, help="Initial target events before scaling.")
    parser.add_argument("--format", dest="output_format", choices=["standard", "winning_template"], default="winning_template",
                        help="Output format for the Markdown artifact.")

    args = parser.parse_args()

    engine = GrantWritingEngineV2()
    org = build_safe_org_profile()

    # Gather input corpus (will work for external paths at runtime on user's machine)
    corpus = read_corpus(args.input_dir) if args.input_dir else {}
    corpus_summary = summarize_corpus(corpus)

    # Dates and timeline
    if args.start_date and args.end_date:
        timeline = engine.synchronize_timeline(args.start_date, args.end_date)
    else:
        # Default: next month start, +12 months
        today = datetime.today()
        next_month = 1 if today.month == 12 else today.month + 1
        year = today.year + 1 if next_month == 1 else today.year
        start = f"{year}-{next_month:02d}-01"
        end_year = year + (1 if next_month != 1 else 0)
        end_month = next_month - 1 if next_month != 1 else 12
        end = f"{end_year}-{end_month:02d}-28"  # rough month-end
        timeline = engine.synchronize_timeline(start, end)

    # Budget and scope
    initial_scope = {"participants": args.participants, "events": args.events, "staffing_fte": 4.0, "event_budget_per": 1250}
    budget = engine.calibrate_budget(args.funder, org, initial_scope)
    scope = engine.scale_program_scope(budget["total_budget"], args.funder, initial_scope)

    # Compose sections and write optimized outputs
    sections = compose_sections(engine, args.funder, org, corpus_summary, budget, scope, timeline)
    paths = write_outputs(args.out_dir, args.funder, sections, budget, scope, timeline, args.output_format)

    print(json.dumps({
        "status": "success",
        "output": paths,
        "files_parsed": list(corpus.keys())[:10],
        "files_parsed_count": len(corpus),
    }, indent=2))


if __name__ == "__main__":
    main()
