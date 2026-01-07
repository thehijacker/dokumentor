// Main application logic
let currentPage = 1;
let currentDocumentId = null;
let categories = [];
let cameraStream = null;
let currentSort = { by: 'filename', order: 'desc' };

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Add global modal focus management to avoid aria-hidden focus blocking
    document.addEventListener('show.bs.modal', (e) => {
        try {
            // Save the element that had focus before modal is shown
            e.target._lastFocusEl = document.activeElement;
        } catch (ex) {
            console.warn('Failed to store last focus before showing modal', ex);
        }
    });

    document.addEventListener('hide.bs.modal', (e) => {
        try {
            // If an element inside the modal retains focus, blur it before aria-hidden is applied
            const active = document.activeElement;
            if (e.target && e.target.contains(active)) {
                active.blur && active.blur();
            }
        } catch (ex) {
            console.warn('Failed to blur active element during modal hide', ex);
        }
    });

    document.addEventListener('hidden.bs.modal', (e) => {
        try {
            // Restore focus to the previously focused element
            const last = e.target && e.target._lastFocusEl;
            if (last && typeof last.focus === 'function') {
                last.focus();
            }
            // Cleanup the modal DOM if it was dynamically inserted
            if (e.target && e.target.classList && e.target.classList.contains('draggable-modal')) {
                // Remove from DOM after hidden
                e.target.remove();
            }
        } catch (ex) {
            console.warn('Failed to restore focus after modal hidden', ex);
        }
    });

    translateUI();
    loadStats();
    loadCategories();
    loadRecentDocuments();
    setupUploadArea();
    setupUploadCategorySelection();
    setupSortableColumns();
    setupCategoryFormHandlers();
    
    // Restore last active tab
    const lastTab = localStorage.getItem('activeTab') || 'dashboard';
    showSection(lastTab);
    
    // Start polling for new documents
    startDocumentPolling();
});

// Setup category form handlers to prevent Enter from closing modal
function setupCategoryFormHandlers() {
    const categoryForm = document.getElementById('category-form');
    const subcategoryForm = document.getElementById('subcategory-form');
    
    if (categoryForm) {
        categoryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            saveCategory();
        });
    }
    
    if (subcategoryForm) {
        subcategoryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            saveSubcategory();
        });
    }
}

// Store active tab
function storeActiveTab(section) {
    localStorage.setItem('activeTab', section);
}

// Setup upload category selection
function setupUploadCategorySelection() {
    const checkbox = document.getElementById('auto-categorize-checkbox');
    const selectionArea = document.getElementById('category-selection-area');
    const aiModelSelection = document.getElementById('ai-model-selection');
    const categorySelect = document.getElementById('upload-category-select');
    const subcategorySelect = document.getElementById('upload-subcategory-select');
    
    // Toggle selection area and AI model selection
    checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
            selectionArea.style.display = 'block';
            aiModelSelection.style.display = 'block';
            loadUploadCategories();
        } else {
            selectionArea.style.display = 'none';
            aiModelSelection.style.display = 'none';
        }
    });
    
    // Update subcategories when category changes
    categorySelect.addEventListener('change', () => {
        const categoryId = parseInt(categorySelect.value);
        if (categoryId) {
            const category = categories.find(c => c.id === categoryId);
            if (category && category.subcategories) {
                subcategorySelect.innerHTML = '<option value="">' + t('select_subcategory') + '</option>' + 
                    category.subcategories.map(sub => 
                        `<option value="${sub.id}">${sub.name}</option>`
                    ).join('');
            }
        } else {
            subcategorySelect.innerHTML = '<option value="">' + t('select_subcategory') + '</option>';
        }
    });
}

// Load categories for upload selection
function loadUploadCategories() {
    const categorySelect = document.getElementById('upload-category-select');
    categorySelect.innerHTML = '<option value="">' + t('select_category_first') + '</option>' +
        categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
}

// Setup sortable columns
function setupSortableColumns() {
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const sortBy = header.getAttribute('data-sort');
            
            // Toggle sort order if clicking the same column
            if (currentSort.by === sortBy) {
                currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.by = sortBy;
                currentSort.order = 'asc';
            }
            
            // Update visual indicators
            updateSortIcons();
            
            // Reload documents with new sort
            loadDocuments(currentPage);
        });
    });
}

function updateSortIcons() {
    // Reset all sort icons
    document.querySelectorAll('.sortable').forEach(header => {
        header.classList.remove('sort-active');
        let icon = header.querySelector('.sort-icon');
        
        // Create icon if it doesn't exist
        if (!icon) {
            const span = header.querySelector('span');
            if (span) {
                icon = document.createElement('i');
                icon.className = 'bi sort-icon';
                header.appendChild(icon);
            }
        }
        
        if (icon) {
            icon.className = 'bi sort-icon';
        }
    });
    
    // Set active sort icon
    const activeHeader = document.querySelector(`.sortable[data-sort="${currentSort.by}"]`);
    if (activeHeader) {
        activeHeader.classList.add('sort-active');
        let icon = activeHeader.querySelector('.sort-icon');
        
        // Create icon if it doesn't exist
        if (!icon) {
            icon = document.createElement('i');
            activeHeader.appendChild(icon);
        }
        
        if (icon) {
            icon.className = currentSort.order === 'asc' ? 'bi bi-chevron-up sort-icon' : 'bi bi-chevron-down sort-icon';
        }
    }
}

// Translate UI
function translateUI() {
    const brandTextEl = document.querySelector('#app-name .brand-text');
    if (brandTextEl) brandTextEl.textContent = t('app_name');
    const versionEl = document.querySelector('#app-name .app-version');
    if (versionEl) versionEl.textContent = 'v' + (window.APP_VERSION || versionEl.textContent.replace(/^v/, ''));
    document.getElementById('nav-dashboard').textContent = t('dashboard');
    document.getElementById('nav-documents').textContent = t('documents');
    document.getElementById('nav-upload').textContent = t('upload');
    document.getElementById('nav-categories').textContent = t('categories');
    document.getElementById('nav-settings').textContent = t('settings');
    document.getElementById('logout-btn').textContent = t('logout');
    document.getElementById('dashboard-title').textContent = t('dashboard');
    document.getElementById('documents-title').textContent = t('my_documents');
    document.getElementById('upload-title').textContent = t('upload_document');
    document.getElementById('categories-title').textContent = t('manage_categories');
    const settingsTitle = document.getElementById('settings-title');
    if (settingsTitle) settingsTitle.textContent = t('settings');
    const pdfPasswordsTitle = document.getElementById('pdf-passwords-title');
    if (pdfPasswordsTitle) pdfPasswordsTitle.textContent = t('pdf_passwords');
    const pdfPasswordsDesc = document.getElementById('pdf-passwords-desc');
    if (pdfPasswordsDesc) pdfPasswordsDesc.textContent = t('pdf_passwords_desc');
    const addPasswordText = document.getElementById('add-password-text');
    if (addPasswordText) addPasswordText.textContent = t('add_password');
    const savePasswordsText = document.getElementById('save-passwords-text');
    if (savePasswordsText) savePasswordsText.textContent = t('save_passwords');
    const userInfoTitle = document.getElementById('user-info-title');
    if (userInfoTitle) userInfoTitle.textContent = t('user_info');
    const usernameLabel = document.getElementById('username-label');
    if (usernameLabel) usernameLabel.textContent = t('username') + ':';
    const emailLabel = document.getElementById('email-label');
    if (emailLabel) emailLabel.textContent = t('email') + ':';
    const memberSinceLabel = document.getElementById('member-since-label');
    if (memberSinceLabel) memberSinceLabel.textContent = t('member_since') + ':';
    document.getElementById('stat-total').textContent = t('total_documents');
    document.getElementById('stat-processed').textContent = t('processed_documents');
    document.getElementById('stat-categories').textContent = t('categories');
    document.getElementById('recent-docs-title').textContent = t('documents');
    document.getElementById('search-input').placeholder = t('search');
    document.getElementById('search-btn').textContent = t('search');
    document.getElementById('select-file-text').textContent = t('select_file');
    document.getElementById('or-drag-text').textContent = t('or_drag_drop');
    document.getElementById('supported-formats').textContent = t('supported_formats');
    document.getElementById('take-photo-text').textContent = t('take_photo');
    document.getElementById('modal-title').textContent = t('document_details');
    document.getElementById('modal-close').textContent = t('cancel');
    document.getElementById('modal-save').textContent = t('save');
    
    // Upload category selection
    const autoCategorizeLabel = document.getElementById('auto-categorize-label');
    if (autoCategorizeLabel) autoCategorizeLabel.textContent = t('auto_categorize');
    const uploadCategoryLabel = document.getElementById('upload-category-label');
    if (uploadCategoryLabel) uploadCategoryLabel.textContent = t('category');
    const uploadSubcategoryLabel = document.getElementById('upload-subcategory-label');
    if (uploadSubcategoryLabel) uploadSubcategoryLabel.textContent = t('subcategory');

    // Ensure subcategory placeholder is translated initially
    const uploadSubcategorySelect = document.getElementById('upload-subcategory-select');
    if (uploadSubcategorySelect && (!uploadSubcategorySelect.options || uploadSubcategorySelect.options.length === 0)) {
        uploadSubcategorySelect.innerHTML = '<option value="">' + t('select_subcategory') + '</option>';
    } else if (uploadSubcategorySelect) {
        // If a placeholder exists as the first option, update its text
        const firstOpt = uploadSubcategorySelect.querySelector('option[value=""]');
        if (firstOpt) firstOpt.textContent = t('select_subcategory');
    }

    // AI model selection (upload)
    const aiModelLabel = document.getElementById('ai-model-label');
    if (aiModelLabel) aiModelLabel.textContent = t('ai_model');
    const aiModelHelp = document.getElementById('ai-model-help');
    if (aiModelHelp) aiModelHelp.textContent = t('ai_model_help');
    const aiModelSelect = document.getElementById('ai-model-select');
    if (aiModelSelect) {
        aiModelSelect.innerHTML = `
            <option value="">${t('default')}</option>
            <option value="internal">${t('ai_model_internal') || t('internal')}</option>
            <option value="ollama">${t('ai_model_ollama') || t('ollama')}</option>
            <option value="openai">${t('ai_model_openai') || t('openai')}</option>
        `;
    }
    
    // Table headers
    document.getElementById('th-filename').textContent = t('file_name');
    document.getElementById('th-category').textContent = t('category');
    document.getElementById('th-uploaded').textContent = t('uploaded');
    document.getElementById('th-actions').textContent = t('actions');
    
    // Table headers with sort icons - only update the span text
    const updateHeaderText = (id, text) => {
        const header = document.getElementById(id);
        if (header) {
            const span = header.querySelector('span');
            if (span) {
                span.textContent = text;
            } else {
                header.textContent = text;
            }
        }
    };
    
    updateHeaderText('th-filename-list', t('file_name'));
    updateHeaderText('th-category-list', t('category'));
    updateHeaderText('th-subcategory-list', t('subcategory'));
    updateHeaderText('th-bill-value-list', t('bill_value'));
    updateHeaderText('th-uploaded-list', t('uploaded'));
    updateHeaderText('th-confidence-list', t('confidence'));
    
    // Non-sortable headers
    document.getElementById('th-notes-list').textContent = t('has_notes');
    document.getElementById('th-actions-list').textContent = t('actions');
    
    // Category modal
    document.getElementById('add-cat-btn').textContent = t('add_category');
    document.getElementById('cat-name-label').textContent = t('category_name');
    document.getElementById('cat-desc-label').textContent = t('category_description');
    document.getElementById('cat-cancel-btn').textContent = t('cancel');
    document.getElementById('cat-save-btn').textContent = t('save');
    document.getElementById('parent-cat-label').textContent = t('parent_category');
    document.getElementById('subcat-name-label').textContent = t('subcategory_name');
    document.getElementById('subcat-cancel-btn').textContent = t('cancel');
    document.getElementById('subcat-save-btn').textContent = t('save');
    
    // Category management section
    document.getElementById('categories-subcategories-header').textContent = t('categories_and_subcategories');
    document.getElementById('category-info-header').textContent = t('information');
    document.getElementById('category-info-text').textContent = t('category_info_text');
    document.getElementById('category-tips-header').textContent = t('tips');
    document.getElementById('category-tip-1').textContent = t('category_tip_1');
    document.getElementById('category-tip-2').textContent = t('category_tip_2');
    document.getElementById('category-tip-3').textContent = t('category_tip_3');
    
    // Get user info
    API.get('/api/auth/me')
        .then(user => {
            document.getElementById('user-welcome').textContent = `${t('welcome')}, ${user.username}`;
        })
        .catch(err => {
            window.location.href = '/login';
        });
}

// Show section
function showSection(section) {
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('documents-section').style.display = 'none';
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('categories-section').style.display = 'none';
    document.getElementById('settings-section').style.display = 'none';
    
    // Update active nav links
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => link.classList.remove('active'));
    
    if (section === 'documents') {
        document.getElementById('documents-section').style.display = 'block';
        document.getElementById('nav-documents').classList.add('active');
        updateSortIcons();
        loadDocuments();
    } else if (section === 'upload') {
        document.getElementById('upload-section').style.display = 'block';
        document.getElementById('nav-upload').classList.add('active');
    } else if (section === 'categories') {
        document.getElementById('categories-section').style.display = 'block';
        document.getElementById('nav-categories').classList.add('active');
        loadCategoriesManagement();
    } else if (section === 'settings') {
        document.getElementById('settings-section').style.display = 'block';
        document.getElementById('nav-settings').classList.add('active');
        loadPasswords();
        loadUserInfo();
    } else {
        section = 'dashboard';
        document.getElementById('dashboard-section').style.display = 'block';
        document.getElementById('nav-dashboard').classList.add('active');
    }
    
    storeActiveTab(section);
}

