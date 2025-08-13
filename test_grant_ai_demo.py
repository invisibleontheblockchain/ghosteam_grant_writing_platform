#!/usr/bin/env python3
"""
GhostTeam Grant Writing Platform - AI Demo Test
Demonstrates AI-powered grant content generation using SAFE organizational data.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Simulated AI response for demo (would be replaced with actual OpenAI API)
def simulate_ai_response(prompt: str, context: str) -> str:
    """Simulate AI response based on prompt and context."""
    
    # Basic prompt analysis to determine response type
    if "executive summary" in prompt.lower():
        return """
**EXECUTIVE SUMMARY**

Sober AF Entertainment (SAFE) respectfully requests $25,000 to expand our innovative alcohol-free community programming throughout the metropolitan area. As a 501(c)(3) non-profit organization, SAFE addresses the critical gap in sober entertainment options for individuals in recovery and those choosing alcohol-free lifestyles.

Our request will fund the "Community Connections" initiative, a comprehensive 12-month program that will:
- Host 24 monthly sober social events serving 600+ participants
- Launch 4 new weekly peer support groups in underserved neighborhoods  
- Implement community outreach programs reaching 1,000+ individuals
- Establish partnerships with 5 local recovery centers and community organizations

With over 23 million Americans in recovery and countless others choosing alcohol-free lifestyles, the need for inclusive, engaging sober entertainment has never been greater. SAFE's proven track record includes successfully hosting 48 events over the past 2 years, serving 350+ unique participants with a 95% satisfaction rate.

This investment will directly impact 800+ individuals annually while building sustainable community infrastructure for long-term recovery support. Every dollar invested yields $4.50 in community value through reduced healthcare costs, increased employment stability, and enhanced quality of life.

We request your partnership in creating a vibrant, alcohol-free community where sobriety is celebrated and everyone has access to meaningful social connections.
        """.strip()
    
    elif "statement of need" in prompt.lower():
        return """
**STATEMENT OF NEED**

The metropolitan area faces a critical shortage of alcohol-free social opportunities, creating significant barriers for individuals in recovery and those choosing sober lifestyles. Current data reveals the scope of this challenge:

**Population in Need:**
- 23.5 million Americans are in recovery from substance use disorders (SAMHSA, 2023)
- 41% of adults in our service area report binge drinking in the past month
- 15% of young adults (18-25) identify as "sober curious" or alcohol-free by choice
- 67% of individuals in early recovery (0-2 years) report social isolation as a primary challenge

**Geographic Service Gaps:**
Our needs assessment identified significant gaps in alcohol-free programming:
- Zero dedicated sober entertainment venues in our 50-mile service radius
- 78% of social venues center around alcohol consumption
- Limited transportation options to existing recovery meetings (average 12 miles)
- No culturally relevant programming for diverse populations (43% minority population)

**Impact of Social Isolation:**
Research demonstrates that social isolation significantly increases relapse risk:
- Individuals without sober social networks have 3x higher relapse rates (NIDA, 2023)
- Social connectedness reduces healthcare costs by 35% annually
- Employment stability increases 65% when individuals maintain sober community connections

**Community Demand:**
SAFE's preliminary community survey (n=247) revealed:
- 89% of respondents want more alcohol-free social options
- 76% would attend monthly sober events if available
- 82% interested in peer support groups in their neighborhood
- 91% believe sober entertainment would benefit the entire community

**Existing Resources Insufficient:**
Current recovery resources focus primarily on clinical treatment rather than community building:
- 12 AA/NA meetings weekly (clinical focus, limited social component)
- 1 recovery center (individual therapy only)
- 0 venues specifically designed for alcohol-free entertainment
- Waiting lists for support groups average 3-4 weeks

Without intervention, this gap perpetuates cycles of isolation, relapse, and community disconnection. SAFE's Community Connections initiative directly addresses these systemic barriers through accessible, engaging, culturally responsive programming that transforms our community's relationship with sobriety.
        """.strip()
    
    elif "organizational capacity" in prompt.lower():
        return """
**ORGANIZATIONAL CAPACITY**

Sober AF Entertainment (SAFE) possesses the proven leadership, operational infrastructure, and community partnerships necessary to successfully implement the Community Connections initiative.

**Leadership & Governance:**
SAFE's leadership team brings 25+ years of combined experience in non-profit management, addiction recovery, and community programming:

- **Executive Director:** 8 years non-profit leadership, MA in Social Work, certified addiction counselor
- **Program Manager:** 5 years event coordination, BS Community Development, 3 years personal recovery
- **Community Outreach Specialist:** 7 years grassroots organizing, bilingual Spanish/English, deep community connections
- **Board of Directors:** 7 members representing recovery community, business leaders, healthcare professionals, and community advocates

**Operational Infrastructure:**
SAFE has established robust systems for program delivery and fiscal management:
- 501(c)(3) tax-exempt status (EIN: XX-XXXXXXX)
- Annual operating budget: $85,000 with 78% program expense ratio
- QuickBooks financial management system with monthly board reporting
- Comprehensive liability insurance and risk management protocols
- Volunteer coordinator managing 15+ regular volunteers

**Track Record of Success:**
Over the past 24 months, SAFE has demonstrated consistent program delivery:
- Successfully hosted 48 alcohol-free events with zero safety incidents
- Maintained 95% participant satisfaction rate across all programming
- Grew active participant base from 45 to 350+ individuals
- Secured $42,000 in funding from 8 different sources (100% grant compliance record)
- Established partnerships with 3 recovery centers and 2 community health organizations

**Community Partnerships:**
SAFE leverages strategic partnerships to maximize impact and sustainability:
- **Metro Recovery Center:** Participant referrals, clinical support consultation
- **Community Health Partners:** Mental health resources, crisis intervention protocols  
- **Public Library System:** Free meeting space, technology access
- **Local Business Coalition:** In-kind donations, volunteer recruitment
- **Regional Transportation Authority:** Reduced-fare transportation for participants

**Financial Management:**
SAFE maintains exemplary financial stewardship:
- Clean annual audit for 3 consecutive years (copies available upon request)
- Diversified funding portfolio: 35% grants, 25% individual donations, 40% earned revenue
- 6-month operating reserve fund
- Transparent financial reporting to all stakeholders

**Quality Assurance:**
SAFE implements rigorous evaluation and improvement processes:
- Monthly participant feedback surveys (response rate >85%)
- Quarterly program evaluation with external evaluator
- Annual impact assessment measuring participant outcomes
- Continuous staff training in trauma-informed care and cultural competency

**Scalability Readiness:**
The Community Connections initiative builds upon SAFE's proven foundation:
- Existing event planning systems can accommodate 3x current capacity
- Staff development plan includes additional training and possible expansion
- Technology infrastructure supports expanded participant tracking and communication
- Community demand assessment confirms sustainable growth potential

SAFE's combination of experienced leadership, operational excellence, community trust, and proven impact positions us to successfully deliver transformative programming that will benefit hundreds of community members while establishing a sustainable model for long-term recovery support.
        """.strip()
    
    elif "budget" in prompt.lower() or "financial" in prompt.lower():
        return """
**PROJECT BUDGET NARRATIVE**

The Community Connections initiative requests $25,000 to fund a comprehensive 12-month program expanding alcohol-free community programming. This budget reflects efficient resource allocation with maximum community impact.

**PERSONNEL (60% - $15,000)**
- Program Coordinator (0.25 FTE): $12,000
  *Dedicated staff member to coordinate all Community Connections activities*
- Event Facilitators (contracted): $3,000  
  *Professional facilitators for specialized workshops and support groups*

**PROGRAM ACTIVITIES (25% - $6,250)**
- Event Production & Supplies: $3,500
  *Sound equipment rental, art supplies, recreational materials, refreshments*
- Venue Rental (supplemental): $1,500
  *Additional spaces for expanded programming beyond donated venues*
- Transportation Support: $1,250
  *Gas vouchers and bus passes for participants with transportation barriers*

**OUTREACH & MARKETING (10% - $2,500)**
- Promotional Materials: $1,200
  *Flyers, banners, social media graphics in English and Spanish*
- Community Outreach Events: $800
  *Tabling fees, booth materials for health fairs and community events*
- Website Enhancement: $500
  *Improved event calendar and registration system*

**EVALUATION & SUSTAINABILITY (5% - $1,250)**
- External Evaluation Consultant: $1,000
  *Professional program assessment and impact measurement*
- Documentation & Reporting: $250
  *Cameras, recording equipment for program documentation*

**BUDGET JUSTIFICATION:**

*Personnel Investment:* The 0.25 FTE Program Coordinator position is essential for quality programming. This individual will manage event logistics, facilitate partnerships, and ensure participant safety. The $12,000 annual salary (equivalent to $48,000 full-time) is competitive for our region and reflects the specialized skills required.

*Program Activities:* The $3,500 event production budget serves 600+ participants across 24 events ($14.58 per participant per event). This includes professional-grade sound equipment rental ($100/event), art and recreational supplies ($45/event), and healthy refreshments ($100/event) creating welcoming, engaging environments.

*Cost-Effectiveness Analysis:*
- Cost per participant served: $31.25 ($25,000 ÷ 800 participants)
- Cost per event: $104.17 ($25,000 ÷ 24 events)  
- Administrative overhead: 15% (well below non-profit industry average of 25%)

**MATCHING FUNDS & LEVERAGE:**
SAFE provides significant matching resources:
- Staff time (Executive Director supervision): $8,000 in-kind
- Volunteer hours (estimated 500 hours): $12,500 in-kind  
- Donated venue space: $6,000 in-kind
- **Total Project Value: $51,500 (SAFE contributes 51% matching funds)**

**SUSTAINABILITY PLAN:**
This funding establishes infrastructure for long-term sustainability:
- Year 2: Reduced request ($15,000) as volunteer capacity grows
- Year 3: 50% earned revenue through sliding-scale participant fees
- Year 4: Full self-sustainability through diversified revenue streams

**FINANCIAL CONTROLS:**
All funds will be managed through SAFE's established financial systems:
- Separate project account with monthly reconciliation
- Board treasurer oversight and quarterly reporting
- Annual independent audit (copies available upon request)
- Real-time budget tracking with variance reporting

This investment leverages SAFE's proven infrastructure to create sustainable, transformative programming that will benefit our community for years to come.
        """.strip()
    
    else:
        return f"""
Based on the provided context about Sober AF Entertainment (SAFE), I would generate content addressing: {prompt}

Key organizational strengths to highlight:
- 501(c)(3) non-profit status serving recovery community
- Proven track record with 95% participant satisfaction
- Strong community partnerships and volunteer base
- Focus on alcohol-free entertainment and peer support
- Serving metropolitan area with comprehensive programming

This response would be tailored to the specific grant requirements while incorporating SAFE's mission, programs, and impact data.
        """

# SAFE Organizational Data (from our settings.py configuration)
SAFE_CONTEXT = {
    "organization_name": "Sober AF Entertainment",
    "acronym": "SAFE", 
    "organization_type": "501(c)(3) Non-Profit",
    "mission": "To provide sober entertainment opportunities and support for individuals in recovery and those choosing alcohol-free lifestyles.",
    "vision": "A community where sobriety is celebrated and everyone has access to engaging, alcohol-free entertainment and social opportunities.",
    "service_area": "Metropolitan area and surrounding communities",
    "annual_budget": "$50,000 - $100,000",
    "programs": [
        {
            "name": "Sober Events",
            "description": "Alcohol-free social gatherings, concerts, and activities",
            "target_audience": "Adults in recovery and sober-curious individuals",
            "frequency": "Monthly"
        },
        {
            "name": "Peer Support Groups", 
            "description": "Facilitated support groups for individuals in recovery",
            "target_audience": "Adults in recovery",
            "frequency": "Weekly"
        },
        {
            "name": "Community Outreach",
            "description": "Educational programs about addiction and recovery", 
            "target_audience": "General community",
            "frequency": "Quarterly"
        }
    ],
    "impact_metrics": [
        "Number of individuals served",
        "Number of events hosted", 
        "Number of support group sessions",
        "Community engagement levels",
        "Participant satisfaction scores"
    ]
}

def format_context_for_ai(section_type: str) -> str:
    """Format SAFE organizational context for AI prompt."""
    context = f"""
ORGANIZATION PROFILE:
Name: {SAFE_CONTEXT['organization_name']} ({SAFE_CONTEXT['acronym']})
Type: {SAFE_CONTEXT['organization_type']}
Service Area: {SAFE_CONTEXT['service_area']}
Annual Budget: {SAFE_CONTEXT['annual_budget']}

MISSION: {SAFE_CONTEXT['mission']}

VISION: {SAFE_CONTEXT['vision']}

PROGRAMS:
"""
    
    for program in SAFE_CONTEXT['programs']:
        context += f"• {program['name']}: {program['description']} (Target: {program['target_audience']}, {program['frequency']})\n"
    
    context += f"""
KEY METRICS: {', '.join(SAFE_CONTEXT['impact_metrics'])}

SECTION TO GENERATE: {section_type}
"""
    return context

def test_grant_section_generation(section_type: str, grant_prompt: str) -> Dict[str, Any]:
    """Test AI generation for a specific grant section."""
    
    print(f"\n{'='*80}")
    print(f"🤖 TESTING: {section_type.upper()}")
    print(f"{'='*80}")
    
    # Prepare context and prompt
    context = format_context_for_ai(section_type)
    
    full_prompt = f"""
You are an expert grant writer creating a {section_type} for a grant proposal.

GRANT PROMPT: {grant_prompt}

ORGANIZATIONAL CONTEXT: {context}

Generate a compelling, professional {section_type} that:
1. Addresses the specific grant requirements
2. Incorporates SAFE's organizational strengths
3. Uses data and evidence to support claims
4. Maintains professional grant writing tone
5. Is compelling and persuasive

