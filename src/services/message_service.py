"""
Message Service
Business logic for quick messages management
"""

import time

import streamlit as st

from src.config import MESSAGE_CATEGORIES
from src.data.database import (
    add_quick_message,
    delete_quick_message,
    get_quick_messages,
    update_quick_message,
)
from src.ui.components import render_info_banner, render_page_header, render_section_header
from src.utils.helpers import show_error_toast, show_success_toast


def render_messages_page():
    """Main messages page."""
    render_page_header(
        "💬 Quick Messages",
        "Create and manage message templates for faster customer communication"
    )

    render_info_banner(
        "💡 Save time by creating reusable message templates. Click any message to view, edit, or delete.",
        type="info"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
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

    # ✅ Stats bar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Messages", len(messages))
    with col2:
        categories = len(set(m['category'] for m in messages))
        st.metric("📁 Categories", categories)
    with col3:
        recent = sum(1 for m in messages if m['updated_at'] == m['created_at'])
        st.metric("✨ Recently Added", recent)

    st.markdown("<br>", unsafe_allow_html=True)

    # ✅ Render messages
    for msg in messages:
        _render_message_card(msg)


def _render_message_card(msg: dict):
    """Render a single message card."""
    # ✅ Better expander title with category badge
    with st.expander(f"**{msg['title']}** `{msg['category']}`", expanded=False):

        # ✅ Show message in text area
        st.text_area(
            "Message Content",
            value=msg['message'],
            height=180,
            key=f"preview_{msg['id']}",
            disabled=True,
            label_visibility="collapsed"
        )

        # ✅ Metadata
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            st.caption(f"🕒 Created: {msg['created_at']}")
        with col_meta2:
            st.caption(f"📝 Updated: {msg['updated_at']}")

        st.markdown("---")

        # ✅ Action buttons (NO COPY BUTTON)
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✏️ Edit", key=f"edit_btn_{msg['id']}", width='stretch'):
                st.session_state[f"editing_{msg['id']}"] = True
                st.rerun()

        with col2:
            if st.button("🗑️ Delete", key=f"del_{msg['id']}", type="secondary", width='stretch'):
                st.session_state[f"confirm_delete_{msg['id']}"] = True
                st.rerun()

        # ✅ Delete confirmation
        if st.session_state.get(f"confirm_delete_{msg['id']}", False):
            st.warning(f"⚠️ Delete **{msg['title']}**? This cannot be undone.")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Yes, Delete", key=f"confirm_del_{msg['id']}", type="primary", width='stretch'):
                    with st.spinner("Deleting..."):
                        success, result_msg = delete_quick_message(msg['id'])
                        if success:
                            show_success_toast("Message deleted")
                            # Clean up session state
                            for key in list(st.session_state.keys()):
                                if str(msg['id']) in key:
                                    del st.session_state[key]
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            show_error_toast(result_msg)
                            st.error(result_msg)
            with col_b:
                if st.button("❌ Cancel", key=f"cancel_del_{msg['id']}", width='stretch'):
                    st.session_state[f"confirm_delete_{msg['id']}"] = False
                    st.rerun()

        # ✅ Edit form
        if st.session_state.get(f"editing_{msg['id']}", False):
            _render_edit_form(msg)


def _render_edit_form(msg: dict):
    """Render edit form for a message."""
    st.markdown("---")
    st.markdown("### ✏️ Edit Message")

    edit_title = st.text_input(
        "Title*",
        value=msg['title'],
        key=f"edit_title_{msg['id']}",
        placeholder="e.g., Welcome Message"
    )

    edit_category = st.selectbox(
        "Category*",
        MESSAGE_CATEGORIES,
        index=MESSAGE_CATEGORIES.index(msg['category']) if msg['category'] in MESSAGE_CATEGORIES else 0,
        key=f"edit_cat_{msg['id']}"
    )

    edit_message = st.text_area(
        "Message Content*",
        value=msg['message'],
        height=220,
        key=f"edit_msg_{msg['id']}",
        placeholder="Your message here..."
    )

    # ✅ Character count
    char_count = len(edit_message)
    st.caption(f"📝 {char_count} characters")

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("💾 Save Changes", key=f"save_edit_{msg['id']}", type="primary", width='stretch'):
            if not edit_title.strip():
                show_error_toast("Title is required")
                st.error("❌ Please enter a title")
            elif not edit_message.strip():
                show_error_toast("Message is required")
                st.error("❌ Please enter a message")
            else:
                with st.spinner("Saving..."):
                    success, result_msg = update_quick_message(
                        msg['id'], edit_title, edit_category, edit_message
                    )
                    if success:
                        show_success_toast("Message updated!")
                        st.success(result_msg)
                        # ✅ Clean up session state
                        del st.session_state[f"editing_{msg['id']}"]
                        time.sleep(0.5)
                        # ✅ REFRESH PAGE AUTOMATICALLY
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

    st.info("💡 **Tip:** Use placeholders like `[NAME]`, `[BOOK]`, `[PRICE]` for dynamic content")

    st.markdown("<br>", unsafe_allow_html=True)

    new_title = st.text_input(
        "Message Title*",
        placeholder="e.g., Welcome Message, Shipping Notification",
        key="new_msg_title",
        help="A short, descriptive title for this message"
    )

    new_category = st.selectbox(
        "Category*",
        MESSAGE_CATEGORIES,
        key="new_msg_category",
        help="Organize messages by type"
    )

    new_message = st.text_area(
        "Message Content*",
        placeholder="Type your message here...\n\nExample:\nHello [NAME],\n\nThank you for purchasing [BOOK]...",
        height=280,
        key="new_msg_content",
        help="The full message text"
    )

    # ✅ Character count
    if new_message:
        char_count = len(new_message)
        st.caption(f"📝 {char_count} characters")

    st.markdown("<br>", unsafe_allow_html=True)

    # ✅ Preview section
    if new_message.strip():
        render_section_header("Preview", "👁️")
        st.text_area(
            "How it will look:",
            value=new_message,
            height=150,
            key="preview_new",
            disabled=True,
            label_visibility="collapsed"
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
                        # ✅ REFRESH PAGE AUTOMATICALLY
                        st.rerun()
                    else:
                        show_error_toast(result_msg)
                        st.error(result_msg)

    with col2:
        if st.button("🔄 Clear", width='stretch', key="clear_new_msg"):
            st.rerun()
