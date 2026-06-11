from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def check_eligibility_with_ai(profile, opportunity):
    prompt = f"""
    You are an eligibility assessment AI for students.
    
    STUDENT PROFILE:
    - CGPA: {profile.get('cgpa', 'N/A')}
    - Degree: {profile.get('degree', 'N/A')}
    - Graduation Year: {profile.get('grad_year', 'N/A')}
    - Skills: {', '.join(profile.get('skills', []))}
    - Interests: {', '.join(profile.get('interests', []))}
    
    OPPORTUNITY:
    - Title: {opportunity.get('title', 'N/A')}
    - Min CGPA Required: {opportunity.get('min_cgpa', 'N/A')}
    - Eligible Degrees: {', '.join(opportunity.get('eligible_degrees', []))}
    - Required Skills: {', '.join(opportunity.get('required_skills', []))}
    
    Analyze eligibility and respond in this EXACT format:
    
    ELIGIBLE: [Yes/No]
    REASON: [1-2 sentence explanation]
    MISSING_SKILLS: [comma-separated list or "None"]
    RECOMMENDATION: [what to do next]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # or 'gemini-2.5-pro' for better quality
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"""ELIGIBLE: No
REASON: Error: {str(e)}
MISSING_SKILLS: None
RECOMMENDATION: Check your connection and try again"""

def parse_ai_response(response_text):
    lines = response_text.strip().split('\n')
    result = {
        'eligible': 'No',
        'reason': '',
        'missing_skills': [],
        'recommendation': ''
    }
    
    for line in lines:
        if line.startswith('ELIGIBLE:'):
            result['eligible'] = 'Yes' if 'Yes' in line else 'No'
        elif line.startswith('REASON:'):
            result['reason'] = line.replace('REASON:', '').strip()
        elif line.startswith('MISSING_SKILLS:'):
            skills = line.replace('MISSING_SKILLS:', '').strip()
            result['missing_skills'] = [s.strip() for s in skills.split(',') if s.strip() != 'None']
        elif line.startswith('RECOMMENDATION:'):
            result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
    
    return result