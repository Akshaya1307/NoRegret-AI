import streamlit as st
from mongo_utils import opportunities_collection, profiles_collection
from gemini_utils import (
    check_eligibility_with_ai, 
    parse_ai_response, 
    rank_opportunities, 
    parse_rankings
)
from datetime import datetime
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="NoRegret AI - Career Intelligence Platform",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============ CACHE OPTIMIZATIONS ============
@st.cache_data(ttl=1800)
def load_opportunities():
    """DEBUG VERSION - Shows exactly what's happening with MongoDB"""
    try:
        if opportunities_collection is not None:
            # Try to get all opportunities
            data = list(opportunities_collection.find({}, {"_id": 0}))
            
            # DEBUG: Show success message
            st.sidebar.success(f"✅ MongoDB Connected")
            st.sidebar.write(f"📊 Documents Found: {len(data)}")
            
            # Show first document sample if available
            if data:
                st.sidebar.write(f"📌 Sample: {data[0].get('title', 'No title')}")
            else:
                st.sidebar.warning("⚠️ Collection is empty! No documents found.")
            
            return data
        else:
            st.sidebar.error("❌ opportunities_collection is None")
            st.sidebar.info("Check mongo_utils.py - collection may not be initialized")
            return []
    except Exception as e:
        st.sidebar.error(f"❌ Mongo Error: {e}")
        return []

@st.cache_data(ttl=1800)
def get_total_profiles():
    """Cache profile count"""
    try:
        if profiles_collection is not None:
            return profiles_collection.count_documents({})
        else:
            return 0
    except:
        return 0

# Load data once
opportunities = load_opportunities()
total_profiles_db = get_total_profiles()

# ============ SESSION STATE INITIALIZATION ============
if 'profile' not in st.session_state:
    st.session_state.profile = {}
if 'checked_opps' not in st.session_state:
    st.session_state.checked_opps = {}
if 'profile_saved' not in st.session_state:
    st.session_state.profile_saved = False
if 'generated_rankings' not in st.session_state:
    st.session_state.generated_rankings = []
if 'rankings_generated' not in st.session_state:
    st.session_state.rankings_generated = False

# Custom CSS for Midnight AI Theme
st.markdown("""
<style>
    .stApp { background-color: #0F172A; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .metric-card {
        background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    }
    
    .stRadio > div {
        gap: 8px;
        background-color: #1E293B;
        padding: 10px;
        border-radius: 15px;
        border: 1px solid #8B5CF630;
    }
    .stRadio > div label {
        background-color: transparent;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        color: #94A3B8;
    }
    .stRadio > div label[data-baseweb="radio"] {
        background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
        color: white;
    }
    
    .ranking-item {
        background: linear-gradient(135deg, #8B5CF615 0%, #06B6D415 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 4px solid #8B5CF6;
    }
    
    .welcome-banner {
        background: linear-gradient(135deg, #8B5CF6, #06B6D4);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
    }
    
    .tag {
        display: inline-block;
        padding: 4px 12px;
        margin: 4px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .tag-internship { background: linear-gradient(135deg, #8B5CF6, #06B6D4); color: white; }
    .tag-hackathon { background: linear-gradient(135deg, #F59E0B, #EF4444); color: white; }
    .tag-scholarship { background: linear-gradient(135deg, #10B981, #059669); color: white; }
    .tag-program { background: linear-gradient(135deg, #3B82F6, #1D4ED8); color: white; }
    
    .stMarkdown, .stCaption, p, h1, h2, h3, h4 { color: #F1F5F9; }
    .stAlert { background-color: #1E293B; border-left-color: #8B5CF6; }
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #1E293B;
        color: #F1F5F9;
        border-color: #8B5CF6;
    }
    .stButton button {
        background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
        color: white;
        border: none;
        transition: transform 0.2s;
        font-weight: bold;
    }
    .stButton button:hover { transform: translateY(-2px); }
    .stProgress > div > div { background: linear-gradient(90deg, #8B5CF6, #06B6D4); }
</style>
""", unsafe_allow_html=True)

