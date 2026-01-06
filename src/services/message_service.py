"""
Message Service
Business logic for quick messages management
"""

import time
import streamlit as st

from src.data.database import (
    get_quick_messages,
    add_quick_message,
    update_quick_message,
    delete_quick_message,
)
from src.ui.components import render_page_header, render_info_banner, render_section_header
from src.config import MESSAGE_CATEGORIES
from src.utils.helpers import show_success_toast, show_error_toast


def render_messages_page():
    """Main messages page."""
    render_page_header(
        "Quick Messages",
        "Manage message templates for customer communication"
    )
    
    render_info_banner(
        "💡 Create, edit, and delete message templates. Click 'Copy' to use any message.",
        type="info"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for viewing and adding
    msg_tab1, msg_tab2 = st.tabs(["📋 All Messages", "➕ Add New Message"])
    
    with msg_tab1:
        _render_all_messages_tab()
    
    with msg_tab2:
        _render_add_message_tab()


def _render_all_messages_tab():
    """Render all messages list."""
    messages = get_quick_messages()
    
    if not messages:
        st.info("📝 No messages yet. Add your first message in the 'Add New Message' tab!")
        return
    
    st.success(f"📊 {len(messages)} message(s) saved")
    
    # Filter by category
    all_categories = sorted(set(m['category'] for m in messages))
    selected_category = st.selectbox(
        "Filter by Category",
        ["All"] + all_categories,
        key="category_filter"
    )
    
    filtered_messages = messages if selected_category == "All" else [
        m for m in messages if m['category'] == selected_category
    ]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    for msg in filtered_messages:
        _render_message_card(msg)


def _render_message_card(msg: dict):
    """Render a single message card."""
    with st.expander(f"{msg['title']} ({msg['category']})", expanded=False):
        # Display message
        st.text_area(
            "Message Preview",
            value=msg['message'],
            height=200,
            key=f"preview_{msg['id']}",
            disabled=True
        )
        
        st.caption(f"🕒 Created: {msg['created_at']} • Updated: {msg['updated_at']}")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("📋 Copy to Clipboard", key=f"copy_{msg['id']}", width='stretch'):
                st.code(msg['message'], language=None)
                show_success_toast("Message displayed! Select and copy (Ctrl+C)")
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_btn_{msg['id']}", width='stretch'):
                st.session_state[f"editing_{msg['id']}"] = True
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", key=f"del_{msg['id']}", type="secondary", width='stretch'):
                with st.spinner("Deleting..."):
                    success, result_msg = delete_quick_message(msg['id'])
                    if success:
                        show_success_toast("Message deleted")
                        st.success(result_msg)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        show_error_toast(result_msg)
                        st.error(result_msg)
        
        # Edit form (shown when edit clicked)
        if st.session_state.get(f"editing_{msg['id']}", False):
            _render_edit_form(msg)


def _render_edit_form(msg: dict):
    """Render edit form for a message."""
    st.markdown("---")
    st.markdown("### ✏️ Edit Message")
    
    edit_title = st.text_input(
        "Title",
        value=msg['title'],
        key=f"edit_title_{msg['id']}"
    )
    
    edit_category = st.selectbox(
        "Category",
        MESSAGE_CATEGORIES,
        index=MESSAGE_CATEGORIES.index(msg['category']) if msg['category'] in MESSAGE_CATEGORIES else 0,
        key=f"edit_cat_{msg['id']}"
    )
    
    edit_message = st.text_area(
        "Message",
        value=msg['message'],
        height=200,
        key=f"edit_msg_{msg['id']}"
    )
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("💾 Save Changes", key=f"save_edit_{msg['id']}", type="primary", width='stretch'):
            with st.spinner("Saving..."):
                success, result_msg = update_quick_message(
                    msg['id'], edit_title, edit_category, edit_message
                )
                if success:
                    show_success_toast("Message updated")
                    st.success(result_msg)
                    del st.session_state[f"editing_{msg['id']}"]
                    time.sleep(0.5)
                    st.rerun()
                else:
                    show_error_toast(result_msg)
                    st.error(result_msg)
    
    with col_b:
        if st.button("❌ Cancel", key=f"cancel_edit_{msg['id']}", width='stretch'):
            del st.session_state[f"editing_{msg['id']}"]
            st.rerun()


def _render_add_message_tab():
    """Render add new message form."""
    render_section_header("Create New Message Template", "✍️")
    
    new_title = st.text_input(
        "Message Title",
        placeholder="e.g., Welcome Message, Shipping Notification",
        key="new_msg_title"
    )
    
    new_category = st.selectbox(
        "Category",
        MESSAGE_CATEGORIES,
        key="new_msg_category"
    )
    
    new_message = st.text_area(
        "Your Message",
        placeholder="Type your message here...\n\nTip: Use placeholders like [NAME], [BOOK], [PRICE]",
        height=250,
        key="new_msg_content"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("💾 Save Message", type="primary", width='stretch', key="save_new_msg"):
            if not new_title.strip():
                show_error_toast("Title is required")
                st.error("❌ Please enter a title")
            elif not new_message.strip():
                show_error_toast("Message is required")
                st.error("❌ Please enter a message")
            else:
                with st.spinner("Saving message..."):
                    success, result_msg = add_quick_message(new_title, new_category, new_message)
                    if success:
                        show_success_toast("Message saved!")
                        st.success(result_msg)
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        show_error_toast(result_msg)
                        st.error(result_msg)
    
    with col2:
        if st.button("🔄 Clear", width='stretch', key="clear_new_msg"):
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Preview
    if new_message.strip():
        render_section_header("Preview", "👁️")
        st.code(new_message, language=None)