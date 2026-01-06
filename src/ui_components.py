"""
UI Components for Midad Books
Beautiful, reusable interface elements
كتب مداد - مكونات الواجهة
"""

import streamlit as st
import base64
from pathlib import Path


def image_to_base64(image_path: str) -> str:
    """Convert image to base64 for embedding in HTML."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


def render_logo(logo_path: str = "assets/logo.png", width: int = 100):
    """Render centered logo in sidebar."""
    if Path(logo_path).exists():
        logo_base64 = image_to_base64(logo_path)
        st.sidebar.markdown(
            f'''
            <div style="text-align: center; padding: 20px 0 10px 0;">
                <img src="data:image/png;base64,{logo_base64}" 
                     alt="Midad Books Logo" 
                     width="{width}"
                     style="border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            </div>
            ''',
            unsafe_allow_html=True,
        )
    else:
        # Fallback to emoji logo
        st.sidebar.markdown(
            """
            <div style="text-align: center; font-size: 70px; padding: 20px 0 10px 0;">
                📚
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_title():
    """Render beautiful app title."""
    st.sidebar.markdown(
        """
        <div style="text-align: center;">
            <h1 style="color: #667eea; margin: 0; font-size: 28px;">Midad Books</h1>
            <p style="color: #764ba2; font-size: 16px; margin: 5px 0; font-weight: 500;">كتب مداد</p>
            <p style="color: #999; font-size: 11px; margin: 0; text-transform: uppercase; letter-spacing: 1px;">Arabic Literature Management</p>
        </div>
        <hr style="margin: 20px 0; border: none; border-top: 1px solid #e0e0e0;">
        """,
        unsafe_allow_html=True,
    )


def render_stats_card(stats: dict):
    """Render beautiful stats cards in sidebar with modern colors."""
    st.sidebar.markdown("### 📊 Quick Stats")
    
    # Row 1 - Modern vibrant gradients
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
                        transition: transform 0.2s;">
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 11px; font-weight: 600;">📚 ACTIVE</p>
                <h2 style="color: white; margin: 8px 0 0 0; font-size: 28px;">{stats['active_count']}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 6px rgba(245, 87, 108, 0.3);">
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 11px; font-weight: 600;">✅ SOLD</p>
                <h2 style="color: white; margin: 8px 0 0 0; font-size: 28px;">{stats['sold_count']}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # Row 2 - Eye-catching colors
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 6px rgba(79, 172, 254, 0.3);">
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 11px; font-weight: 600;">💰 REVENUE</p>
                <h3 style="color: white; margin: 8px 0 0 0; font-size: 20px;">€{stats['revenue']:.0f}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                        padding: 15px; border-radius: 10px; text-align: center;
                        box-shadow: 0 4px 6px rgba(67, 233, 123, 0.3);">
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 11px; font-weight: 600;">📈 PROFIT</p>
                <h3 style="color: white; margin: 8px 0 0 0; font-size: 20px;">€{stats['profit']:.0f}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; margin-top: 15px; padding: 12px; 
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                    border-radius: 8px; border: 1px solid #e9ecef;">
            <small style="color: #495057;">📦 Total Stock: <strong style="color: #212529;">{stats['total_stock']}</strong> books</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alerts(low_stock: list, recent_sales: list, week_range: str):
    """Render alerts section with better colors and week range."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Alerts & Activity")
    
    if low_stock:
        st.sidebar.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%); 
                        padding: 12px; border-radius: 8px; 
                        border-left: 4px solid #ff9800; margin-bottom: 10px;
                        box-shadow: 0 2px 4px rgba(255, 152, 0, 0.2);">
                <p style="margin: 0; color: #856404; font-size: 13px; font-weight: 600;">
                    ⚠️ <strong>{len(low_stock)}</strong> book(s) low stock!
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.sidebar.expander("📉 View Low Stock Books"):
            for book in low_stock[:5]:
                st.caption(f"• **{book['title'][:25]}{'...' if len(book['title']) > 25 else ''}** - {book['stock']} left")
    else:
        st.sidebar.markdown(
            """
            <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                        padding: 12px; border-radius: 8px; 
                        border-left: 4px solid #28a745;
                        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);">
                <p style="margin: 0; color: #155724; font-size: 13px; font-weight: 600;">
                    ✅ All stock levels healthy
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    if recent_sales:
        st.sidebar.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); 
                        padding: 12px; border-radius: 8px; 
                        border-left: 4px solid #17a2b8; margin-top: 10px;
                        box-shadow: 0 2px 4px rgba(23, 162, 184, 0.2);">
                <p style="margin: 0; color: #0c5460; font-size: 13px; font-weight: 600;">
                    🔥 <strong>{len(recent_sales)}</strong> sales this week!
                </p>
                <p style="margin: 5px 0 0 0; color: #0c5460; font-size: 11px;">
                    Week: {week_range}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_footer():
    """Render simple footer."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: #adb5bd; font-size: 11px; margin-top: 20px;">
            <p style="margin: 5px 0;">📚 Midad Books</p>
            <p style="margin: 5px 0;">© 2026 • Version 1.0.0</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, icon: str = "📚"):
    """Render beautiful page header with modern gradient."""
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 35px 30px; border-radius: 15px; margin-bottom: 30px;
                    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);">
            <h1 style="color: white; margin: 0; font-size: 36px; font-weight: 700;">{icon} {title}</h1>
            <p style="color: rgba(255,255,255,0.95); margin: 12px 0 0 0; font-size: 16px; font-weight: 400;">{subtitle}</p>
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
                    padding: 14px 18px; 
                    border-radius: 8px; 
                    border-left: 4px solid {style['border']}; 
                    margin: 15px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <p style="margin: 0; color: {style['text']}; font-size: 14px; font-weight: 500;">
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
        <h3 style="color: #495057; margin: 25px 0 15px 0; font-size: 22px; font-weight: 600;
                   border-bottom: 2px solid #e9ecef; padding-bottom: 8px;">
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
        
        /* Better buttons with gradient */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Better data editor */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        /* Smooth animations */
        .element-container {
            animation: fadeIn 0.4s ease-in;
        }
        
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(10px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        /* Better tabs with modern colors */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            font-weight: 600;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
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
        
        .stSelectbox > div > div:hover {
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
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e9ecef;
            transition: border 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Better metrics */
        [data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: 700;
            color: #212529;
        }
        
        /* Sidebar styling with gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        }
        
        /* Better radio buttons */
        .stRadio > label {
            font-weight: 600;
            color: #495057;
        }
        
        /* Success messages */
        .stSuccess {
            background: linear-gradient(135deg, #d1e7dd 0%, #c3e6cb 100%);
            border-left: 4px solid #28a745;
            border-radius: 8px;
        }
        
        /* Error messages */
        .stError {
            background: linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%);
            border-left: 4px solid #dc3545;
            border-radius: 8px;
        }
        
        /* Warning messages */
        .stWarning {
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
            border-left: 4px solid #ffc107;
            border-radius: 8px;
        }
        
        /* Info messages */
        .stInfo {
            background: linear-gradient(135deg, #cfe2ff 0%, #c5d9f5 100%);
            border-left: 4px solid #0d6efd;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )