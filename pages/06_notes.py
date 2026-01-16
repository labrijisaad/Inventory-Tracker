"""
📝 Notes Page
Notes with titles, content, and multiple file uploads - Card Style
"""
from datetime import datetime

import streamlit as st

from src.data.notes_manager import add_note, delete_note, get_file_path, load_notes
from src.ui.components import render_page_header
from src.ui.sidebar import render_sidebar
from src.ui.styles import load_custom_css

st.set_page_config(
    page_title="Notes - Midad Books",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
load_custom_css()
st.session_state.current_page = "Notes"
render_sidebar()

# Page Header
render_page_header(
    "Notes",
    "Quick notes with titles and file uploads",
    "📝"
)

# ============================================================================
# SESSION STATE
# ============================================================================
if 'note_to_delete' not in st.session_state:
    st.session_state.note_to_delete = None
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# ============================================================================
# PROCESS DELETION
# ============================================================================
if st.session_state.note_to_delete is not None:
    if delete_note(st.session_state.note_to_delete):
        st.success("✅ Note deleted successfully!")
        st.session_state.note_to_delete = None
        st.session_state.confirm_delete = None
        st.rerun()

# Load notes
all_notes = load_notes()
notes_sorted = sorted(all_notes, key=lambda x: x['date'], reverse=True)

# ============================================================================
# METRICS & SEARCH
# ============================================================================
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.metric("📝 Total Notes", len(all_notes))

with col2:
    files_count = sum(1 for n in all_notes if n.get('files'))
    st.metric("📎 With Files", files_count)

with col3:
    search_query = st.text_input(
        "🔍 Search notes",
        value=st.session_state.search_query,
        placeholder="Search by title or content...",
        label_visibility="collapsed"
    )
    st.session_state.search_query = search_query

st.markdown("---")

# ============================================================================
# ADD NEW NOTE
# ============================================================================
with st.expander("➕ Add New Note", expanded=False):
    with st.form("add_note", clear_on_submit=False):  # ✅ Never auto-clear
        note_title = st.text_input(
            "Title *",
            placeholder="e.g., Customer Request, Draft Message, Book Idea...",
            help="Short descriptive title",
            key="form_title"
        )

        note_content = st.text_area(
            "Content *",
            placeholder="Write your note here... (Markdown supported)",
            height=150,
            help="Main note content. You can use **bold**, *italic*, etc.",
            key="form_content"
        )

        uploaded_files = st.file_uploader(
            "📎 Attach Files (optional)",
            type=['jpg', 'jpeg', 'png', 'pdf', 'txt', 'doc', 'docx', 'xlsx'],
            help="Upload one or more files. Single images show as preview.",
            accept_multiple_files=True
        )

        submit = st.form_submit_button("✅ Add Note", width='stretch', type="primary")

        if submit:
            errors = []
            if not note_title.strip():
                errors.append("Title is required")
            if not note_content.strip():
                errors.append("Content is required")

            if errors:
                # ✅ SHOW ERRORS BUT DON'T CLEAR FORM
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # ✅ SUCCESS - ADD NOTE BUT DON'T CLEAR FORM!
                add_note(note_title, note_content, uploaded_files)
                st.success("✅ Note added! Form kept for quick entry.")
                # ✅ DON'T DELETE SESSION STATE - Keep the text!
                # User can manually clear if they want
                st.rerun()
st.markdown("---")

# ============================================================================
# FILTER NOTES BY SEARCH
# ============================================================================
if search_query:
    filtered_notes = [
        n for n in notes_sorted
        if search_query.lower() in n.get('title', '').lower()
        or search_query.lower() in n.get('content', '').lower()
    ]
    st.caption(f"Found {len(filtered_notes)} note(s) matching '{search_query}'")
else:
    filtered_notes = notes_sorted

# ============================================================================
# DISPLAY NOTES - CARD STYLE
# ============================================================================
if filtered_notes:
    for note in filtered_notes:
        # Get files
        files = note.get('files', [])
        if not isinstance(files, list):
            files = [files] if files else []

        # Check for single image
        show_image = False
        image_path = None

        if len(files) == 1:
            file_path = get_file_path(files[0])
            if file_path.exists() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                show_image = True
                image_path = file_path

        # ============ NOTE CARD ============
        with st.container(border=True):
            # Header with date and actions
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                date_str = datetime.strptime(note['date'], "%Y-%m-%d %H:%M:%S")
                date_display = date_str.strftime("%d/%m/%Y %H:%M")

                file_badge = ""
                if len(files) > 1:
                    file_badge = f" | 📎 {len(files)} files"
                elif len(files) == 1:
                    file_badge = " | 📎 1 file"

                st.markdown(f"📅 `{date_display}`")
                st.markdown(f"💮 Note **`N°{note['id']}`**{file_badge}")

            with col2:
                if files:
                    file_path = get_file_path(files[0])
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            st.download_button(
                                "Download",
                                f,
                                file_name=files[0],
                                key=f"download_{note['id']}"
                            )

            with col3:
                if st.session_state.confirm_delete == note['id']:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Delete", key=f"confirm_{note['id']}", type="primary"):
                            st.session_state.note_to_delete = note['id']
                            st.rerun()
                    with col_b:
                        if st.button("Keep", key=f"cancel_{note['id']}"):
                            st.session_state.confirm_delete = None
                            st.rerun()
                else:
                    if st.button("Delete", key=f"delete_{note['id']}"):
                        st.session_state.confirm_delete = note['id']
                        st.rerun()

            st.markdown("---")

            # ============ CONTENT LAYOUT ============
            if show_image:
                # ✅ TWO COLUMNS: Content + Image
                col_content, col_image = st.columns([2, 1])

                with col_content:
                    # Title
                    st.markdown(f"### 📌 {note.get('title', 'Untitled')}")
                    st.markdown("")
                    # Content
                    st.markdown(note.get('content', ''))

                with col_image:
                    # ✅ IMAGE CARD with border
                    st.markdown(
                        """
                        <div style="
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            padding: 8px;
                            background: #f9f9f9;
                        ">
                        """,
                        unsafe_allow_html=True
                    )
                    # ✅ Show image with container width
                    st.image(
                        str(image_path),
                        width='stretch'
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.caption(f"📷 {files[0]}")

            else:
                # ✅ FULL WIDTH: No image or multiple files
                # Title
                st.markdown(f"### 📌 {note.get('title', 'Untitled')}")
                st.markdown("")
                # Content
                st.markdown(note.get('content', ''))

                # ✅ SHOW FILES LIST
                if files:
                    st.markdown("")
                    st.markdown("**📎 Attached Files:**")

                    for idx, filename in enumerate(files, 1):
                        file_path = get_file_path(filename)
                        if file_path.exists():
                            # File icon
                            file_ext = file_path.suffix.lower()
                            icon_map = {
                                '.pdf': '📄',
                                '.doc': '📝', '.docx': '📝',
                                '.txt': '📃',
                                '.xlsx': '📊', '.xls': '📊',
                                '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️'
                            }
                            icon = icon_map.get(file_ext, '📎')

                            # File row
                            col_file, col_btn = st.columns([4, 1])
                            with col_file:
                                st.markdown(f"{icon} `{filename}`")
                            with col_btn:
                                with open(file_path, "rb") as f:
                                    st.download_button(
                                        "Download",
                                        f,
                                        file_name=filename,
                                        key=f"download_{note['id']}_{idx}"
                                    )

else:
    if search_query:
        st.info(f"🔍 No notes found matching '{search_query}'")
    else:
        st.info("📝 No notes yet. Add your first note above!")

# Footer
st.markdown("---")
st.caption("💡 **Tip:** Upload multiple files! Single images show as preview cards. Multiple files show as a list.")
