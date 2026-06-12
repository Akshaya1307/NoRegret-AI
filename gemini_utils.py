from google import genai
import os
import re
import streamlit as st

# ============ FIXED: API Key Loading ============
# Try multiple ways to get the API key
GEMINI_API_KEY = None

# Method 1: Try Streamlit secrets
try:
    if hasattr(st, 'secrets') and st.secrets:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            print("✅ API Key loaded from Streamlit secrets")
except Exception as e:
    print(f"Error loading from secrets: {e}")

# Method 2: Try environment variable
if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        print("✅ API Key loaded from environment variable")

# Method 3: Hardcoded fallback (ONLY FOR TESTING - remove later)
if not GEMINI_API_KEY:
    # DON'T hardcode your key here in production!
    # This is just to test if API works
    print("❌ No API key found in secrets or environment")

# Initialize Gemini Client
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    print("❌ Gemini client not initialized - missing API key")

def check_eligibility_with_ai(profile, opportunity):
    # Check if client is available
    if client is None:
        return f"""
ELIGIBILITY_SCORE: 0

ELIGIBLE: No

REASON:
Gemini API client not initialized. API key is missing.

STRENGTHS:
None

MISSING_SKILLS:
None

RECOMMENDATION:
Please add GEMINI_API_KEY to Streamlit Cloud secrets.

NEXT_STEPS:
1. Go to share.streamlit.io
2. Click 'Manage app' → 'Settings' → 'Secrets'
3. Add: GEMINI_API_KEY = 'your_key_here'
4. Redeploy the app
"""

    prompt = f"""
You are NoRegret AI, an intelligent career opportunity advisor.

Analyze the student's profile against the opportunity and provide a detailed evaluation.

STUDENT PROFILE:
- Name: {profile.get('name', 'N/A')}
- CGPA: {profile.get('cgpa', 'N/A')} out of 10
- Degree: {profile.get('degree', 'N/A')}
- Graduation Year: {profile.get('grad_year', 'N/A')}
- Skills: {', '.join(profile.get('skills', []))}
- Interests: {', '.join(profile.get('interests', []))}

OPPORTUNITY:
- Title: {opportunity.get('title', 'N/A')}
- Type: {opportunity.get('type', 'N/A')}
- Minimum CGPA Required: {opportunity.get('min_cgpa', 'N/A')}
- Eligible Degrees: {', '.join(opportunity.get('eligible_degrees', []))}
- Required Skills: {', '.join(opportunity.get('required_skills', []))}
- Deadline: {opportunity.get('deadline', 'N/A')}
- Description: {opportunity.get('description', 'N/A')}

Evaluate the student strictly.

IMPORTANT:
Follow the format exactly.
Do not change field names.
Do not omit any field.
Always provide a numeric ELIGIBILITY_SCORE.
Be SPECIFIC about which skills are missing from the Required Skills list.

Respond EXACTLY like this:

ELIGIBILITY_SCORE: 85

ELIGIBLE: Yes

REASON:
Explanation here

STRENGTHS:
Strength 1, Strength 2

MISSING_SKILLS:
Skill 1, Skill 2, Skill 3

RECOMMENDATION:
Advice here

NEXT_STEPS:
Action plan here

Rules:
1. Be strict with CGPA requirements.
2. Be strict with required skills.
3. Be strict with degree requirements unless "Any" is listed.
4. Calculate a realistic eligibility score.
5. If the student is missing ANY required skills, list them explicitly in MISSING_SKILLS.
6. If no skills are missing, write "None" in MISSING_SKILLS.
7. Give practical, actionable recommendations.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        print("\n===== GEMINI RESPONSE =====")
        print(response.text)
        print("===========================\n")

        return response.text

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Gemini API Error: {error_msg}")
        
        return f"""
ELIGIBILITY_SCORE: 0

ELIGIBLE: No

REASON:
Gemini API error: {error_msg}

STRENGTHS:
None

MISSING_SKILLS:
None

RECOMMENDATION:
Check your Gemini API key and billing status.

NEXT_STEPS:
1. Verify API key is correct
2. Enable billing at https://console.cloud.google.com/
3. Check API quotas at https://ai.google.dev/
"""


def parse_ai_response(response_text):
    result = {
        'score': '0',
        'eligible': 'No',
        'reason': '',
        'strengths': '',
        'missing_skills': [],
        'recommendation': '',
        'next_steps': ''
    }

    lines = response_text.strip().split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # SCORE
        if line.startswith("ELIGIBILITY_SCORE:"):
            match = re.search(r'\d+', line)
            if match:
                result['score'] = match.group()

        # ELIGIBLE
        elif line.startswith("ELIGIBLE:"):
            result['eligible'] = (
                "Yes"
                if "yes" in line.lower()
                else "No"
            )

        # REASON
        elif line.startswith("REASON:"):
            current_section = "reason"
            result['reason'] = ""

        # STRENGTHS
        elif line.startswith("STRENGTHS:"):
            current_section = "strengths"
            result['strengths'] = ""

        # MISSING SKILLS
        elif line.startswith("MISSING_SKILLS:"):
            current_section = "missing_skills"

            skills_text = (
                line.replace("MISSING_SKILLS:", "")
                .strip()
            )

            if skills_text and skills_text.lower() != "none":
                result['missing_skills'] = [
                    s.strip()
                    for s in skills_text.split(',')
                    if s.strip()
                ]

        # RECOMMENDATION
        elif line.startswith("RECOMMENDATION:"):
            current_section = "recommendation"
            result['recommendation'] = ""

        # NEXT STEPS
        elif line.startswith("NEXT_STEPS:"):
            current_section = "next_steps"
            result['next_steps'] = ""

        else:
            if current_section == "reason":
                result['reason'] += line + " "
            elif current_section == "strengths":
                result['strengths'] += line + " "
            elif current_section == "missing_skills":
                if line.lower() != "none":
                    extra_skills = [
                        s.strip()
                        for s in line.split(',')
                        if s.strip()
                    ]
                    result['missing_skills'].extend(extra_skills)
            elif current_section == "recommendation":
                result['recommendation'] += line + " "
            elif current_section == "next_steps":
                result['next_steps'] += line + " "

    result['reason'] = result['reason'].strip()
    result['strengths'] = result['strengths'].strip()
    result['recommendation'] = result['recommendation'].strip()
    result['next_steps'] = result['next_steps'].strip()

    result['missing_skills'] = list(
        set(result['missing_skills'])
    )

    return result


def rank_opportunities(profile, opportunities):
    """
    Rank opportunities from best match to worst match using Gemini AI
    """
    
    # Check if client is available
    if client is None:
        return "⭐ RANKINGS:\n\nGemini API client not initialized. Please check API key configuration."
    
    # Check if opportunities exist
    if not opportunities:
        return "⭐ RANKINGS:\n\nNo opportunities available to rank."
    
    # Limit to top 10 opportunities to avoid token limits
    opportunities_to_rank = opportunities[:10]
    
    # Build the prompt with ALL opportunities
    opportunities_text = ""
    for i, opp in enumerate(opportunities_to_rank, start=1):
        title = opp.get('title', 'Untitled')
        opp_type = opp.get('type', 'N/A')
        required_skills = ', '.join(opp.get('required_skills', []))
        min_cgpa = opp.get('min_cgpa', 'N/A')
        description = opp.get('description', '')[:100]
        
        opportunities_text += f"""
{i}. 
   Title: {title}
   Type: {opp_type}
   Required Skills: {required_skills}
   Minimum CGPA: {min_cgpa}
   Description: {description}
"""
    
    prompt = f"""You are NoRegret AI, an intelligent career opportunity advisor.

STUDENT PROFILE:
- Name: {profile.get('name', 'N/A')}
- CGPA: {profile.get('cgpa', 'N/A')} out of 10
- Degree: {profile.get('degree', 'N/A')}
- Graduation Year: {profile.get('grad_year', 'N/A')}
- Skills: {', '.join(profile.get('skills', []))}
- Interests: {', '.join(profile.get('interests', []))}

AVAILABLE OPPORTUNITIES:
{opportunities_text}

Based on the student's profile above, rank these opportunities from BEST MATCH (highest match) to WORST MATCH (lowest match).

Consider:
1. Skill alignment - Does the student have the required skills?
2. CGPA requirements - Does student meet minimum CGPA?
3. Degree eligibility - Is student's degree eligible?
4. Interests alignment - Does the opportunity match student's interests?

IMPORTANT: Return rankings in EXACTLY this format (one line per opportunity):

⭐ RANKINGS:

1. [Full Opportunity Title] | Match Score: [0-100] | Reason: [One short sentence why it's a good/poor match]
2. [Full Opportunity Title] | Match Score: [0-100] | Reason: [One short sentence why it's a good/poor match]
3. [Full Opportunity Title] | Match Score: [0-100] | Reason: [One short sentence why it's a good/poor match]
4. [Full Opportunity Title] | Match Score: [0-100] | Reason: [One short sentence why it's a good/poor match]
5. [Full Opportunity Title] | Match Score: [0-100] | Reason: [One short sentence why it's a good/poor match]

Only rank the TOP 5 opportunities. Be honest and realistic with match scores. Use the exact opportunity titles as provided above."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        print("\n===== RANKING RESPONSE =====")
        print(response.text)
        print("===========================\n")
        
        return response.text
    
    except Exception as e:
        return f"⭐ RANKINGS:\n\nError generating rankings: {str(e)}\n\nPlease check your API configuration."


def parse_rankings(rankings_text):
    """
    Parse the rankings response into a structured format
    """
    rankings = []
    
    # Debug print
    print("Parsing rankings text:", rankings_text[:500])
    
    lines = rankings_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Look for lines that start with number and have |
        if line and line[0].isdigit() and '|' in line:
            try:
                # Split by |
                parts = line.split('|')
                
                # Extract title (first part, remove the number)
                title_part = parts[0].strip()
                # Remove the number and dot (e.g., "1. " or "1.")
                title = re.sub(r'^\d+\.\s*', '', title_part)
                
                # Extract score from second part
                score = 0
                for part in parts:
                    if 'Match Score:' in part:
                        score_text = re.search(r'\d+', part)
                        if score_text:
                            score = int(score_text.group())
                        break
                
                # Extract reason from third part or wherever Reason: is
                reason = ""
                for part in parts:
                    if 'Reason:' in part:
                        reason = part.replace('Reason:', '').strip()
                        break
                    elif 'reason' in part.lower():
                        reason = part.split(':')[-1].strip()
                        break
                
                # If we still don't have a reason, try to get it from the line
                if not reason and len(parts) >= 3:
                    reason = parts[2].strip()
                
                rankings.append({
                    'title': title,
                    'score': str(score),
                    'reason': reason if reason else "Good match based on your profile"
                })
            except Exception as e:
                print(f"Error parsing line '{line}': {e}")
                continue
    
    # If no rankings parsed, try a fallback method
    if not rankings:
        print("No rankings parsed, trying fallback method...")
        # Try to extract any numbered lines
        for line in lines:
            line = line.strip()
            # Match patterns like "1. Title | Score: 85 | Reason: ..."
            match = re.match(r'^(\d+)\.\s*(.+?)\s*\|\s*(?:Match Score:\s*)?(\d+)', line, re.IGNORECASE)
            if match:
                rankings.append({
                    'title': match.group(2).strip(),
                    'score': match.group(3),
                    'reason': "AI recommended based on your profile"
                })
    
    print(f"✅ Parsed {len(rankings)} rankings")
    return rankings
