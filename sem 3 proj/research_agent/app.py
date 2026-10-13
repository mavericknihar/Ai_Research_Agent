import streamlit as st
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from research_agent import create_agent, ResearchState
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Autonomous Research Agent • Neon AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# THEME CONFIGURATION
# ---------------------------------------------------------
THEMES = {
    "⚡ Cyber Cyan": {
        "primary": "#00f5ff",
        "secondary": "#0077b6",
        "accent": "#7928ca",
        "glow": "rgba(0, 245, 255, 0.4)",
        "card_border": "rgba(0, 245, 255, 0.25)",
        "bg_gradient": "radial-gradient(circle at 15% 10%, rgba(0, 245, 255, 0.08) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(121, 40, 202, 0.08) 0%, transparent 50%)",
        "btn_gradient": "linear-gradient(135deg, #00f5ff 0%, #0077b6 100%)",
        "badge_color": "#00f5ff",
    },
    "🔮 Synthwave Violet": {
        "primary": "#c084fc",
        "secondary": "#a855f7",
        "accent": "#f43f5e",
        "glow": "rgba(192, 132, 252, 0.4)",
        "card_border": "rgba(192, 132, 252, 0.25)",
        "bg_gradient": "radial-gradient(circle at 15% 10%, rgba(168, 85, 247, 0.10) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(244, 63, 94, 0.08) 0%, transparent 50%)",
        "btn_gradient": "linear-gradient(135deg, #a855f7 0%, #f43f5e 100%)",
        "badge_color": "#c084fc",
    },
    "🟢 Matrix Emerald": {
        "primary": "#00ff9d",
        "secondary": "#059669",
        "accent": "#00b4d8",
        "glow": "rgba(0, 255, 157, 0.4)",
        "card_border": "rgba(0, 255, 157, 0.25)",
        "bg_gradient": "radial-gradient(circle at 15% 10%, rgba(0, 255, 157, 0.08) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(5, 150, 105, 0.08) 0%, transparent 50%)",
        "btn_gradient": "linear-gradient(135deg, #00ff9d 0%, #059669 100%)",
        "badge_color": "#00ff9d",
    },
    "🔥 Solar Amber": {
        "primary": "#ffb703",
        "secondary": "#fb8500",
        "accent": "#e63946",
        "glow": "rgba(255, 183, 3, 0.4)",
        "card_border": "rgba(255, 183, 3, 0.25)",
        "bg_gradient": "radial-gradient(circle at 15% 10%, rgba(255, 183, 3, 0.10) 0%, transparent 50%), radial-gradient(circle at 85% 90%, rgba(251, 133, 0, 0.08) 0%, transparent 50%)",
        "btn_gradient": "linear-gradient(135deg, #ffb703 0%, #fb8500 100%)",
        "badge_color": "#ffb703",
    },
}

DEFAULT_MODELS = {
    "groq": ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "Custom Model"],
    "openai": ["gpt-4o-mini", "gpt-4o", "o3-mini", "Custom Model"],
    "gemini": ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "Custom Model"],
    "ollama": ["llama3.1", "mistral", "qwen2.5", "Custom Model"],
}