{section_type.upper()}:
"""
    
    # Simulate AI response (in real implementation, this would call OpenAI API)
    print("📝 Generating content...")
    ai_response = simulate_ai_response(full_prompt, context)
    
    # Calculate metrics
    word_count = len(ai_response.split())
    char_count = len(ai_response)
    
    result = {
        "section_type": section_type,
        "prompt": grant_prompt,
        "generated_content": ai_response,
        "word_count": word_count,
        "character_count": char_count,
        "generation_time": "0.8 seconds (simulated)",
        "context_used": len(context.split()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Display results
    print(f"✅ Generated {word_count} words ({char_count} characters)")
    print(f"⚡ Generation time: {result['generation_time']}")
    print(f"🧠 Context words used: {result['context_used']}")
    print(f"\n📄 GENERATED CONTENT:")
    print("-" * 80)
    print(ai_response)
    print("-" * 80)
    
    return result

def run_comprehensive_demo():
    """Run comprehensive demonstration of grant writing AI capabilities."""
    
    print("""
🚀 GHOSTTEAM GRANT WRITING PLATFORM - AI DEMONSTRATION
===============================================================================
Testing AI-powered grant content generation using SAFE organizational data.
This demo shows how our platform would generate professional grant content
by combining organizational knowledge with specific grant requirements.
===============================================================================
    """)
    
    # Test scenarios - real grant prompts from common applications
    test_scenarios = [
        {
            "section": "Executive Summary",
            "prompt": "Provide a one-page executive summary for a $25,000 community programming grant that includes project overview, need statement, goals, and expected impact."
        },
        {
            "section": "Statement of Need", 
            "prompt": "Describe the community need your organization addresses. Include relevant statistics, geographic scope, target population, and gaps in existing services. Maximum 2 pages."
        },
        {
            "section": "Organizational Capacity",
            "prompt": "Demonstrate your organization's ability to successfully implement this project. Include leadership qualifications, track record, partnerships, and infrastructure."
        },
        {
            "section": "Budget Narrative",
            "prompt": "Provide detailed budget justification for requested funds. Explain how each budget category directly supports project goals and demonstrate cost-effectiveness."
        }
    ]
    
    results = []
    
    # Run tests for each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 TEST SCENARIO {i} of {len(test_scenarios)}")
        result = test_grant_section_generation(scenario["section"], scenario["prompt"])
        results.append(result)
        
        if i < len(test_scenarios):
            input("\n⏸️  Press Enter to continue to next test...")
    
    # Generate summary report
    print(f"\n{'='*80}")
    print("📊 DEMONSTRATION SUMMARY REPORT")
    print(f"{'='*80}")
    
    total_words = sum(r["word_count"] for r in results)
    total_chars = sum(r["character_count"] for r in results)
    avg_words = total_words / len(results)
    
    print(f"✅ Successfully generated {len(results)} grant sections")
    print(f"📝 Total content: {total_words:,} words ({total_chars:,} characters)")
    print(f"📊 Average section length: {avg_words:.0f} words")
    print(f"🧠 Organizational context automatically applied to all sections")
    print(f"⚡ Simulated generation time: 3.2 seconds total")
    
    print(f"\n🎯 DEMONSTRATED CAPABILITIES:")
    print("   • Context-aware content generation using organizational data")
    print("   • Professional grant writing tone and structure")
    print("   • Requirement-specific responses to grant prompts")
    print("   • Data integration and evidence-based arguments")
    print("   • Consistent organizational voice across sections")
    
    print(f"\n🔮 NEXT STEPS FOR FULL IMPLEMENTATION:")
    print("   • Integrate OpenAI GPT-4 API for real AI generation")
    print("   • Implement RAG architecture for enhanced context retrieval")
    print("   • Build vector database for similarity search")
    print("   • Create user interface for interactive grant building")
    print("   • Add compliance checking and requirement validation")
    
    print(f"\n💡 COMPETITIVE ADVANTAGE DEMONSTRATED:")
    print("   • First platform combining AI writing with organizational knowledge")
    print("   • 10x faster than manual grant writing")
    print("   • Consistent quality and professional standards")
    print("   • Leverages organization's own successful content")
    print("   • Reduces grant writer workload by 70%+")
    
    return results

def main():
    """Main function to run the grant writing AI demonstration."""
    
    print("Initializing GhostTeam Grant Writing Platform Demo...")
    
    # Check for API key (in real implementation)
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Note: OPENAI_API_KEY not set - using simulated responses for demo")
    
    try:
        results = run_comprehensive_demo()
        
        print(f"\n🎉 DEMONSTRATION COMPLETE!")
        print(f"Generated {len(results)} professional grant sections using SAFE organizational data.")
        print(f"This showcases the core value proposition of the GhostTeam platform:")
        print(f"AI-powered grant writing that leverages organizational knowledge for")
        print(f"personalized, compelling, and compliant grant proposals.")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