// Load stats
async function loadStats() {
    try {
        const stats = await API.get('/api/stats');
        document.getElementById('total-docs').textContent = stats.total_documents;
        document.getElementById('processed-docs').textContent = stats.processed_documents;
        document.getElementById('total-categories').textContent = Object.keys(stats.by_category).length;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load categories
async function loadCategories() {
    try {
        categories = await API.get('/api/categories');
        
        // Populate category filter dropdown
        const categoryFilter = document.getElementById('category-filter');
        categoryFilter.innerHTML = `<option value="">${t('all_categories')}</option>`;
        
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            categoryFilter.appendChild(option);
        });
        
        // Populate subcategory filter (initially empty)
        const subcategoryFilter = document.getElementById('subcategory-filter');
        subcategoryFilter.innerHTML = `<option value="">${t('all_subcategories')}</option>`;
        
        // Add change event to update subcategories
        categoryFilter.addEventListener('change', updateSubcategoryFilter);
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Update subcategory filter based on selected category
function updateSubcategoryFilter() {
    const categoryId = document.getElementById('category-filter').value;
    const subcategoryFilter = document.getElementById('subcategory-filter');
    
    subcategoryFilter.innerHTML = `<option value="">${t('all_subcategories')}</option>`;
    
    if (categoryId) {
        const category = categories.find(c => c.id === parseInt(categoryId));
        if (category && category.subcategories) {
            category.subcategories.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.id;
                option.textContent = sub.name;
                subcategoryFilter.appendChild(option);
            });
        }
    }
}

// Load recent documents
async function loadRecentDocuments() {
    try {
        const data = await API.get('/api/documents?per_page=5');
        const tbody = document.getElementById('recent-docs-body');
        
        if (data.documents.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">${t('no_documents')}</td></tr>`;
            return;
        }
        
        tbody.innerHTML = data.documents.map(doc => `
            <tr class="document-item" onclick="viewDocument(${doc.id})">
                <td>
                    <i class="bi bi-file-earmark-${doc.file_type === 'pdf' ? 'pdf' : (doc.file_type === 'docx' ? 'word' : 'image')}"></i>
                    ${doc.original_filename}
                </td>
                <td>${doc.category ? doc.category.name : '-'}</td>
                <td>${formatDate(doc.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); viewDocument(${doc.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load recent documents:', error);
    }
}

// Load documents with filters
async function loadDocuments(page = 1) {
    try {
        const search = document.getElementById('search-input').value;
        const categoryId = document.getElementById('category-filter').value;
        const subcategoryId = document.getElementById('subcategory-filter').value;
        
        let url = `/api/documents?page=${page}&per_page=20`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (categoryId) url += `&category_id=${categoryId}`;
        if (subcategoryId) url += `&subcategory_id=${subcategoryId}`;
        url += `&sort_by=${currentSort.by}&sort_order=${currentSort.order}`;
        
        const data = await API.get(url);
        const tbody = document.getElementById('documents-body');
        
        if (data.documents.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center">${t('no_documents')}</td></tr>`;
            document.getElementById('pagination').innerHTML = '';
            return;
        }
        
        tbody.innerHTML = data.documents.map(doc => {
            const confidence = doc.ai_confidence || 0;
            const confidenceClass = confidence > 0.7 ? 'confidence-high' : confidence > 0.4 ? 'confidence-medium' : 'confidence-low';
            const billValueDisplay = doc.bill_value ? `${doc.bill_value.toFixed(2)} €` : t('no_bill_value');
            const notesIcon = doc.notes ? `<i class="bi bi-sticky-fill text-warning" title="${doc.notes}" data-bs-toggle="tooltip"></i>` : '-';
            
            return `
                <tr class="document-item" onclick="viewDocument(${doc.id})">
                    <td>
                        <!-- Desktop view -->
                        <div class="d-none d-lg-block filename-cell">
                            <i class="bi bi-file-earmark-${doc.file_type === 'pdf' ? 'pdf' : (doc.file_type === 'docx' ? 'word' : 'image')}"></i>
                            <span title="${doc.original_filename}">${doc.original_filename}</span>
                        </div>
                        <!-- Mobile card view -->
                        <div class="d-lg-none mobile-card">
                            <div class="d-flex align-items-center mb-1">
                                <i class="bi bi-file-earmark-${doc.file_type === 'pdf' ? 'pdf' : (doc.file_type === 'docx' ? 'word' : 'image')} me-2"></i>
                                <strong class="flex-grow-1" style="font-size: 0.9rem;">${doc.original_filename}</strong>
                            </div>
                            <div class="mobile-card-details">
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">${t('category')}:</span>
                                    <span>${doc.category ? doc.category.name : '-'}</span>
                                </div>
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">${t('subcategory')}:</span>
                                    <span>${doc.subcategory ? doc.subcategory.name : '-'}</span>
                                </div>
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">${t('bill_value')}:</span>
                                    <span><strong>${billValueDisplay}</strong></span>
                                </div>
                                ${doc.notes ? `<div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">${t('notes')}:</span>
                                    <span class="text-truncate" style="max-width: 150px;" title="${doc.notes}">${doc.notes}</span>
                                </div>` : ''}
                                <div class="d-flex justify-content-between mb-1">
                                    <span class="text-muted">${t('uploaded')}:</span>
                                    <span>${formatDate(doc.created_at)}</span>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <span class="text-muted">${t('confidence')}:</span>
                                    <span class="badge ${confidenceClass}">${Math.round(confidence * 100)}%</span>
                                </div>
                            </div>
                        </div>
                    </td>
                    <td class="d-none d-lg-table-cell">${doc.category ? doc.category.name : '-'}</td>
                    <td class="d-none d-lg-table-cell">${doc.subcategory ? doc.subcategory.name : '-'}</td>
                    <td class="d-none d-lg-table-cell">${billValueDisplay}</td>
                    <td class="d-none d-lg-table-cell text-center">${notesIcon}</td>
                    <td class="d-none d-lg-table-cell">${formatDate(doc.created_at)}</td>
                    <td class="d-none d-lg-table-cell">
                        <span class="badge ${confidenceClass}">
                            ${Math.round(confidence * 100)}%
                        </span>
                    </td>
                    <td>
                        <div class="d-none d-lg-flex gap-1">
                            <button class="btn btn-sm btn-info" onclick="event.stopPropagation(); previewDocumentInline(${doc.id}, '${doc.file_type}')" title="${t('preview')}">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); viewDocument(${doc.id})" title="${t('view')}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-success" onclick="event.stopPropagation(); downloadDocument(${doc.id})" title="${t('download')}">
                                <i class="bi bi-download"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteDocument(${doc.id})" title="${t('delete')}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                        <div class="d-lg-none mobile-action-grid mt-2">
                            <button class="btn btn-sm btn-info" onclick="event.stopPropagation(); previewDocumentInline(${doc.id}, '${doc.file_type}')">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); viewDocument(${doc.id})">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-success" onclick="event.stopPropagation(); downloadDocument(${doc.id})">
                                <i class="bi bi-download"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteDocument(${doc.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Update pagination
        updatePagination(data.page, data.pages);
        currentPage = page;
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

// Update pagination
function updatePagination(currentPage, totalPages) {
    const pagination = document.getElementById('pagination');
    let html = '';
    
    // Previous
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadDocuments(${currentPage - 1}); return false;">
                Previous
            </a>
        </li>
    `;
    
    // Pages
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="loadDocuments(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Next
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadDocuments(${currentPage + 1}); return false;">
                Next
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

// Setup upload area
function setupUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadMultipleFiles(Array.from(e.target.files));
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            uploadMultipleFiles(Array.from(e.dataTransfer.files));
        }
    });
    
    // Add Enter key support for search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadDocuments();
            }
        });
    }
}

