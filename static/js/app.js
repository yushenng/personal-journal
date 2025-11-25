let editingEntryId = null;
let deletingEntryId = null;

// Load entries when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadEntries();
    setupEventListeners();
});

function setupEventListeners() {
    const form = document.getElementById('entry-form');
    const cancelBtn = document.getElementById('cancel-btn');
    const deleteModal = document.getElementById('delete-modal');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const deleteConfirmInput = document.getElementById('delete-confirm-input');

    form.addEventListener('submit', handleFormSubmit);
    cancelBtn.addEventListener('click', cancelEdit);

    // Delete modal handlers
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    confirmDeleteBtn.addEventListener('click', confirmDelete);
    
    // Enable/disable delete button based on input
    deleteConfirmInput.addEventListener('input', (e) => {
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        if (e.target.value.trim() === 'DELETE') {
            confirmDeleteBtn.disabled = false;
        } else {
            confirmDeleteBtn.disabled = true;
        }
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === deleteModal) {
            closeDeleteModal();
        }
    });
}

async function loadEntries() {
    try {
        const response = await fetch('/api/entries');
        const data = await response.json();

        if (data.success) {
            displayEntries(data.entries);
        } else {
            showError('Failed to load entries: ' + data.error);
        }
    } catch (error) {
        showError('Error loading entries: ' + error.message);
    }
}

function displayEntries(entries) {
    const entriesList = document.getElementById('entries-list');

    if (entries.length === 0) {
        entriesList.innerHTML = '<p class="empty-state">No entries yet. Start writing your first journal entry!</p>';
        return;
    }

    entriesList.innerHTML = entries.map(entry => `
        <div class="entry-card" data-id="${entry.id}">
            <div class="entry-header">
                <div class="entry-title">${escapeHtml(entry.title)}</div>
                <div class="entry-date">${formatDate(entry.created_at)}${entry.updated_at !== entry.created_at ? ' (edited)' : ''}</div>
            </div>
            <div class="entry-content">${escapeHtml(entry.content)}</div>
            <div class="entry-actions">
                <button class="btn-edit" onclick="editEntry(${entry.id})">Edit</button>
                <button class="btn-delete" onclick="showDeleteModal(${entry.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const title = document.getElementById('entry-title').value.trim();
    const content = document.getElementById('entry-content').value.trim();

    if (!title || !content) {
        alert('Please fill in both title and content.');
        return;
    }

    try {
        let response;
        if (editingEntryId) {
            // Update existing entry
            response = await fetch(`/api/entries/${editingEntryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, content }),
            });
        } else {
            // Create new entry
            response = await fetch('/api/entries', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, content }),
            });
        }

        const data = await response.json();

        if (data.success) {
            // Reset form
            document.getElementById('entry-form').reset();
            editingEntryId = null;
            document.getElementById('form-title').textContent = 'New Entry';
            document.getElementById('cancel-btn').style.display = 'none';
            
            // Reload entries
            loadEntries();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error saving entry: ' + error.message);
    }
}

async function editEntry(entryId) {
    try {
        const response = await fetch('/api/entries');
        const data = await response.json();

        if (data.success) {
            const entry = data.entries.find(e => e.id === entryId);
            if (entry) {
                // Populate form with entry data
                document.getElementById('entry-title').value = entry.title;
                document.getElementById('entry-content').value = entry.content;
                editingEntryId = entryId;
                document.getElementById('form-title').textContent = 'Edit Entry';
                document.getElementById('cancel-btn').style.display = 'inline-block';
                
                // Scroll to form
                document.querySelector('.entry-form-container').scrollIntoView({ behavior: 'smooth' });
            }
        }
    } catch (error) {
        alert('Error loading entry: ' + error.message);
    }
}

function cancelEdit() {
    document.getElementById('entry-form').reset();
    editingEntryId = null;
    document.getElementById('form-title').textContent = 'New Entry';
    document.getElementById('cancel-btn').style.display = 'none';
}

function showDeleteModal(entryId) {
    deletingEntryId = entryId;
    const modal = document.getElementById('delete-modal');
    const input = document.getElementById('delete-confirm-input');
    const confirmBtn = document.getElementById('confirm-delete-btn');
    
    input.value = '';
    confirmBtn.disabled = true;
    modal.style.display = 'block';
    input.focus();
}

function closeDeleteModal() {
    const modal = document.getElementById('delete-modal');
    modal.style.display = 'none';
    deletingEntryId = null;
    document.getElementById('delete-confirm-input').value = '';
}

async function confirmDelete() {
    if (!deletingEntryId) return;

    try {
        const response = await fetch(`/api/entries/${deletingEntryId}`, {
            method: 'DELETE',
        });

        const data = await response.json();

        if (data.success) {
            closeDeleteModal();
            loadEntries();
        } else {
            alert('Error deleting entry: ' + data.error);
        }
    } catch (error) {
        alert('Error deleting entry: ' + error.message);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const entriesList = document.getElementById('entries-list');
    entriesList.innerHTML = `<p class="loading" style="color: #ff6b6b;">${escapeHtml(message)}</p>`;
}