# ============ HEADER SECTION ============
col_hero1, col_hero2, col_hero3 = st.columns([1, 2, 1])
with col_hero2:
    st.markdown("<h1 style='text-align: center;'>👑 NoRegret AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>AI-Powered Career Intelligence Platform</p>", unsafe_allow_html=True)
    st.markdown("---")

# ============ OPTIMIZED NAVIGATION ============
selected_page = st.radio(
    "",
    ["🏠 Home", "📊 Dashboard", "🎯 Opportunities", "📈 Skill Analysis"],
    horizontal=True,
    label_visibility="collapsed"
)

# ============ PAGE RENDERING FUNCTIONS ============

def render_home_page():
    if not st.session_state.profile:
        st.markdown("""
        <div class="welcome-banner">
            <h2>✨ Welcome to NoRegret AI!</h2>
            <p>Your AI-powered career companion that helps you discover opportunities, analyze eligibility, and track your career readiness.</p>
            <p><strong>Powered by Gemini AI</strong> - Get personalized opportunity rankings and intelligent career advice.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📝 Create Your Profile")
        
        with st.form(key="profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name", placeholder="Enter your name")
                cgpa = st.number_input("CGPA (out of 10)", min_value=0.0, max_value=10.0, step=0.1, value=7.0)
                degree = st.selectbox("Degree", ["B.Tech", "B.E.", "BCA", "MCA", "B.Sc", "Other"])
                grad_year = st.number_input("Graduation Year", min_value=2024, max_value=2028, step=1, value=2026)
            
            with col2:
                skills_input = st.text_area("Skills (comma-separated)", "Python, JavaScript, SQL", height=100)
                interests = st.text_area("Interests (comma-separated)", "AI, Web Development, Hackathons", height=100)
            
            submitted = st.form_submit_button("🚀 Save Profile & Get Started", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("Please enter your name")
                else:
                    skills_list = [s.strip() for s in skills_input.split(",") if s.strip()]
                    interests_list = [i.strip() for i in interests.split(",") if i.strip()]
                    
                    profile = {
                        "name": name,
                        "cgpa": cgpa,
                        "degree": degree,
                        "grad_year": grad_year,
                        "skills": skills_list,
                        "interests": interests_list,
                        "created_at": datetime.now().isoformat()
                    }
                    st.session_state.profile = profile
                    try:
                        if profiles_collection is not None:
                            profiles_collection.insert_one(profile)
                            st.session_state.profile_saved = True
                    except:
                        pass
                    st.success("✅ Profile created successfully!")
                    st.rerun()
    else:
        st.markdown(f"""
        <div class="welcome-banner">
            <h2>👋 Welcome Back, {st.session_state.profile.get('name', 'Student')}!</h2>
            <p>Your career readiness score is ready. Let's find your next opportunity with AI-powered rankings.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Your Profile Card")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="background-color: #1E293B; padding: 25px; border-radius: 15px; border: 1px solid #8B5CF630;">
                <h3 style="text-align: center;">{st.session_state.profile.get('name', 'Student')}</h3>
                <hr>
                <p><strong>📊 CGPA:</strong> {st.session_state.profile.get('cgpa', 'N/A')}/10</p>
                <p><strong>🎓 Degree:</strong> {st.session_state.profile.get('degree', 'N/A')}</p>
                <p><strong>💡 Skills:</strong> <code>{', '.join(st.session_state.profile.get('skills', []))}</code></p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("✏️ Edit Profile", use_container_width=True):
            st.session_state.profile = {}
            st.rerun()

def render_dashboard_page():
    if not st.session_state.profile:
        st.warning("⚠️ Please complete your profile on the Home page first!")
        return
    
    st.markdown("## 🚀 Your Career Readiness Dashboard")
    st.markdown("---")
    
    user_skills = [s.lower() for s in st.session_state.profile.get('skills', [])]
    
    all_required_skills = set()
    for opp in opportunities:
        all_required_skills.update([s.lower() for s in opp.get('required_skills', [])])
    
    skills_coverage = len(set(user_skills).intersection(all_required_skills)) / len(all_required_skills) if all_required_skills else 0
    cgpa_score = min(st.session_state.profile.get('cgpa', 0) / 10, 1.0)
    
    eligible_count = sum(1 for r in st.session_state.checked_opps.values() if r.get('eligible') == 'Yes')
    total_checked = len(st.session_state.checked_opps)
    match_rate = (eligible_count / total_checked) if total_checked > 0 else 0
    readiness_score = int((skills_coverage * 0.4 + cgpa_score * 0.3 + match_rate * 0.3) * 100)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>📊 Readiness</h3><h1>{readiness_score}%</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>✅ Eligible</h3><h1>{eligible_count}</h1></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>🎯 Match Rate</h3><h1>{int(match_rate * 100)}%</h1></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><h3>👥 Community</h3><h1>{total_profiles_db}</h1></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("### 💪 Skills Coverage")
        st.progress(skills_coverage)
        st.markdown("### 📊 CGPA Score")
        st.progress(cgpa_score)
    with col_p2:
        st.markdown("### 🎯 Opportunity Match Rate")
        st.progress(match_rate)
        if total_checked > 0:
            avg_score = sum(int(r.get('score', 0)) for r in st.session_state.checked_opps.values()) // total_checked
            st.markdown("### ⭐ Average Score")
            st.progress(avg_score / 100)

def render_opportunities_page():
    if not st.session_state.profile:
        st.warning("⚠️ Please complete your profile on the Home page first!")
        return
    
    st.markdown("## ⭐ AI-Powered Opportunity Rankings")
    st.markdown("---")
    
    col_rank1, col_rank2, col_rank3 = st.columns([2, 1, 1])
    with col_rank1:
        st.info("🤖 Let Gemini AI rank the best opportunities for you.")
    with col_rank2:
        if opportunities:
            st.metric("📊 Total Opportunities", len(opportunities))
    with col_rank3:
        if st.button("🚀 Generate AI Rankings", use_container_width=True):
            with st.spinner("✨ Gemini AI is analyzing..."):
                try:
                    ranking_text = rank_opportunities(st.session_state.profile, opportunities)
                    with st.expander("🔍 Debug: Raw Gemini Output"):
                        st.code(ranking_text)
                    
                    rankings = parse_rankings(ranking_text)
                    
                    if not rankings:
                        st.error("⚠️ Gemini returned no rankings. Please try again.")
                    else:
                        st.session_state.generated_rankings = rankings
                        st.session_state.rankings_generated = True
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    if st.session_state.get('rankings_generated', False) and st.session_state.get('generated_rankings'):
        st.markdown("---")
        st.markdown("### 🎯 Your Personalized Top 5 Opportunities")
        
        for rank, item in enumerate(st.session_state.generated_rankings, start=1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📌"
            score_color = "#22C55E" if rank == 1 else "#06B6D4" if rank == 2 else "#F59E0B" if rank == 3 else "#8B5CF6"
            
            st.markdown(f"""
            <div class="ranking-item" style="border-left-color: {score_color};">
                <h3>{medal} #{rank} - {item['title']}</h3>
                <p><strong>🎯 Match Score: <span style="color: {score_color};">{item['score']}%</span></strong></p>
                <p>💡 {item['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Rankings", use_container_width=True):
            st.session_state.rankings_generated = False
            st.session_state.generated_rankings = []
            st.rerun()
        
        st.markdown("---")
    
    # Skill-based matching
    user_skills_raw = st.session_state.profile.get("skills", [])
    user_skills = [s.lower().strip() for s in user_skills_raw if s]
    
    matched_opps = []
    
    for opp in opportunities:
        required_skills_raw = opp.get("required_skills", [])
        required_skills = [s.lower().strip() for s in required_skills_raw if s]
        
        # Check for matches
        matched = False
        for user_skill in user_skills:
            for req_skill in required_skills:
                if user_skill in req_skill or req_skill in user_skill:
                    matched = True
                    break
            if matched:
                break
        
        if matched:
            matched_opps.append(opp)
    
    # Show all opportunities if no matches
    if not matched_opps:
        st.warning(f"🔍 No exact skill matches found. Showing all {len(opportunities)} available opportunities.")
        matched_opps = opportunities
    
    st.info(f"🎯 Found {len(matched_opps)} opportunities relevant to your skills")
    
    filter_type = st.selectbox("📂 Filter by Type", ["All", "internship", "hackathon", "scholarship", "program"])
    if filter_type != "All":
        matched_opps = [opp for opp in matched_opps if opp.get('type') == filter_type]
    
    # Use a unique counter for each opportunity to guarantee unique keys
    for idx, opp in enumerate(matched_opps[:10]):
        with st.expander(f"🎯 {opp.get('title', 'Untitled')}"):
            st.caption(f"📅 Deadline: {opp.get('deadline', 'No deadline')} | Type: {opp.get('type', 'Unknown')}")
            st.write(opp.get('description', 'No description'))
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                with st.expander("📋 Requirements"):
                    st.markdown(f"**CGPA:** {opp.get('min_cgpa', 'N/A')}")
                    st.markdown(f"**Skills:** {', '.join(opp.get('required_skills', []))}")
            
            # Create a truly unique key using multiple identifiers
            opp_id = opp.get('id', opp.get('_id', idx))
            title_clean = opp.get('title', 'unknown')[:20].replace(" ", "_").replace("/", "_")
            # Use index + id + title to guarantee uniqueness
            unique_key = f"analyze_{idx}_{opp_id}_{title_clean}"
            
            if opp_id not in st.session_state.checked_opps:
                if st.button(f"🔍 Analyze", key=unique_key, use_container_width=True):
                    with st.spinner("🤖 AI analyzing..."):
                        ai_response = check_eligibility_with_ai(st.session_state.profile, opp)
                        result = parse_ai_response(ai_response)
                        st.session_state.checked_opps[opp_id] = result
                        st.rerun()
            else:
                result = st.session_state.checked_opps[opp_id]
                score = int(result.get('score', 0)) if str(result.get('score', '0')).isdigit() else 0
                st.metric("🎯 Score", f"{score}/100")
                st.progress(score / 100)
                st.success("✅ ELIGIBLE" if result.get('eligible') == 'Yes' else "❌ NOT ELIGIBLE")
                
                # Add clear button with unique key too
                clear_key = f"clear_{idx}_{opp_id}_{title_clean}"
                if st.button(f"🗑️ Clear", key=clear_key, use_container_width=True):
                    del st.session_state.checked_opps[opp_id]
                    st.rerun()

def render_skill_analysis_page():
    if not st.session_state.profile:
        st.warning("⚠️ Please complete your profile on the Home page first!")
        return
    
    st.markdown("## 📈 Skill Gap Analysis")
    st.markdown("---")
    
    if st.session_state.checked_opps:
        all_missing = []
        for result in st.session_state.checked_opps.values():
            missing = result.get('missing_skills', [])
            all_missing.extend([m.lower() for m in missing if m])
        
        if all_missing:
            skill_counts = Counter(all_missing)
            fig = px.bar(x=list(skill_counts.keys()), y=list(skill_counts.values()), 
                         title="Skills You Need to Learn",
                         color=list(skill_counts.values()),
                         color_continuous_scale="purple")
            fig.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#1E293B", font_color="#F1F5F9")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📋 Learning Recommendations")
            
            for skill, count in skill_counts.most_common(5):
                st.markdown(f"**📌 {skill.title()}** - Missing in {count} opportunities")
        else:
            st.success("🎉 No skill gaps detected! You have all required skills!")
            st.balloons()
    else:
        st.info("👆 Go to Opportunities tab and analyze some opportunities first to see your skill gaps!")

# ============ PAGE ROUTING ============
if selected_page == "🏠 Home":
    render_home_page()
elif selected_page == "📊 Dashboard":
    render_dashboard_page()
elif selected_page == "🎯 Opportunities":
    render_opportunities_page()
elif selected_page == "📈 Skill Analysis":
    render_skill_analysis_page()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p>🎯 <strong>NoRegret AI</strong> - Powered by Gemini AI | Midnight Theme</p>
</div>
""", unsafe_allow_html=True)