// Upload multiple files
async function uploadMultipleFiles(files) {
    // Get auto-categorize settings
    const checkbox = document.getElementById('auto-categorize-checkbox');
    const autoCategorize = checkbox && checkbox.checked;
    let categoryId = null;
    let subcategoryId = null;
    
    if (autoCategorize) {
        const categorySelect = document.getElementById('upload-category-select');
        const subcategorySelect = document.getElementById('upload-subcategory-select');
        categoryId = categorySelect.value ? parseInt(categorySelect.value) : null;
        subcategoryId = subcategorySelect.value ? parseInt(subcategorySelect.value) : null;
        
        if (!categoryId) {
            showToast(t('select_category_first'), 'error');
            return;
        }
    }
    
    if (files.length === 1) {
        // Single file - show modal after upload
        uploadingInProgress = true;
        await uploadFile(files[0], true, categoryId, subcategoryId);
        uploadingInProgress = false;
    } else {
        // Multiple files - process in background
        uploadingInProgress = true;
        let completed = 0;
        const total = files.length;
        
        const toastId = showProgressToast(`${t('uploading')} ${completed}/${total}...`);
        
        for (const file of files) {
            try {
                await uploadFile(file, false, categoryId, subcategoryId);
                completed++;
                updateProgressToast(toastId, `${t('uploading')} ${completed}/${total}...`);
            } catch (error) {
                console.error('Upload failed:', error);
            }
        }
        
        removeProgressToast(toastId);
        showToast(`${completed} ${t('files_uploaded')}`, 'success');
        
        // Update document count immediately to prevent false notifications
        const response = await API.get('/api/documents?limit=1');
        lastDocumentCount = response.total || 0;
        
        uploadingInProgress = false;
        
        loadStats();
        loadRecentDocuments();
        if (document.getElementById('documents-section').style.display === 'block') {
            loadDocuments();
        }
    }
}

// Upload file
async function uploadFile(file, showModal = true, categoryId = null, subcategoryId = null) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Get selected AI model if auto-categorize is enabled
    const autoCategorize = document.getElementById('auto-categorize-checkbox').checked;
    if (autoCategorize) {
        const aiModel = document.getElementById('ai-model-select').value;
        if (aiModel) {
            formData.append('ai_model', aiModel);
        }
    }
    
    try {
        const response = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const result = await response.json();
        const documentId = result.document_id;
        
        // Apply category if provided
        if (categoryId) {
            try {
                await API.put(`/api/documents/${documentId}/update`, {
                    category_id: categoryId,
                    subcategory_id: subcategoryId
                });
            } catch (error) {
                console.error('Failed to set category:', error);
            }
        }
        
        // Reset file input
        document.getElementById('file-input').value = '';
        
        if (showModal) {
            // Single file - show modal
            const uploadProgress = document.getElementById('upload-progress');
            const uploadStatus = document.getElementById('upload-status');
            uploadProgress.style.display = 'block';
            uploadStatus.textContent = t('processing');
            
            setTimeout(() => {
                uploadProgress.style.display = 'none';
                showToast(t('upload_success'), 'success');
                loadStats();
                loadRecentDocuments();
                viewDocument(documentId);
            }, 1000);
        }
        
        return result;
    } catch (error) {
        if (showModal) {
            const uploadProgress = document.getElementById('upload-progress');
            uploadProgress.style.display = 'none';
        }
        
        // Check if it's a duplicate error (409 status)
        if (error.message && error.message.includes('Duplicate')) {
            showToast(t('duplicate_file'), 'error');
        } else {
            showToast(t('upload_error') + ': ' + error.message, 'error');
        }
        throw error;
    }
}

// Progress toast management
let progressToasts = {};
let toastIdCounter = 0;

function showProgressToast(message) {
    const id = `progress-toast-${toastIdCounter++}`;
    const toastHtml = `
        <div class="toast align-items-center text-white bg-info border-0" role="alert" id="${id}" data-bs-autohide="false">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('toast-container');
    if (container) {
        container.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(id);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        progressToasts[id] = { element: toastElement, toast: toast };
    }
    return id;
}

function updateProgressToast(id, message) {
    if (progressToasts[id]) {
        const body = progressToasts[id].element.querySelector('.toast-body');
        if (body) body.textContent = message;
    }
}

function removeProgressToast(id) {
    if (progressToasts[id]) {
        progressToasts[id].toast.hide();
        setTimeout(() => {
            progressToasts[id].element.remove();
            delete progressToasts[id];
        }, 500);
    }
}

// Poll for new documents from watch folder
let lastDocumentCount = 0;
let pollingInterval = null;
let uploadingInProgress = false;

function startDocumentPolling() {
    // Get initial count
    API.get('/api/documents?limit=1').then(response => {
        lastDocumentCount = response.total || 0;
    }).catch(err => console.error('Initial count failed:', err));
    
    // Poll every 5 seconds
    pollingInterval = setInterval(async () => {
        try {
            const response = await API.get('/api/documents?limit=1');
            const currentCount = response.total || 0;
            
            // Only show notification if not currently uploading and count increased
            if (lastDocumentCount > 0 && currentCount > lastDocumentCount && !uploadingInProgress) {
                // New documents added from watch folder
                const diff = currentCount - lastDocumentCount;
                showToast(`${diff} ${t('new_documents_processed')}`, 'info');
                
                // Reload document lists
                if (document.getElementById('documents-section').style.display === 'block') {
                    loadDocuments();
                } else {
                    loadRecentDocuments();
                }
                loadStats();
            }
            
            lastDocumentCount = currentCount;
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 5000);
}

// Camera functions
async function captureFromCamera() {
    const cameraContainer = document.getElementById('camera-container');
    const video = document.getElementById('camera-preview');
    
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' },
            audio: false 
        });
        
        video.srcObject = cameraStream;
        cameraContainer.style.display = 'block';
    } catch (error) {
        showToast(t('camera_access_denied') + ': ' + error.message, 'error');
    }
}

function capturePhoto() {
    const video = document.getElementById('camera-preview');
    const canvas = document.getElementById('capture-canvas');
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    canvas.toBlob((blob) => {
        const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' });
        stopCamera();
        uploadFile(file);
    }, 'image/jpeg', 0.95);
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    document.getElementById('camera-container').style.display = 'none';
}

// View document
async function viewDocument(id) {
    try {
        const doc = await API.get(`/api/documents/${id}`);
        currentDocumentId = id;
        
        const modalBody = document.getElementById('modal-body');
        
        // Determine which category to use for subcategories
        let selectedCategoryId = doc.category ? doc.category.id : (categories.length > 0 ? categories[0].id : null);
        
        // Build subcategories dropdown
        let subcategoriesOptions = '<option value="">-</option>';
        if (selectedCategoryId) {
            const cat = categories.find(c => c.id === selectedCategoryId);
            if (cat && cat.subcategories && cat.subcategories.length > 0) {
                subcategoriesOptions += cat.subcategories.map(sub => 
                    `<option value="${sub.id}" ${doc.subcategory && doc.subcategory.id === sub.id ? 'selected' : ''}>${sub.name}</option>`
                ).join('');
            }
        }
        
        // Parse extracted data if available
        let extractedAmount = '';
        if (doc.extracted_data) {
            try {
                const data = typeof doc.extracted_data === 'string' ? JSON.parse(doc.extracted_data) : doc.extracted_data;
                if (data.amounts && data.amounts.length > 0) {
                    extractedAmount = data.amounts.join(', ');
                }
            } catch (e) {
                console.error('Error parsing extracted_data:', e);
            }
        }
        
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label class="form-label">${t('original_name')}</label>
                    <input type="text" class="form-control" id="edit-filename" value="${doc.original_filename}">
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">${t('file_type')}</label>
                    <input type="text" class="form-control" value="${doc.file_type.toUpperCase()}" disabled>
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">${t('file_size')}</label>
                    <input type="text" class="form-control" value="${formatFileSize(doc.file_size)}" disabled>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4 mb-2">
                    <label class="form-label">${t('category')}</label>
                    <select class="form-select" id="edit-category">
                        ${categories.map(cat => 
                            `<option value="${cat.id}" ${selectedCategoryId === cat.id ? 'selected' : ''}>${cat.name}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="col-md-4 mb-2">
                    <label class="form-label">${t('subcategory')}</label>
                    <select class="form-select" id="edit-subcategory">
                        ${subcategoriesOptions}
                    </select>
                </div>
                <div class="col-md-2 mb-2">
                    <label class="form-label">${t('confidence')}</label>
                    <input type="text" class="form-control" value="${doc.ai_confidence ? Math.round(doc.ai_confidence * 100) + '%' : '0%'}" disabled>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6 mb-2">
                    <label class="form-label">${t('amounts')} <small class="text-muted">(${t('extracted_data')})</small></label>
                    <div class="input-group">
                        <input type="text" class="form-control" value="${extractedAmount || '-'}" disabled>
                        <span class="input-group-text">€</span>
                    </div>
                </div>
                <div class="col-md-6 mb-2">
                    <label class="form-label">${t('bill_value')}</label>
                    <div class="input-group">
                        <input type="number" class="form-control" id="edit-bill-value" step="0.01" value="${doc.bill_value || ''}" placeholder="0.00">
                        <span class="input-group-text">€</span>
                    </div>
                </div>
            </div>
            
            <div class="mb-2">
                <label class="form-label">${t('notes')}</label>
                <textarea class="form-control" id="edit-notes" rows="2">${doc.notes || ''}</textarea>
            </div>
            
            <div class="mb-2">
                <label class="form-label">${t('ocr_text')}</label>
                <div class="ocr-text" style="max-height: 200px;">${doc.ocr_text || 'N/A'}</div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">${t('ai_model_reprocess')}</label>
                <select class="form-select" id="reprocess-ai-model">
                    <option value="">${t('default')}</option>
                    <option value="internal">${t('internal')}</option>
                    <option value="ollama">${t('ollama')}</option>
                    <option value="openai">${t('openai')}</option>
                </select>
                <div class="form-text">${t('ai_model_reprocess_help')}</div>
            </div>
            
            <div class="d-flex gap-2 mt-3">
                <button class="btn btn-warning" onclick="reprocessDocument(${id})">
                    <i class="bi bi-arrow-clockwise"></i> ${t('reprocess')}
                </button>
                <button class="btn btn-info" onclick="previewDocumentInline(${id}, '${doc.file_type}')">
                    <i class="bi bi-eye"></i> ${t('preview')}
                </button>
                <button class="btn btn-success" onclick="downloadDocument(${id}, '${doc.original_filename}')">
                    <i class="bi bi-download"></i> ${t('download')}
                </button>
                <button class="btn btn-danger ms-auto" onclick="deleteDocument(${id}); bootstrap.Modal.getInstance(document.getElementById('documentModal')).hide();">
                    <i class="bi bi-trash"></i> ${t('delete')}
                </button>
            </div>
        `;
        
        // Add change listener to category dropdown to update subcategories
        document.getElementById('edit-category').addEventListener('change', function() {
            const categoryId = parseInt(this.value);
            const cat = categories.find(c => c.id === categoryId);
            const subcategorySelect = document.getElementById('edit-subcategory');
            
            subcategorySelect.innerHTML = '<option value="">-</option>';
            if (cat && cat.subcategories) {
                subcategorySelect.innerHTML += cat.subcategories.map(sub => 
                    `<option value="${sub.id}">${sub.name}</option>`
                ).join('');
            }
        });
        
        // Show modal
        new bootstrap.Modal(document.getElementById('documentModal')).show();
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Save document changes
async function saveDocumentChanges() {
    const categoryId = parseInt(document.getElementById('edit-category').value);
    const subcategoryId = document.getElementById('edit-subcategory').value;
    const notes = document.getElementById('edit-notes').value;
    const filename = document.getElementById('edit-filename').value.trim();
    const billValue = parseFloat(document.getElementById('edit-bill-value').value) || null;
    
    if (!filename) {
        alert('Filename cannot be empty');
        return;
    }
    
    try {
        await API.put(`/api/documents/${currentDocumentId}/update`, {
            category_id: categoryId,
            subcategory_id: subcategoryId || null,
            notes: notes,
            original_filename: filename,
            bill_value: billValue
        });
        
        showToast(t('save_success'), 'success');
        bootstrap.Modal.getInstance(document.getElementById('documentModal')).hide();
        
        // Reload documents
        loadDocuments(currentPage);
        loadRecentDocuments();
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Preview document inline in same page
function previewDocumentInline(id, fileType) {
    // Create preview modal (draggable & resizable)
    let bodyContent = '';
    if (fileType === 'pdf') {
        bodyContent = '<iframe src="/api/documents/' + id + '/preview#view=FitH&toolbar=1&navpanes=0" style="width: 100%; height: 100%; border: none;"></iframe>';
    } else if (fileType === 'docx') {
        bodyContent = '<div style="width: 100%; height: 100%; overflow: auto; display: flex; align-items: center; justify-content: center; background: #f8f9fa;"><div class="text-center"><p class="mb-3">' + t('docx_preview_unavailable') + '</p><a class="btn btn-primary me-2" href="/api/documents/' + id + '/preview" target="_blank">' + t('open_in_new_tab') + '</a><a class="btn btn-secondary" href="/api/documents/' + id + '/download">' + t('download') + '</a></div></div>';
    } else {
        bodyContent = '<div style="width: 100%; height: 100%; overflow: auto; display: flex; align-items: center; justify-content: center; background: #333;"><img id="preview-image" src="/api/documents/' + id + '/preview" style="max-width: 100%; max-height: 100%; object-fit: contain; cursor: zoom-in;" onclick="this.style.transform = this.style.transform === \"scale(2)\" ? \"scale(1)\" : \"scale(2)\"; this.style.cursor = this.style.transform === \"scale(2)\" ? \"zoom-out\" : \"zoom-in\";" /></div>';
    }

    const previewModalHtml = `
        <div class="modal fade draggable-modal" id="previewModal" tabindex="-1">
            <style>
                .draggable-modal .modal-dialog { position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%); max-width: 95%; width: 80%; height: 80%; }
                .draggable-modal .modal-content { position: relative; height: 100%; display: flex; flex-direction: column; }
                .draggable-modal .modal-header { cursor: move; user-select: none; display: flex; align-items: center; justify-content: space-between; }
                .draggable-modal .modal-body { position: relative; overflow: auto; flex: 1 1 auto; }
                .draggable-modal .modal-resizer { width: 28px; height: 28px; position: absolute; right: -6px; bottom: -6px; cursor: se-resize; opacity: 1; z-index: 10050; background: rgba(0,0,0,0.06); border-radius: 4px; box-shadow: 0 0 0 1px rgba(0,0,0,0.04) inset; pointer-events: auto; }
                .draggable-modal .modal-resizer:after { content: ""; position: absolute; right: 6px; bottom: 6px; width: 12px; height: 12px; border-right: 2px solid rgba(0,0,0,0.45); border-bottom: 2px solid rgba(0,0,0,0.45); transform: rotate(0deg); pointer-events: none; } 
                .preview-maximize-btn { margin-right: 8px; }
            </style>
            <div class="modal-dialog" id="preview-dialog">
                <div class="modal-content">
                    <div class="modal-header" id="preview-header">
                        <h5 class="modal-title">${t('preview')}</h5>
                        <div class="d-flex gap-2 align-items-center">
                            <button type="button" class="btn btn-sm btn-outline-secondary preview-maximize-btn" id="maximize-btn" aria-label="Maximize">
                                <i class="bi bi-arrows-fullscreen" style="font-size: 1rem;"></i>
                            </button>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                    </div>
                    <div class="modal-body p-0" id="preview-modal-body" style="height: 100%;">
                        ${bodyContent}
                    </div>
                    <div class="modal-resizer" id="preview-resizer" title="Resize"></div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing preview modal if any
    const existingModal = document.getElementById('previewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add new modal to body
    document.body.insertAdjacentHTML('beforeend', previewModalHtml);
    
    // Show modal
    const modalEl = document.getElementById('previewModal');
    // Save preview type for later behaviors on both modal and dialog elements
    const dialogEl = document.getElementById('preview-dialog');
    if (dialogEl) dialogEl.dataset.previewType = fileType;
    if (modalEl) modalEl.dataset.previewType = fileType;
    const previewModal = new bootstrap.Modal(modalEl);
    previewModal.show();

    // Ensure dialog is centered using pixel coordinates (avoid transform-based positioning)
    setTimeout(() => {
        const dialog = document.getElementById('preview-dialog');
        const modalBody = document.getElementById('preview-modal-body');
        if (dialog) {
            dialog.style.position = 'fixed';
            dialog.style.transform = 'none';
            dialog.style.margin = '0';
            // compute size and center in px
            const w = Math.round(window.innerWidth * 0.8);
            const h = Math.round(window.innerHeight * 0.8);
            const left = Math.round((window.innerWidth - w) / 2);
            const top = Math.round((window.innerHeight - h) / 2);
            dialog.style.width = w + 'px';
            dialog.style.height = h + 'px';
            dialog.style.left = left + 'px';
            dialog.style.top = top + 'px';
        }

        // If this is a PDF preview, let the iframe handle scrolling to avoid duplicate scrollbars
        try {
            const modalEl = document.getElementById('previewModal');
            if (modalEl && modalEl.dataset.previewType === 'pdf') {
                if (modalBody) {
                    modalBody.style.overflow = 'hidden';
                }
                const iframe = modalEl.querySelector('iframe');
                if (iframe) {
                    iframe.style.height = '100%';
                    iframe.style.width = '100%';
                }
            } else if (modalBody) {
                modalBody.style.overflow = 'auto';
            }
        } catch (e) {
            console.warn('Preview init overflow handling failed', e);
        }
    }, 25);

    // Setup draggable and resizable behavior
    setTimeout(() => {
        const dialog = document.getElementById('preview-dialog');
        const header = document.getElementById('preview-header');
        const resizer = document.getElementById('preview-resizer');
        const maximizeBtn = document.getElementById('maximize-btn');

        makeModalDraggable(dialog, header);
        makeModalResizable(dialog, resizer);

        // Maximize toggle
        maximizeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            togglePreviewMaximize();
        });

    }, 50);
    
    // Clean up on hide
    modalEl.addEventListener('hidden.bs.modal', function() {
        // Remove to avoid memory leaks
        this.remove();
    });
}

function togglePreviewMaximize() {
    const dialog = document.getElementById('preview-dialog');
    const modalBody = document.getElementById('preview-modal-body');
    const maximizeBtn = document.getElementById('maximize-btn');
    
    if (!dialog) return;
    const header = dialog.querySelector('.modal-header');
    const headerHeight = header ? Math.ceil(header.getBoundingClientRect().height) : 56;

    if (!dialog.dataset.maximized || dialog.dataset.maximized === 'false') {
        // Save current size/position in px
        dialog.dataset.prevLeft = dialog.style.left || dialog.getBoundingClientRect().left + 'px';
        dialog.dataset.prevTop = dialog.style.top || dialog.getBoundingClientRect().top + 'px';
        dialog.dataset.prevWidth = dialog.style.width || dialog.getBoundingClientRect().width + 'px';
        dialog.dataset.prevHeight = dialog.style.height || dialog.getBoundingClientRect().height + 'px';
        dialog.dataset.prevTransform = dialog.style.transform || 'none';
        
        // Maximize to exact viewport bounds (use client dims to avoid fractional gaps)
        const vw = document.documentElement.clientWidth;
        const vh = document.documentElement.clientHeight;
        // Use left/top/right/bottom to avoid fractional gaps on right/bottom
        dialog.style.left = '0px';
        dialog.style.top = '0px';
        dialog.style.right = '0px';
        dialog.style.bottom = '0px';
        dialog.style.width = 'auto';
        dialog.style.height = 'auto';
        dialog.style.transform = 'none';
        dialog.style.margin = '0';
        if (modalBody) modalBody.style.height = (vh - headerHeight) + 'px';
        dialog.dataset.maximized = 'true';
        maximizeBtn.classList.add('active');

        // If PDF, ensure only iframe scrolls
        if (dialog.dataset.previewType === 'pdf' && modalBody) {
            modalBody.style.overflow = 'hidden';
            const iframe = dialog.querySelector('iframe');
            if (iframe) iframe.style.height = (vh - headerHeight) + 'px';
        }
    } else {
        // Restore
        // Remove any right/bottom used in maximized state and restore previous values
        dialog.style.right = '';
        dialog.style.bottom = '';
        dialog.style.left = dialog.dataset.prevLeft || '50%';
        dialog.style.top = dialog.dataset.prevTop || '50%';
        dialog.style.width = dialog.dataset.prevWidth || '80%';
        dialog.style.height = dialog.dataset.prevHeight || '80%';
        dialog.style.transform = dialog.dataset.prevTransform || 'none';
        if (modalBody) modalBody.style.height = '';
        dialog.dataset.maximized = 'false';
        maximizeBtn.classList.remove('active');

        // Restore PDF scroll behavior
        if (dialog.dataset.previewType === 'pdf' && modalBody) {
            modalBody.style.overflow = 'hidden';
            const iframe = dialog.querySelector('iframe');
            if (iframe) iframe.style.height = '100%';
        }
    }
}

// Make modal draggable by header
function makeModalDraggable(dialog, handle) {
    if (!dialog || !handle) return;
    let isDragging = false;
    let startX = 0, startY = 0, startLeft = 0, startTop = 0;
    let overlay = null;

    handle.addEventListener('mousedown', (e) => {
        // Only start drag on left mouse button
        if (e.button !== 0) return;
        // Ignore drags that start from interactive elements (buttons, links, inputs)
        if (e.target.closest('button, a, input, textarea, select, .btn, .btn-close')) return;
        e.preventDefault();
        isDragging = true;
        const rect = dialog.getBoundingClientRect();
        startX = e.clientX;
        startY = e.clientY;
        startLeft = rect.left;
        startTop = rect.top;
        // Cancel transform to allow pixel positioning and prevent jumpy transitions
        dialog.style.transition = 'none';
        dialog.style.transform = 'none';
        dialog.style.left = `${startLeft}px`;
        dialog.style.top = `${startTop}px`;
        document.body.style.userSelect = 'none';

        // Add overlay to capture mouse events (prevents iframe interference)
        overlay = document.createElement('div');
        overlay.id = 'modal-interaction-overlay';
        overlay.style.position = 'fixed';
        overlay.style.left = 0;
        overlay.style.top = 0;
        overlay.style.right = 0;
        overlay.style.bottom = 0;
        overlay.style.zIndex = 10051;
        overlay.style.cursor = 'move';
        document.body.appendChild(overlay);

        // Attach listeners to overlay to ensure we capture events even over iframes
        overlay.addEventListener('mousemove', onMouseMove);
        overlay.addEventListener('mouseup', stopDrag);
    });

    function onMouseMove(e) {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        const rect = dialog.getBoundingClientRect();
        let newLeft = startLeft + dx;
        let newTop = startTop + dy;
        // Clamp so dialog stays at least partly on-screen
        newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - rect.width));
        newTop = Math.max(0, Math.min(newTop, window.innerHeight - 40));
        dialog.style.left = `${newLeft}px`;
        dialog.style.top = `${newTop}px`;
    }

    function stopDrag() {
        if (!isDragging) return;
        isDragging = false;
        document.body.style.userSelect = '';
        // restore transition
        dialog.style.transition = '';
        if (overlay) {
            overlay.removeEventListener('mousemove', onMouseMove);
            overlay.removeEventListener('mouseup', stopDrag);
            document.body.removeChild(overlay);
            overlay = null;
        }
    }

    // Also listen on document in case overlay isn't available
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', stopDrag);
}

// Make modal resizable via a small handle
function makeModalResizable(dialog, resizer) {
    if (!dialog || !resizer) return;
    let isResizing = false;
    let startX = 0, startY = 0, startWidth = 0, startHeight = 0;
    let overlay = null;

    resizer.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isResizing = true;
        const rect = dialog.getBoundingClientRect();
        startX = e.clientX;
        startY = e.clientY;
        startWidth = rect.width;
        startHeight = rect.height;
        document.body.style.userSelect = 'none';
        // disable transitions during resize to avoid jank
        dialog.style.transition = 'none';

        // Add overlay to capture mouse events (prevents iframe interference)
        overlay = document.createElement('div');
        overlay.id = 'modal-interaction-overlay';
        overlay.style.position = 'fixed';
        overlay.style.left = 0;
        overlay.style.top = 0;
        overlay.style.right = 0;
        overlay.style.bottom = 0;
        overlay.style.zIndex = 10051;
        overlay.style.cursor = 'se-resize';
        document.body.appendChild(overlay);

        overlay.addEventListener('mousemove', onMouseMove);
        overlay.addEventListener('mouseup', stopResize);
    });

    function onMouseMove(e) {
        if (!isResizing) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        let newWidth = Math.max(400, startWidth + dx);
        let newHeight = Math.max(200, startHeight + dy);
        // Clamp to viewport
        newWidth = Math.min(newWidth, window.innerWidth - 40);
        newHeight = Math.min(newHeight, window.innerHeight - 40);
        dialog.style.width = `${newWidth}px`;
        dialog.style.height = `${newHeight}px`;
        // Adjust body height so content fits
        const header = dialog.querySelector('.modal-header');
        const headerHeight = header ? header.getBoundingClientRect().height : 56;
        const modalBody = dialog.querySelector('.modal-body');
        if (modalBody) modalBody.style.height = `${Math.max(100, newHeight - headerHeight)}px`;
    }

    function stopResize() {
        if (!isResizing) return;
        isResizing = false;
        document.body.style.userSelect = '';
        // restore transitions
        dialog.style.transition = '';
        if (overlay) {
            overlay.removeEventListener('mousemove', onMouseMove);
            overlay.removeEventListener('mouseup', stopResize);
            document.body.removeChild(overlay);
            overlay = null;
        }
    }

    // Also listen on document as fallback
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', stopResize);
}

// Preview document in new tab
function previewDocument(id, fileType) {
    window.open(`/api/documents/${id}/preview`, '_blank');
}

// Download document
function downloadDocument(id, filename) {
    const link = document.createElement('a');
    link.href = `/api/documents/${id}/download`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Reprocess document
async function reprocessDocument(id) {
    try {
        // Get selected AI model from dropdown
        const aiModelSelect = document.getElementById('reprocess-ai-model');
        const aiModel = aiModelSelect ? aiModelSelect.value : null;
        
        const payload = {};
        if (aiModel) {
            payload.ai_model = aiModel;
        }
        
        await API.post(`/api/documents/${id}/reprocess`, payload);
        showToast(t('reprocess_success'), 'success');
        
        bootstrap.Modal.getInstance(document.getElementById('documentModal')).hide();
        loadDocuments(currentPage);
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Download document
function downloadDocument(id) {
    window.open(`/api/documents/${id}/download`, '_blank');
}

// Delete document
async function deleteDocument(id) {
    if (!confirm(t('confirm_delete'))) {
        return;
    }
    
    try {
        await API.delete(`/api/documents/${id}/delete`);
        showToast(t('delete_success'), 'success');
        
        loadDocuments(currentPage);
        loadRecentDocuments();
        loadStats();
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Logout
async function logout() {
    try {
        await API.post('/api/auth/logout');
        window.location.href = '/login';
    } catch (error) {
        window.location.href = '/login';
    }
}

// ============================================
// CATEGORY MANAGEMENT FUNCTIONS
// ============================================

// Load categories management view
async function loadCategoriesManagement() {
    try {
        const categories = await API.get('/api/categories');
        const container = document.getElementById('categories-list');
        
        // Get previously expanded category
        const expandedCatId = localStorage.getItem('expandedCategoryId');
        
        if (categories.length === 0) {
            container.innerHTML = `<p class="text-muted text-center py-4">${t('no_categories')}</p>`;
            return;
        }
        
        container.innerHTML = categories.map((cat, index) => {
            const isExpanded = expandedCatId ? cat.id == expandedCatId : index === 0;
            return `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button ${isExpanded ? '' : 'collapsed'}" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#collapse${cat.id}"
                            onclick="localStorage.setItem('expandedCategoryId', '${cat.id}')">
                        ${cat.name} <span class="badge bg-primary ms-2">${cat.subcategories ? cat.subcategories.length : 0}</span>
                    </button>
                </h2>
                <div id="collapse${cat.id}" class="accordion-collapse collapse ${isExpanded ? 'show' : ''}" 
                     data-bs-parent="#categories-list">
                    <div class="accordion-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <p class="mb-0 text-muted">${cat.description || `${t('no_description')}`}</p>
                            <div>
                                <button class="btn btn-sm btn-outline-primary me-1" 
                                        onclick="showEditCategoryModal(${cat.id}, '${cat.name.replace(/'/g, "\\'")}', '${(cat.description || '').replace(/'/g, "\\'")}')">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" 
                                        onclick="deleteCategory(${cat.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                        
                        <h6 class="mb-2">${t('subcategories')}:</h6>
                        <ul class="list-group mb-2">
                            ${(cat.subcategories || []).map(sub => `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    ${sub.name}
                                    <div>
                                        <button class="btn btn-sm btn-outline-primary me-1" 
                                                onclick="showEditSubcategoryModal(${sub.id}, '${sub.name.replace(/'/g, "\\'")}', ${cat.id}, '${cat.name.replace(/'/g, "\\'")}')">
                                            <i class="bi bi-pencil"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger" 
                                                onclick="deleteSubcategory(${sub.id})">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                        <button class="btn btn-sm btn-success" onclick="showAddSubcategoryModal(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')">
                            <i class="bi bi-plus-circle"></i> ${t('add_subcategory')}
                        </button>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Show add category modal
function showAddCategoryModal() {
    document.getElementById('category-id').value = '';
    document.getElementById('category-name-input').value = '';
    document.getElementById('category-desc-input').value = '';
    document.getElementById('category-modal-title').textContent = t('add_category');
    new bootstrap.Modal(document.getElementById('categoryModal')).show();
}

// Show edit category modal
function showEditCategoryModal(id, name, description) {
    document.getElementById('category-id').value = id;
    document.getElementById('category-name-input').value = name;
    document.getElementById('category-desc-input').value = description;
    document.getElementById('category-modal-title').textContent = t('edit_category');
    new bootstrap.Modal(document.getElementById('categoryModal')).show();
}

// Save category (create or update)
async function saveCategory() {
    const id = document.getElementById('category-id').value;
    const name = document.getElementById('category-name-input').value.trim();
    const description = document.getElementById('category-desc-input').value.trim();
    
    if (!name) {
        alert('Please enter a category name');
        return;
    }
    
    try {
        let newCategoryId = id;
        
        if (id) {
            // Update
            await API.put(`/api/categories/${id}`, { name, description });
            showToast(t('category_updated'), 'success');
            // Keep the same category expanded
            localStorage.setItem('expandedCategoryId', id);
        } else {
            // Create
            const response = await API.post('/api/categories', { name, description });
            showToast(t('category_added'), 'success');
            // Expand the newly created category
            newCategoryId = response.id;
            localStorage.setItem('expandedCategoryId', newCategoryId);
        }
        
        bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
        loadCategoriesManagement();
        loadCategories(); // Refresh filters
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Delete category
async function deleteCategory(id) {
    if (!confirm(t('confirm_delete_category'))) {
        return;
    }
    
    try {
        await API.delete(`/api/categories/${id}`);
        showToast(t('category_deleted'), 'success');
        loadCategoriesManagement();
        loadCategories(); // Refresh filters
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Show add subcategory modal
function showAddSubcategoryModal(categoryId, categoryName) {
    document.getElementById('subcategory-id').value = '';
    document.getElementById('subcategory-category-id').value = categoryId;
    document.getElementById('parent-category-name').value = categoryName;
    document.getElementById('subcategory-name-input').value = '';
    document.getElementById('subcat-modal-title').textContent = t('add_subcategory');
    new bootstrap.Modal(document.getElementById('subcategoryModal')).show();
}

// Show edit subcategory modal
function showEditSubcategoryModal(id, name, categoryId, categoryName) {
    document.getElementById('subcategory-id').value = id;
    document.getElementById('subcategory-category-id').value = categoryId;
    document.getElementById('parent-category-name').value = categoryName;
    document.getElementById('subcategory-name-input').value = name;
    document.getElementById('subcat-modal-title').textContent = t('edit_category');
    new bootstrap.Modal(document.getElementById('subcategoryModal')).show();
}

// Save subcategory (create or update)
async function saveSubcategory() {
    const id = document.getElementById('subcategory-id').value;
    const categoryId = document.getElementById('subcategory-category-id').value;
    const name = document.getElementById('subcategory-name-input').value.trim();
    
    if (!name) {
        alert('Please enter a subcategory name');
        return;
    }
    
    try {
        if (id) {
            // Update
            await API.put(`/api/subcategories/${id}`, { name });
            showToast(t('category_updated'), 'success');
        } else {
            // Create
            await API.post('/api/subcategories', { name, category_id: parseInt(categoryId) });
            showToast(t('category_added'), 'success');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('subcategoryModal')).hide();
        loadCategoriesManagement();
        loadCategories(); // Refresh filters
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Delete subcategory
async function deleteSubcategory(id) {
    if (!confirm(t('confirm_delete_category'))) {
        return;
    }
    
    try {
        await API.delete(`/api/subcategories/${id}`);
        showToast(t('category_deleted'), 'success');
        loadCategoriesManagement();
        loadCategories(); // Refresh filters
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

// Password Management
let passwordsData = [];

async function loadPasswords() {
    try {
        const response = await API.get('/api/user/settings/pdf-passwords');
        passwordsData = response.passwords || [];
        renderPasswords();
    } catch (error) {
        console.error('Failed to load passwords:', error);
        passwordsData = [];
        renderPasswords();
    }
}

function renderPasswords() {
    const container = document.getElementById('passwords-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (passwordsData.length === 0) {
        container.innerHTML = `<p class="text-muted"><em>${t('no_passwords_configured')}</em></p>`;
        return;
    }
    
    passwordsData.forEach((password, index) => {
        const div = document.createElement('div');
        div.className = 'input-group mb-2';
        div.innerHTML = `
            <input type="password" class="form-control" id="password-${index}" value="${password}" onchange="updatePassword(${index}, this.value)" placeholder="${t('password_placeholder')}">
            <button class="btn btn-outline-secondary" type="button" onclick="togglePasswordVisibility(${index})" title="Show/Hide">
                <i class="bi bi-eye" id="eye-icon-${index}"></i>
            </button>
            <button class="btn btn-outline-danger" type="button" onclick="removePassword(${index})">
                <i class="bi bi-trash"></i>
            </button>
        `;
        container.appendChild(div);
    });
}

function togglePasswordVisibility(index) {
    const input = document.getElementById(`password-${index}`);
    const icon = document.getElementById(`eye-icon-${index}`);
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

function addPasswordField() {
    passwordsData.push('');
    renderPasswords();
    // Focus on the new input
    const inputs = document.querySelectorAll('#passwords-list input');
    if (inputs.length > 0) {
        inputs[inputs.length - 1].focus();
    }
}

function updatePassword(index, value) {
    passwordsData[index] = value;
}

function removePassword(index) {
    passwordsData.splice(index, 1);
    renderPasswords();
}

async function savePasswords() {
    try {
        // Filter out empty passwords
        const filteredPasswords = passwordsData.filter(p => p && p.trim());
        
        const response = await API.post('/api/user/settings/pdf-passwords', {
            passwords: filteredPasswords
        });
        
        passwordsData = response.passwords || filteredPasswords;
        renderPasswords();
        showToast(t('passwords_saved'), 'success');
    } catch (error) {
        showToast(t('error') + ': ' + error.message, 'error');
    }
}

async function loadUserInfo() {
    try {
        const user = await API.get('/api/auth/me');
        document.getElementById('user-username').textContent = user.username;
        document.getElementById('user-email').textContent = user.email;
        const createdDate = new Date(user.created_at);
        document.getElementById('user-created').textContent = createdDate.toLocaleDateString();
    } catch (error) {
        console.error('Failed to load user info:', error);
    }
}
