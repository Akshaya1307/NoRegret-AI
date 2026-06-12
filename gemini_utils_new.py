def render_skill_analysis_page():
    if not st.session_state.profile:
        st.warning("⚠️ Please complete your profile on the Home page first!")
        return
    
    st.markdown("## 📈 Skill Gap Analysis")
    st.markdown("---")
    
    if st.session_state.checked_opps:
        # Debug: Show what's in checked_opps
        with st.expander("🔍 Debug: Checked Opportunities Data"):
            for opp_id, result in st.session_state.checked_opps.items():
                st.write(f"**Opportunity {opp_id}:**")
                st.write(f"  - Eligible: {result.get('eligible')}")
                st.write(f"  - Score: {result.get('score')}")
                st.write(f"  - Missing Skills: {result.get('missing_skills', [])}")
                st.write(f"  - Reason: {result.get('reason', '')[:100]}")
                st.write("---")
        
        all_missing = []
        for opp_id, result in st.session_state.checked_opps.items():
            missing = result.get('missing_skills', [])
            if missing:
                all_missing.extend([m.lower().strip() for m in missing if m])
                st.write(f"Found missing skills for {opp_id}: {missing}")  # Debug
        
        if all_missing:
            st.success(f"✅ Found {len(all_missing)} skill gaps across your analyzed opportunities!")
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
                st.markdown(f"   → Learn this to unlock more opportunities!")
        else:
            st.warning("⚠️ No skill gaps detected in the analyzed opportunities.")
            st.info("This might mean:")
            st.markdown("1. You haven't analyzed enough opportunities yet")
            st.markdown("2. Your profile skills perfectly match all opportunities (unlikely)")
            st.markdown("3. Gemini isn't returning missing_skills data - check the debug panel above")
    else:
        st.info("👆 Go to Opportunities tab and analyze some opportunities first to see your skill gaps!")