def get_neon_css(theme_key: str) -> str:
    t = THEMES.get(theme_key, THEMES["⚡ Cyber Cyan"])
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    :root {{
        --neon-primary: {t['primary']};
        --neon-secondary: {t['secondary']};
        --neon-accent: {t['accent']};
        --neon-glow: {t['glow']};
        --neon-border: {t['card_border']};
        --btn-grad: {t['btn_gradient']};
    }}
    
    * {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    code, pre, .terminal-text {{
        font-family: 'JetBrains Mono', monospace !important;
    }}
    
    /* Overall Background */
    .stApp {{
        background-color: #060813 !important;
        background-image: {t['bg_gradient']} !important;
        color: #e2e8f0;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: rgba(10, 14, 28, 0.85) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--neon-border) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.6);
    }}
    
    /* Main Hero Banner */
    .hero-banner {{
        background: rgba(13, 18, 36, 0.7);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--neon-border);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 25px var(--neon-glow);
        backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
    }}
    
    .hero-banner::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: var(--btn-grad);
        box-shadow: 0 0 15px var(--neon-primary);
    }}
    
    .hero-title {{
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, var(--neon-primary) 60%, var(--neon-accent) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.02em;
        text-shadow: 0 0 35px var(--neon-glow);
    }}
    
    .hero-subtitle {{
        color: #94a3b8;
        font-size: 1.15rem;
        margin-top: 0.6rem;
        font-weight: 400;
    }}
    
    /* Status Badges */
    .badge-container {{
        display: flex;
        gap: 0.75rem;
        margin-top: 1.2rem;
        flex-wrap: wrap;
    }}
    
    .neon-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid var(--neon-border);
        color: #f1f5f9;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .pulse-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--neon-primary);
        box-shadow: 0 0 8px var(--neon-primary);
        animation: pulseGlow 1.8s infinite ease-in-out;
    }}
    
    @keyframes pulseGlow {{
        0%, 100% {{ transform: scale(1); opacity: 1; box-shadow: 0 0 10px var(--neon-primary); }}
        50% {{ transform: scale(1.3); opacity: 0.5; box-shadow: 0 0 3px var(--neon-primary); }}
    }}
    
    /* Glassmorphic Neon Cards */
    .neon-card {{
        background: rgba(13, 18, 36, 0.65);
        border-radius: 16px;
        padding: 1.6rem;
        border: 1px solid var(--neon-border);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(14px);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }}
    
    .neon-card:hover {{
        border-color: var(--neon-primary);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px var(--neon-glow);
    }}
    
    /* Research HUD & Realtime Terminal */
    .hud-container {{
        background: #080c1a;
        border-radius: 16px;
        border: 1px solid var(--neon-border);
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 0 30px rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(0, 0, 0, 0.4);
    }}
    
    .hud-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.8rem;
        margin-bottom: 1rem;
    }}
    
    .hud-title {{
        color: var(--neon-primary);
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .terminal-box {{
        background: rgba(5, 7, 15, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 1rem;
        max-height: 220px;
        overflow-y: auto;
        font-size: 0.85rem;
        color: #94a3b8;
    }}
    
    .terminal-line {{
        padding: 0.25rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.02);
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
    }}
    
    .terminal-time {{
        color: #475569;
        font-size: 0.75rem;
        min-width: 65px;
    }}
    
    .terminal-tag {{
        color: var(--neon-primary);
        font-weight: 600;
    }}
    
    .terminal-msg {{
        color: #cbd5e1;
        flex: 1;
    }}
    
    /* Step Timeline in HUD */
    .timeline-steps {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 0.75rem;
        margin-bottom: 1.2rem;
    }}
    
    .step-node {{
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 0.8rem 0.6rem;
        text-align: center;
        transition: all 0.3s ease;
    }}
    
    .step-node.active {{
        border-color: var(--neon-primary);
        background: rgba(15, 23, 42, 0.9);
        box-shadow: 0 0 15px var(--neon-glow);
    }}
    
    .step-node.done {{
        border-color: #10b981;
        background: rgba(6, 78, 59, 0.25);
    }}
    
    .step-icon-circle {{
        font-size: 1.25rem;
        margin-bottom: 0.25rem;
    }}
    
    .step-label {{
        font-size: 0.78rem;
        color: #cbd5e1;
        font-weight: 500;
    }}
    
    /* Result Answer Container */
    .briefing-card {{
        background: rgba(13, 18, 36, 0.85);
        border: 1px solid var(--neon-border);
        border-radius: 20px;
        padding: 2.2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), 0 0 30px var(--neon-glow);
        backdrop-filter: blur(16px);
        margin-top: 1.5rem;
        position: relative;
    }}
    
    .briefing-card::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: var(--btn-grad);
    }}
    
    .briefing-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }}
    
    .briefing-title {{
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    
    .briefing-body {{
        color: #e2e8f0;
        line-height: 1.85;
        font-size: 1.02rem;
    }}
    
    .briefing-body h1, .briefing-body h2, .briefing-body h3 {{
        color: var(--neon-primary);
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }}
    
    .briefing-body a {{
        color: var(--neon-primary);
        text-decoration: none;
        border-bottom: 1px dashed var(--neon-primary);
        transition: all 0.2s;
    }}
    
    .briefing-body a:hover {{
        color: #ffffff;
        text-shadow: 0 0 10px var(--neon-primary);
    }}
    
    /* Source Cards Grid */
    .source-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }}
    
    .source-tile {{
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.25s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    
    .source-tile:hover {{
        border-color: var(--neon-primary);
        background: rgba(15, 23, 42, 0.95);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px var(--neon-glow);
    }}
    
    .source-tile-title {{
        color: #f1f5f9;
        font-weight: 600;
        font-size: 0.92rem;
        text-decoration: none;
        margin-bottom: 0.4rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}
    
    .source-tile-domain {{
        color: var(--neon-primary);
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 0.5rem;
    }}
    
    .source-tile-snippet {{
        color: #94a3b8;
        font-size: 0.8rem;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}
    
    /* Interactive Streamlit Overrides */
    .stTextArea textarea {{
        background: rgba(10, 14, 28, 0.8) !important;
        border: 1px solid var(--neon-border) !important;
        border-radius: 14px !important;
        color: #f8fafc !important;
        font-size: 1.05rem !important;
        padding: 1.2rem !important;
        transition: all 0.25s ease !important;
    }}
    
    .stTextArea textarea:focus {{
        border-color: var(--neon-primary) !important;
        box-shadow: 0 0 20px var(--neon-glow) !important;
    }}
    
    .stButton > button {{
        background: var(--btn-grad) !important;
        color: #060813 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 20px var(--neon-glow) !important;
        transition: all 0.25s ease !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 30px var(--neon-glow), 0 0 20px var(--neon-primary) !important;
        color: #000000 !important;
    }}
    
    .stButton > button:disabled {{
        opacity: 0.4 !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    
    /* Metric styling */
    [data-testid="stMetricValue"] {{
        color: var(--neon-primary) !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    
    /* Sliders */
    .stSlider [data-baseweb="slider"] {{
        color: var(--neon-primary) !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: #060813;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.15);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--neon-primary);
        box-shadow: 0 0 10px var(--neon-primary);
    }}
</style>
"""


def init_session_state():
    defaults = {
        "theme": "⚡ Cyber Cyan",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "max_iterations": 2,
        "temperature": 0.3,
        "history": [],
        "current_answer": None,
        "current_state": None,
        "is_researching": False,
        "live_logs": [],
        "current_step_idx": 0,
        "query_input": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_header(provider: str, model: str):
    st.markdown(f"""
    <div class="hero-banner">
        <h1 class="hero-title">⚡ AUTONOMOUS RESEARCH AGENT</h1>
        <p class="hero-subtitle">High-Velocity Deep Research Engine • Neural Planning • Live Web Crawling • Synthesized Citations</p>
        <div class="badge-container">
            <div class="neon-badge"><div class="pulse-dot"></div> SYSTEM ONLINE</div>
            <div class="neon-badge">⚡ PROVIDER: {provider.upper()}</div>
            <div class="neon-badge">🧠 MODEL: {model}</div>
            <div class="neon-badge">🌐 CRAWLER: LIVE DDGS</div>
            <div class="neon-badge">🔬 SEMESTER 3 PROJECT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### 🎨 Aesthetic Themes")
        selected_theme = st.selectbox(
            "Neon Aesthetic",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.theme) if st.session_state.theme in THEMES else 0,
            help="Switch neon cyber palette across the UI"
        )
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
            
        st.markdown("---")
        st.markdown("### ⚙️ Neural Provider & Model")
        
        provider_options = ["groq", "openai", "gemini", "ollama"]
        current_prov_idx = provider_options.index(st.session_state.provider) if st.session_state.provider in provider_options else 0
        provider = st.selectbox("LLM Provider", options=provider_options, index=current_prov_idx)
        st.session_state.provider = provider
        
        # Model options
        models = DEFAULT_MODELS.get(provider, ["Custom Model"])
        model_choice = st.selectbox("Model", options=models, index=0)
        
        if model_choice == "Custom Model":
            custom_model = st.text_input("Enter Model Name", value="openai/gpt-oss-20b" if provider == "groq" else "")
            st.session_state.model = custom_model
        else:
            st.session_state.model = model_choice
            
        st.markdown("---")
        st.markdown("### 🎛️ Research Hyperparameters")
        
        st.session_state.max_iterations = st.slider(
            "Research Cycles (Depth)",
            min_value=1,
            max_value=4,
            value=st.session_state.max_iterations,
            help="Higher cycles trigger deeper search iterations and gap-filling"
        )
        
        st.session_state.temperature = st.slider(
            "Creativity / Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.05
        )
        
        st.markdown("---")
        st.markdown("### 📊 Session Statistics")
        c1, c2 = st.columns(2)
        c1.metric("Queries", len(st.session_state.history))
        total_sources = sum(len(h.get("sources", [])) for h in st.session_state.history)
        c2.metric("Sources", total_sources)
        
        st.markdown("---")
        st.markdown("### 🕒 Research History")
        if st.session_state.history:
            for idx, item in enumerate(reversed(st.session_state.history)):
                q_label = item['question'][:30] + "..." if len(item['question']) > 30 else item['question']
                col_btn, col_del = st.columns([4, 1])
                with col_btn:
                    if st.button(f"🔍 {q_label}", key=f"hist_load_{idx}", use_container_width=True):
                        st.session_state.current_answer = item["answer"]
                        st.session_state.current_state = item["state"]
                        st.rerun()
                with col_del:
                    if st.button("✕", key=f"hist_del_{idx}"):
                        st.session_state.history.remove(item)
                        st.rerun()
                        
            if st.button("🗑️ Clear All History", use_container_width=True):
                st.session_state.history = []
                st.session_state.current_answer = None
                st.session_state.current_state = None
                st.rerun()
        else:
            st.caption("No queries run in this session yet.")


def render_sources_grid(sources: List[Dict]):
    if not sources:
        return
        
    st.markdown('<h3 style="color:#ffffff; margin-top:1.5rem; margin-bottom:0.8rem;">📚 Traceable Sources & Evidence</h3>', unsafe_allow_html=True)
    st.markdown('<div class="source-grid">', unsafe_allow_html=True)
    
    for s in sources:
        url = s.get("url", "#")
        title = s.get("title", url)
        snippet = s.get("snippet", "")
        # Clean domain
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
        except Exception:
            domain = "web"
            
        st.markdown(f"""
        <div class="source-tile">
            <div>
                <div class="source-tile-domain">🌐 {domain}</div>
                <a href="{url}" target="_blank" class="source-tile-title">{title}</a>
                <div class="source-tile-snippet">{snippet}</div>
            </div>
            <div style="margin-top:0.8rem; text-align:right;">
                <a href="{url}" target="_blank" style="color:var(--neon-primary); font-size:0.75rem; text-decoration:none; font-weight:600;">VISIT SOURCE ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)


def render_hud(steps: List[str], current_step: int, logs: List[Dict[str, str]]):
    """Render the Cyberpunk Heads-Up Display (HUD) with step indicators and streaming terminal log."""
    step_items = [
        ("🎯", "Planning", "Formulating strategy"),
        ("🌐", "Web Search", "Querying live web"),
        ("📄", "Scraping", "Extracting content"),
        ("📝", "Summarizing", "Synthesizing evidence"),
        ("⚖️", "Evaluating", "Gap verification"),
        ("🚀", "Synthesis", "Final briefing"),
    ]
    
    st.markdown('<div class="hud-container">', unsafe_allow_html=True)
    st.markdown("""
    <div class="hud-header">
        <div class="hud-title"><div class="pulse-dot"></div> NEURAL RESEARCH HEADS-UP DISPLAY (HUD)</div>
        <div style="color:#94a3b8; font-size:0.8rem; font-family:'JetBrains Mono';">STATUS: ACTIVE PIPELINE</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Timeline
    step_html = '<div class="timeline-steps">'
    for idx, (icon, title, desc) in enumerate(step_items):
        if idx < current_step:
            cls = "done"
            status_text = "✓ COMPLETED"
        elif idx == current_step:
            cls = "active"
            status_text = "⟳ RUNNING"
        else:
            cls = "pending"
            status_text = "○ STANDBY"
            
        step_html += f"""
        <div class="step-node {cls}">
            <div class="step-icon-circle">{icon}</div>
            <div class="step-label">{title}</div>
            <div style="font-size:0.68rem; color:#64748b; font-family:'JetBrains Mono';">{status_text}</div>
        </div>
        """
    step_html += '</div>'
    st.markdown(step_html, unsafe_allow_html=True)
    
    # Terminal Log Box
    st.markdown('<div class="terminal-box">', unsafe_allow_html=True)
    if logs:
        for entry in logs[-8:]:
            st.markdown(f"""
            <div class="terminal-line">
                <span class="terminal-time">[{entry['time']}]</span>
                <span class="terminal-tag">[{entry['tag'].upper()}]</span>
                <span class="terminal-msg">{entry['msg']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="terminal-line"><span class="terminal-msg">Initializing neural agent processes...</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    init_session_state()
    st.markdown(get_neon_css(st.session_state.theme), unsafe_allow_html=True)
    render_header(st.session_state.provider, st.session_state.model)
    render_sidebar()
    
    # Quick trending prompt chips
    st.markdown('<p style="color:#94a3b8; font-size:0.88rem; margin-bottom:0.4rem; font-weight:600;">⚡ TRENDING RESEARCH INQUIRIES</p>', unsafe_allow_html=True)
    
    chips = [
        "Quantum error correction breakthroughs 2026",
        "Autonomous AI agent swarm architectures",
        "CRISPR in-vivo gene editing clinical trials",
        "Solid-state battery commercial readiness",
        "Nuclear fusion net-gain energy milestones",
    ]
    
    chip_cols = st.columns(len(chips))
    for i, chip_text in enumerate(chips):
        with chip_cols[i]:
            if st.button(f"✨ {chip_text[:22]}...", key=f"chip_{i}", use_container_width=True):
                st.session_state.query_input = chip_text
                st.rerun()
                
    # Search input area
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col_input, col_action = st.columns([4, 1])
    
    with col_input:
        question = st.text_area(
            "Research Question",
            value=st.session_state.get("query_input", ""),
            placeholder="Enter research topic (e.g. 'Recent advances in neuromorphic computing architectures 2026')",
            height=95,
            label_visibility="collapsed"
        )
        
    with col_action:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        research_btn = st.button(
            "⚡ EXECUTE RESEARCH",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_researching or not question.strip()
        )
        
    # Execution Logic
    if research_btn and question.strip():
        st.session_state.is_researching = True
        st.session_state.current_answer = None
        st.session_state.current_state = None
        st.session_state.live_logs = []
        
        hud_placeholder = st.empty()
        
        def push_log(tag: str, msg: str, step_idx: int):
            now_str = datetime.now().strftime("%H:%M:%S")
            st.session_state.live_logs.append({"time": now_str, "tag": tag, "msg": msg})
            with hud_placeholder.container():
                render_hud(["Planning", "Web Search", "Scraping", "Summarizing", "Evaluating", "Synthesis"], step_idx, st.session_state.live_logs)
                
        try:
            push_log("INIT", "Instantiating research agent with neural pipeline...", 0)
            agent = create_agent(
                provider=st.session_state.provider,
                model=st.session_state.model,
                temperature=st.session_state.temperature
            )
            
            def agent_callback(event_type: str, msg: str, data: Optional[Dict[str, Any]] = None):
                step_map = {
                    "plan_start": (0, "PLAN"),
                    "queries_planned": (1, "PLAN"),
                    "search_query_done": (1, "SEARCH"),
                    "scrape_start": (2, "SCRAPE"),
                    "source_scraped": (2, "SCRAPE"),
                    "summarize_start": (3, "ANALYZE"),
                    "summarize_done": (3, "ANALYZE"),
                    "eval_done": (4, "EVALUATE"),
                    "synthesize_start": (5, "SYNTHESIZE"),
                    "synthesize_done": (5, "COMPLETE"),
                    "complete": (5, "DONE")
                }
                step_idx, tag = step_map.get(event_type, (1, "AGENT"))
                push_log(tag, msg, step_idx)
                time.sleep(0.05)
                
            result = agent.run(
                question=question,
                max_iterations=st.session_state.max_iterations,
                callback=agent_callback
            )
            
            st.session_state.current_answer = result.final_answer
            st.session_state.current_state = result
            st.session_state.history.append({
                "question": question,
                "answer": result.final_answer,
                "sources": result.sources,
                "state": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
            push_log("FINISH", "Research briefing generated successfully!", 5)
            st.session_state.is_researching = False
            time.sleep(0.5)
            hud_placeholder.empty()
            st.rerun()
            
        except Exception as e:
            st.session_state.is_researching = False
            hud_placeholder.empty()
            st.error(f"❌ Research pipeline failed: {str(e)}")
            
    # Display research answer if available
    if st.session_state.current_answer and st.session_state.current_state:
        state: ResearchState = st.session_state.current_state
        
        # Action Toolbar & Metrics
        st.markdown('<div class="briefing-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="briefing-header">
            <div class="briefing-title">🎯 Executive Research Briefing</div>
            <div style="font-size:0.85rem; color:#94a3b8; font-family:'JetBrains Mono';">
                CYCLES: {state.iteration} • DOCUMENTS: {len(state.documents)} • SOURCES: {len(state.sources)}
            </div>
        </div>
        <div class="briefing-body">
        """, unsafe_allow_html=True)
        
        # Render markdown content
        st.markdown(st.session_state.current_answer, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Action buttons
        col_copy, col_down_md, col_down_json = st.columns([1, 1, 1])
        
        with col_copy:
            # Markdown download
            st.download_button(
                label="📥 Download Report (.md)",
                data=f"# Research Inquiry: {question}\n\n{st.session_state.current_answer}\n\n## Sources\n" + "\n".join([f"- [{s.get('title')}]: {s.get('url')}" for s in state.sources]),
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        with col_down_md:
            # JSON state export
            export_data = {
                "question": question,
                "answer": st.session_state.current_answer,
                "iterations": state.iteration,
                "sources": state.sources,
                "summaries": state.summaries,
                "timestamp": datetime.now().isoformat()
            }
            st.download_button(
                label="🗂️ Export Pipeline State (.json)",
                data=json.dumps(export_data, indent=2),
                file_name=f"research_state_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True
            )
            
        with col_down_json:
            if st.button("🔄 New Research Query", use_container_width=True):
                st.session_state.current_answer = None
                st.session_state.current_state = None
                st.session_state.query_input = ""
                st.rerun()
                
        # Render traceable source cards
        if state.sources:
            render_sources_grid(state.sources)
            
    # Footer
    st.markdown("""
    <div style="text-align: center; color: #475569; font-size: 0.85rem; padding: 3rem 1rem 1rem 1rem; margin-top: 3rem; border-top: 1px solid rgba(255, 255, 255, 0.05); font-family: 'JetBrains Mono';">
        ⚡ AUTONOMOUS RESEARCH AGENT • SEMESTER 3 PROJECT<br>
        POWERED BY LANGCHAIN • GROQ HIGH-SPEED INFERENCE • STREAMLIT NEON UI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()