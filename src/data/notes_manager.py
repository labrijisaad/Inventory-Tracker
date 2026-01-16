"""
Notes Manager
Simple notes with file uploads (multiple files supported)
"""
import json
from pathlib import Path
from datetime import datetime

# Data paths
DATA_DIR = Path("data")
NOTES_FILE = DATA_DIR / "notes.json"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

def load_notes() -> list[dict]:
    """Load all notes from JSON file."""
    if NOTES_FILE.exists():
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_notes(notes: list[dict]) -> None:
    """Save notes to JSON file."""
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def add_note(title: str, content: str, uploaded_files: list = None) -> dict:
    """Add a new note with title, content, and optional multiple file uploads."""
    notes = load_notes()

    # Generate new ID
    new_id = max([n['id'] for n in notes], default=0) + 1

    # Handle multiple file uploads
    filenames = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename = f"{new_id}_{uploaded_file.name}"
            file_path = UPLOADS_DIR / filename
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            filenames.append(filename)

    # Create note
    note = {
        'id': new_id,
        'title': title,
        'content': content,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'files': filenames  # Now a list instead of single filename
    }

    notes.append(note)
    save_notes(notes)
    return note

def delete_note(note_id: int) -> bool:
    """Delete a note and its associated files."""
    notes = load_notes()
    for note in notes:
        if note['id'] == note_id:
            # Delete all files if exist
            files = note.get('files', [])
            if not isinstance(files, list):
                # Handle old format (single filename)
                files = [files] if files else []

            for filename in files:
                file_path = UPLOADS_DIR / filename
                if file_path.exists():
                    file_path.unlink()

            # Remove note
            notes.remove(note)
            save_notes(notes)
            return True
    return False

def get_file_path(filename: str) -> Path:
    """Get full path for uploaded file."""
    return UPLOADS_DIR / filename
