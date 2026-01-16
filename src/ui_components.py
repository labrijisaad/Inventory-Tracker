"""
UI Components for Midad Books
Beautiful, reusable interface elements
كتب مداد - مكونات الواجهة
"""

import base64
from pathlib import Path

import streamlit as st


def image_to_base64(image_path: str) -> str:
    """Convert image to base64 for embedding in HTML."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


def render_logo(logo_path: str = "assets/logo.png", width: int = 100):
    """Render beautiful centered logo with dark mode neon glow."""
    if Path(logo_path).exists():
        logo_base64 = image_to_base64(logo_path)
        st.sidebar.markdown(
            f'''
            <div style="text-align: center; padding: 25px 0 15px 0; margin-bottom: 10px;">
                <div style="display: inline-block; padding: 18px; 
                            background: linear-gradient(135deg, #8a6eff 0%, #5836b3 100%);
                            border-radius: 50%; 
                            box-shadow: 0 0 40px rgba(138, 110, 255, 0.8),
                                        0 0 80px rgba(138, 110, 255, 0.4),
                                        0 0 0 8px rgba(138, 110, 255, 0.2),
                                        0 0 0 16px rgba(138, 110, 255, 0.1),
                                        inset 0 0 20px rgba(255, 255, 255, 0.1);
                            position: relative;
                            animation: float 3s ease-in-out infinite, glow 2s ease-in-out infinite;">
                    <img src="data:image/png;base64,{logo_base64}" 
                         alt="Midad Books" 
                         width="{width}"
                         style="border-radius: 50%; border: 4px solid rgba(255, 255, 255, 0.3); display: block;
                                filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.5));">
                </div>
            </div>
            <style>
                @keyframes float {{
                    0%, 100% {{ transform: translateY(0px); }}
                    50% {{ transform: translateY(-12px); }}
                }}
                @keyframes glow {{
                    0%, 100% {{ 
                        box-shadow: 0 0 40px rgba(138, 110, 255, 0.8),
                                    0 0 80px rgba(138, 110, 255, 0.4),
                                    0 0 0 8px rgba(138, 110, 255, 0.2),
                                    0 0 0 16px rgba(138, 110, 255, 0.1),
                                    inset 0 0 20px rgba(255, 255, 255, 0.1);
                    }}
                    50% {{ 
                        box-shadow: 0 0 60px rgba(138, 110, 255, 1),
                                    0 0 120px rgba(138, 110, 255, 0.6),
                                    0 0 0 8px rgba(138, 110, 255, 0.3),
                                    0 0 0 16px rgba(138, 110, 255, 0.15),
                                    inset 0 0 30px rgba(255, 255, 255, 0.2);
                    }}
                }}
            </style>
            ''',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            """
            <div style="text-align: center; padding: 25px 0 15px 0; margin-bottom: 10px;">
                <div style="display: inline-block; width: 130px; height: 130px; 
                            background: linear-gradient(135deg, #8a6eff 0%, #5836b3 100%);
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            box-shadow: 0 0 40px rgba(138, 110, 255, 0.8),
                                        0 0 80px rgba(138, 110, 255, 0.4),
                                        0 0 0 8px rgba(138, 110, 255, 0.2),
                                        0 0 0 16px rgba(138, 110, 255, 0.1),
                                        inset 0 0 20px rgba(255, 255, 255, 0.1);
                            animation: float 3s ease-in-out infinite, glow 2s ease-in-out infinite;">
                    <span style="font-size: 65px; line-height: 1; 
                                 filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.5));">📚</span>
                </div>
            </div>
            <style>
                @keyframes float {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-12px); }
                }
                @keyframes glow {
                    0%, 100% { 
                        box-shadow: 0 0 40px rgba(138, 110, 255, 0.8),
                                    0 0 80px rgba(138, 110, 255, 0.4),
                                    0 0 0 8px rgba(138, 110, 255, 0.2),
                                    0 0 0 16px rgba(138, 110, 255, 0.1),
                                    inset 0 0 20px rgba(255, 255, 255, 0.1);
                    }
                    50% { 
                        box-shadow: 0 0 60px rgba(138, 110, 255, 1),
                                    0 0 120px rgba(138, 110, 255, 0.6),
                                    0 0 0 8px rgba(138, 110, 255, 0.3),
                                    0 0 0 16px rgba(138, 110, 255, 0.15),
                                    inset 0 0 30px rgba(255, 255, 255, 0.2);
                    }
                }
            </style>
            """,
            unsafe_allow_html=True,
        )


def render_title():
    """Render elegant app title with neon effect."""
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding: 0 0 25px 0;">
            <h1 style="background: linear-gradient(135deg, #b8b8ff 0%, #8a6eff 100%);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       background-clip: text;
                       margin: 0 0 8px 0; font-size: 32px; font-weight: 900; 
                       letter-spacing: -1px;
                       filter: drop-shadow(0 0 10px rgba(138, 110, 255, 0.5));">
                Midad Books
            </h1>
            <p style="color: #b8b8ff; font-size: 20px; margin: 0 0 12px 0; font-weight: 700; 
                      font-family: 'Arial', sans-serif; opacity: 0.9;
                      text-shadow: 0 0 20px rgba(138, 110, 255, 0.5);">
                كتب مداد
            </p>
            <div style="width: 80px; height: 4px; 
                        background: linear-gradient(90deg, #8a6eff 0%, #5836b3 100%); 
                        margin: 15px auto; border-radius: 3px;
                        box-shadow: 0 0 20px rgba(138, 110, 255, 0.8);"></div>
            <p style="color: #9e9e9e; font-size: 10px; margin: 12px 0 0 0; text-transform: uppercase; 
                      letter-spacing: 2px; font-weight: 700;">
                Arabic Literature
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats_card(stats: dict):
    """Render premium dark mode stats cards with neon glow."""
    st.sidebar.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h3 style="color: #b8b8ff; font-size: 12px; font-weight: 800; margin: 0 0 16px 0; 
                       text-transform: uppercase; letter-spacing: 1.5px; padding-left: 2px;
                       text-shadow: 0 0 10px rgba(138, 110, 255, 0.5);">
                📊 Quick Stats
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Row 1 - Books with dark neon effect
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #8a6eff 0%, #5836b3 100%); 
                        padding: 18px 12px; border-radius: 16px; text-align: center;
                        box-shadow: 0 8px 32px rgba(138, 110, 255, 0.5),
                                    0 0 40px rgba(138, 110, 255, 0.3),
                                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                        transition: all 0.3s ease;
                        cursor: pointer;
                        position: relative;
                        overflow: hidden;
                        border: 1px solid rgba(255, 255, 255, 0.1);">
                <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%;
                            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
                <div style="color: rgba(255,255,255,0.95); font-size: 9px; font-weight: 800; 
                            letter-spacing: 1px; margin-bottom: 8px; position: relative;">
                    📚 ACTIVE
                </div>
                <div style="color: white; font-size: 32px; font-weight: 900; line-height: 1; position: relative;
                            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);">
                    {stats['active_count']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #c93f9e 100%); 
                        padding: 18px 12px; border-radius: 16px; text-align: center;
                        box-shadow: 0 8px 32px rgba(240, 147, 251, 0.5),
                                    0 0 40px rgba(240, 147, 251, 0.3),
                                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                        position: relative; overflow: hidden;
                        border: 1px solid rgba(255, 255, 255, 0.1);">
                <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%;
                            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
                <div style="color: rgba(255,255,255,0.95); font-size: 9px; font-weight: 800; 
                            letter-spacing: 1px; margin-bottom: 8px; position: relative;">
                    ✅ SOLD
                </div>
                <div style="color: white; font-size: 32px; font-weight: 900; line-height: 1; position: relative;
                            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);">
                    {stats['sold_count']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.sidebar.markdown("<div style='margin: 14px 0;'></div>", unsafe_allow_html=True)
    
    # Row 2 - Financial
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 18px 12px; border-radius: 16px; text-align: center;
                        box-shadow: 0 8px 32px rgba(79, 172, 254, 0.5),
                                    0 0 40px rgba(79, 172, 254, 0.3),
                                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                        position: relative; overflow: hidden;
                        border: 1px solid rgba(255, 255, 255, 0.1);">
                <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%;
                            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
                <div style="color: rgba(255,255,255,0.95); font-size: 9px; font-weight: 800; 
                            letter-spacing: 1px; margin-bottom: 8px; position: relative;">
                    💰 REVENUE
                </div>
                <div style="color: white; font-size: 20px; font-weight: 900; line-height: 1; position: relative;
                            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);">
                    €{stats['revenue']:.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                        padding: 18px 12px; border-radius: 16px; text-align: center;
                        box-shadow: 0 8px 32px rgba(67, 233, 123, 0.5),
                                    0 0 40px rgba(67, 233, 123, 0.3),
                                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                        position: relative; overflow: hidden;
                        border: 1px solid rgba(255, 255, 255, 0.1);">
                <div style="position: absolute; top: -50%; right: -50%; width: 200%; height: 200%;
                            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
                <div style="color: rgba(255,255,255,0.95); font-size: 9px; font-weight: 800; 
                            letter-spacing: 1px; margin-bottom: 8px; position: relative;">
                    📈 PROFIT
                </div>
                <div style="color: white; font-size: 20px; font-weight: 900; line-height: 1; position: relative;
                            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);">
                    €{stats['profit']:.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    # Stock summary with dark glassmorphism
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; margin-top: 16px; padding: 14px; 
                    background: rgba(138, 110, 255, 0.1); 
                    backdrop-filter: blur(20px);
                    border-radius: 12px; 
                    border: 2px solid rgba(138, 110, 255, 0.3);
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
                                0 0 40px rgba(138, 110, 255, 0.2);">
            <p style="margin: 0; color: #b8b8ff; font-size: 11px; font-weight: 700;">
                📦 Total Stock: <strong style="background: linear-gradient(135deg, #b8b8ff 0%, #8a6eff 100%);
                                               -webkit-background-clip: text;
                                               -webkit-text-fill-color: transparent;
                                               background-clip: text;
                                               font-size: 16px; font-weight: 900;
                                               filter: drop-shadow(0 0 10px rgba(138, 110, 255, 0.8));">{stats['total_stock']}</strong> books
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, icon: str = "📚"):
    """Render beautiful dark mode page header with neon gradient."""
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, 
                        rgba(138, 110, 255, 0.2) 0%, 
                        rgba(88, 54, 179, 0.2) 100%); 
                    backdrop-filter: blur(20px);
                    padding: 35px 30px; border-radius: 16px; margin-bottom: 30px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5),
                                0 0 60px rgba(138, 110, 255, 0.3);
                    border: 1px solid rgba(138, 110, 255, 0.3);">
            <h1 style="color: #f0f0f0; margin: 0; font-size: 36px; font-weight: 900; 
                       letter-spacing: -0.5px;
                       text-shadow: 0 0 30px rgba(138, 110, 255, 0.8);">{icon} {title}</h1>
            <p style="color: #e0e0e0; margin: 12px 0 0 0; font-size: 16px; 
                      font-weight: 400; line-height: 1.5; opacity: 0.9;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alerts(low_stock: list, recent_sales: list, week_range: str):
    """Render alerts section with better design."""
    st.sidebar.markdown("<div style='margin: 20px 0 15px 0;'></div>", unsafe_allow_html=True)
    
    st.sidebar.markdown(
        """
        <h3 style="color: #495057; font-size: 14px; font-weight: 600; margin: 0 0 10px 0; 
                   text-transform: uppercase; letter-spacing: 0.5px;">
            ⚡ Alerts & Activity
        </h3>
        """,
        unsafe_allow_html=True
    )
    
    if low_stock:
        st.sidebar.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%); 
                        padding: 10px 12px; border-radius: 6px; 
                        border-left: 3px solid #ff9800; margin-bottom: 8px;
                        box-shadow: 0 2px 4px rgba(255, 152, 0, 0.2);">
                <p style="margin: 0; color: #856404; font-size: 12px; font-weight: 600;">
                    ⚠️ {len(low_stock)} book(s) low stock
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.sidebar.expander("📉 View Details", expanded=False):
            for book in low_stock[:5]:
                st.caption(f"• **{book['title'][:22]}{'...' if len(book['title']) > 22 else ''}** — {book['stock']} left")
    else:
        st.sidebar.markdown(
            """
            <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                        padding: 10px 12px; border-radius: 6px; 
                        border-left: 3px solid #28a745;
                        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);">
                <p style="margin: 0; color: #155724; font-size: 12px; font-weight: 600;">
                    ✅ Stock levels healthy
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    if recent_sales:
        st.sidebar.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); 
                        padding: 10px 12px; border-radius: 6px; 
                        border-left: 3px solid #17a2b8; margin-top: 8px;
                        box-shadow: 0 2px 4px rgba(23, 162, 184, 0.2);">
                <p style="margin: 0; color: #0c5460; font-size: 12px; font-weight: 600;">
                    🔥 {len(recent_sales)} book(s) sold this week
                </p>
                <p style="margin: 3px 0 0 0; color: #0c5460; font-size: 10px;">
                    {week_range}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_footer():
    """Render simple footer."""
    st.sidebar.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: #adb5bd; font-size: 10px; padding-top: 15px; 
                    border-top: 1px solid #e9ecef;">
            <p style="margin: 3px 0;">Midad Books</p>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_info_banner(message: str, type: str = "info"):
    """Render colorful info banner with modern gradients."""
    colors = {
        "info": {"bg": "linear-gradient(135deg, #cfe2ff 0%, #c5d9f5 100%)", "border": "#0d6efd", "text": "#084298", "icon": "ℹ️"},
        "success": {"bg": "linear-gradient(135deg, #d1e7dd 0%, #c3e6cb 100%)", "border": "#198754", "text": "#0f5132", "icon": "✅"},
        "warning": {"bg": "linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%)", "border": "#ffc107", "text": "#856404", "icon": "⚠️"},
        "error": {"bg": "linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%)", "border": "#dc3545", "text": "#842029", "icon": "❌"},
    }
    
    style = colors.get(type, colors["info"])
    
    st.markdown(
        f"""
        <div style="background: {style['bg']}; 
                    padding: 12px 16px; 
                    border-radius: 8px; 
                    border-left: 3px solid {style['border']}; 
                    margin: 12px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
            <p style="margin: 0; color: {style['text']}; font-size: 13px; font-weight: 500;">
                {style['icon']} {message}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, icon: str = "📋"):
    """Render section header with modern styling."""
    st.markdown(
        f"""
        <h3 style="color: #495057; margin: 20px 0 12px 0; font-size: 20px; font-weight: 600;
                   border-bottom: 2px solid #e9ecef; padding-bottom: 6px;">
            {icon} {title}
        </h3>
        """,
        unsafe_allow_html=True,
    )


def load_custom_css():
    """Load custom CSS for enhanced styling with modern colors."""
    st.markdown(
        """
        <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Sidebar improvements */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        }
        
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }
        
        /* Better radio buttons (navigation) */
        .stRadio > div {
            gap: 8px;
        }
        
        .stRadio > div > label {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 12px 16px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            color: #495057;
            width: 100%;
            display: block;
        }
        
        .stRadio > div > label:hover {
            border-color: #667eea;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            transform: translateX(3px);
        }
        
        .stRadio > div > label[data-baseweb="radio"] > div:first-child {
            display: none;
        }
        
        /* Selected radio button */
        .stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
            font-size: 14px;
            margin: 0;
        }
        
        /* Better buttons with gradient */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Secondary buttons */
        .stButton > button[kind="secondary"] {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
        }
        
        /* Better data editor */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        /* Smooth animations */
        .element-container {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(8px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        /* Better tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
            font-weight: 600;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            font-size: 14px;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        /* Better selectbox */
        .stSelectbox > div > div {
            border-radius: 8px;
            border: 2px solid #e9ecef;
            transition: border 0.3s ease;
        }
        
        .stSelectbox > div > div:hover,
        .stSelectbox > div > div:focus-within {
            border-color: #667eea;
        }
        
        /* Better number input */
        .stNumberInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e9ecef;
            transition: border 0.3s ease;
        }
        
        .stNumberInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Better text input */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid #e9ecef;
            transition: border 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Better metrics */
        [data-testid="stMetricValue"] {
            font-size: 26px;
            font-weight: 700;
            color: #212529;
        }
        
        /* Better expander */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            font-weight: 600;
            padding: 12px;
        }
        
        /* Success messages */
        .stSuccess {
            background: linear-gradient(135deg, #d1e7dd 0%, #c3e6cb 100%);
            border-left: 4px solid #28a745;
            border-radius: 8px;
            padding: 12px;
        }
        
        /* Error messages */
        .stError {
            background: linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%);
            border-left: 4px solid #dc3545;
            border-radius: 8px;
            padding: 12px;
        }
        
        /* Warning messages */
        .stWarning {
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
            border-left: 4px solid #ffc107;
            border-radius: 8px;
            padding: 12px;
        }
        
        /* Info messages */
        .stInfo {
            background: linear-gradient(135deg, #cfe2ff 0%, #c5d9f5 100%);
            border-left: 4px solid #0d6efd;
            border-radius: 8px;
            padding: 12px;
        }
        
        /* Better spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Compact sidebar */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )