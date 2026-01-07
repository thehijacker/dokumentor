// Translations
const translations = {
    en: {
        // App
        app_name: "Dokumentor",
        welcome: "Welcome",
        logout: "Logout",
        
        // Auth
        login: "Login",
        register: "Register",
        username: "Username",
        email: "Email",
        password: "Password",
        no_account: "Don't have an account?",
        have_account: "Already have an account?",
        registration_disabled: "Registration is currently disabled",
        
        // Navigation
        dashboard: "Dashboard",
        documents: "Documents",
        upload: "Upload",
        categories: "Categories",
        settings: "Settings",
        
        // Documents
        all_documents: "All Documents",
        my_documents: "My Documents",
        upload_document: "Upload Document",
        search: "Search...",
        filter_by_category: "Filter by Category",
        filter_by_subcategory: "Filter by Subcategory",
        all_categories: "All Categories",
        all_subcategories: "All Subcategories",
        no_documents: "No documents found",
        file_name: "File Name",
        category: "Category",
        subcategory: "Subcategory",
        uploaded: "Uploaded",
        confidence: "Confidence",
        actions: "Actions",
        
        // Actions
        view: "View",
        preview: "Preview",
        edit: "Edit",
        delete: "Delete",
        download: "Download",
        reprocess: "Reprocess",
        save: "Save",
        cancel: "Cancel",
        
        // Upload
        select_file: "Select File",
        or_drag_drop: "or drag and drop",
        take_photo: "Take Photo",
        supported_formats: "Supported formats: PDF, DOCX, PNG, JPG, JPEG, TIFF, BMP",
        max_file_size: "Maximum file size: 50MB",
        uploading: "Uploading...",
        processing: "Processing...",
        upload_success: "Document uploaded successfully!",
        upload_error: "Upload failed",
        duplicate_file: "Duplicate file detected. This file was already uploaded",
        files_uploaded: "files uploaded successfully",
        new_documents_processed: "new document(s) processed from watch folder",
        camera_access_denied: "Camera access denied",
        auto_categorize: "Auto-categorize uploaded files",
        select_category_first: "Please select category first",
        select_subcategory: "Select subcategory...",
        ai_model: "AI Model",
        ai_model_internal: "Internal ML (Pretrained)",
        ai_model_ollama: "Ollama",
        ai_model_openai: "OpenAI",
        ai_model_reprocess: "AI Model for Reprocessing",
        ai_model_reprocess_help: "Choose AI model to use for reprocessing. Default uses pretrained ML model with automatic Ollama fallback if confidence is low.",
        ai_model_help: "Choose AI model for categorization. Default uses pretrained ML model with automatic Ollama fallback if confidence is low.",
        default: "Default (Pretrained ML with Ollama fallback)",
        internal: "Internal",
        ollama: "Ollama",
        openai: "OpenAI",
        
        // Details
        document_details: "Document Details",
        original_name: "Original Name",
        file_type: "File Type",
        file_size: "File Size",
        processed_at: "Processed At",
        ocr_text: "OCR Text",
        ocr_language: "OCR Language",
        extracted_data: "Extracted Data",
        amounts: "Amounts",
        dates: "Dates",
        invoice_numbers: "Invoice Numbers",
        notes: "Notes",
        bill_value: "Bill Value",
        has_notes: "Has notes",
        no_bill_value: "N/A",
        tags: "Tags",
        manually_categorized: "Manually Categorized",
        docx_preview_unavailable: "This document cannot be previewed inline. You can open it in a new tab or download it.",
        open_in_new_tab: "Open in New Tab",
        download: "Download",
        
        // Stats
        total_documents: "Total Documents",
        processed_documents: "Processed Documents",
        documents_by_category: "Documents by Category",
        
        // Messages
        confirm_delete: "Are you sure you want to delete this document?",
        delete_success: "Document deleted successfully",
        save_success: "Changes saved successfully",
        reprocess_success: "Document reprocessed successfully",
        error: "Error",
        loading: "Loading...",
        
        // Categories
        monthly_costs: "Monthly Costs",
        shops: "Shops",
        medical: "Medical",
        automotive: "Automotive",
        other: "Other",
        
        // Category Management
        manage_categories: "Manage Categories",
        add_category: "Add Category",
        add_subcategory: "Add Subcategory",
        edit_category: "Edit Category",
        delete_category: "Delete Category",
        category_name: "Category Name",
        category_description: "Category Description",
        confirm_delete_category: "Are you sure you want to delete this category and all its subcategories?",
        category_added: "Category added successfully",
        category_updated: "Category updated successfully",
        category_deleted: "Category deleted successfully",
        subcategory_name: "Subcategory Name",
        parent_category: "Parent Category",
        subcategories: "Subcategories",
        categories_and_subcategories: "Categories & Subcategories",
        information: "Information",
        tips: "Tips",
        category_info_text: "Manage your document categories and subcategories here. Categories help organize and automatically classify your documents.",
        category_tip_1: "Create categories that match your document types",
        category_tip_2: "Use subcategories for more specific classification",
        category_tip_3: "The AI will learn from your corrections",
        no_categories: "No categories. Click 'Add Category' to create the first one.",
        no_description: "No description",
        
        // Settings
        pdf_passwords: "PDF Passwords",
        pdf_passwords_desc: "Manage passwords for encrypted PDF documents. These passwords will be tried automatically when previewing or processing encrypted PDFs.",
        add_password: "Add Password",
        save_passwords: "Save Passwords",
        user_info: "User Information",
        member_since: "Member Since",
        password_placeholder: "Enter PDF password",
        passwords_saved: "Passwords saved successfully",
        remove: "Remove",
        no_passwords_configured: "No passwords configured"
    },
    sl: {
        // App
        app_name: "Dokumentor",
        welcome: "Živijo",
        logout: "Odjava",
        
        // Auth
        login: "Prijava",
        register: "Registracija",
        username: "Uporabniško ime",
        email: "E-pošta",
        password: "Geslo",
        no_account: "Nimate računa?",
        have_account: "Že imate račun?",
        registration_disabled: "Registracija je trenutno onemogočena",
        
        // Navigation
        dashboard: "Nadzorna plošča",
        documents: "Dokumenti",
        upload: "Naloži",
        categories: "Kategorije",
        settings: "Nastavitve",
        
        // Documents
        all_documents: "Vsi dokumenti",
        my_documents: "Moji dokumenti",
        upload_document: "Naloži dokument",
        search: "Iskanje...",
        filter_by_category: "Filtriraj po kategoriji",
        filter_by_subcategory: "Filtriraj po podkategoriji",
        all_categories: "Vse kategorije",
        all_subcategories: "Vse podkategorije",
        no_documents: "Ni najdenih dokumentov",
        file_name: "Ime datoteke",
        category: "Kategorija",
        subcategory: "Podkategorija",
        uploaded: "Naloženo",
        confidence: "Zaupanje",
        actions: "Dejanja",
        
        // Actions
        view: "Poglej",
        preview: "Predogled",
        edit: "Uredi",
        delete: "Izbriši",
        download: "Prenesi",
        reprocess: "Ponovno obdelaj",
        save: "Shrani",
        cancel: "Prekliči",
        
        // Upload
        select_file: "Izberi datoteko",
        or_drag_drop: "ali povleci in spusti",
        take_photo: "Zajemi sliko",
        supported_formats: "Podprti formati: PDF, DOCX, PNG, JPG, JPEG, TIFF, BMP",
        max_file_size: "Največja velikost datoteke: 50MB",
        uploading: "Nalaganje...",
        processing: "Obdelava...",
        upload_success: "Dokument uspešno naložen!",
        upload_error: "Nalaganje ni uspelo",
        duplicate_file: "Podvojena datoteka. Ta datoteka je že bila naložena",
        files_uploaded: "datotek uspešno naloženih",
        new_documents_processed: "nov(ih) dokument(ov) obdelanih iz spremljane mape",
        camera_access_denied: "Dostop do kamere zavrnjen",
        auto_categorize: "Samodejno kategoriziraj naložene datoteke",
        select_category_first: "Najprej izberite kategorijo",
        select_subcategory: "Izberite podkategorijo",
        ai_model: "AI Model",
        ai_model_internal: "Notranji ML (Predhodno naučen)",
        ai_model_ollama: "Ollama",
        ai_model_openai: "OpenAI",
        ai_model_reprocess: "AI Model za ponovno obdelavo",
        ai_model_reprocess_help: "Izberite AI model za ponovno obdelavo. Privzeto uporablja predhodno naučen ML model s samodejnim preklopom na Ollama, če je zaupanje nizko.",
        ai_model_help: "Izberite AI model za kategorizacijo. Privzeto uporablja predhodno naučen ML model s samodejnim preklopom na Ollama, če je zaupanje nizko.",
        default: "Privzeto (Predhodno naučen ML s preklopom na Ollama)",
        internal: "Notranji",
        ollama: "Ollama",
        openai: "OpenAI",
        
        // Details
        document_details: "Podrobnosti dokumenta",
        original_name: "Izvorno ime",
        file_type: "Tip datoteke",
        file_size: "Velikost datoteke",
        processed_at: "Obdelano",
        ocr_text: "OCR besedilo",
        ocr_language: "OCR jezik",
        extracted_data: "Izvlečeni podatki",
        amounts: "Zneski",
        dates: "Datumi",
        invoice_numbers: "Številke računov",
        notes: "Opombe",
        bill_value: "Vrednost računa",
        has_notes: "Ima opombe",
        no_bill_value: "Ni podatka",
        tags: "Oznake",
        manually_categorized: "Ročno kategorizirano",
        docx_preview_unavailable: "Ta dokument ni mogoče predogledati v vrstici. Odprite ga lahko v novem zavihku ali prenesete.",
        open_in_new_tab: "Odpri v novem zavihku",
        download: "Prenesi",
        
        // Stats
        total_documents: "Skupaj dokumentov",
        processed_documents: "Obdelanih dokumentov",
        documents_by_category: "Dokumenti po kategorijah",
        
        // Messages
        confirm_delete: "Ali ste prepričani, da želite izbrisati ta dokument?",
        delete_success: "Dokument uspešno izbrisan",
        save_success: "Spremembe uspešno shranjene",
        reprocess_success: "Dokument uspešno ponovno obdelan",
        error: "Napaka",
        loading: "Nalaganje...",
        
        // Categories
        monthly_costs: "Mesečni stroški",
        shops: "Trgovine",
        medical: "Zdravstvo",
        automotive: "Avtomobilsko",
        other: "Ostalo",
        
        // Category Management
        manage_categories: "Upravljanje kategorij",
        add_category: "Dodaj kategorijo",
        add_subcategory: "Dodaj podkategorijo",
        edit_category: "Uredi kategorijo",
        delete_category: "Izbriši kategorijo",
        category_name: "Ime kategorije",
        category_description: "Opis kategorije",
        confirm_delete_category: "Ali ste prepričani, da želite izbrisati to kategorijo in vse njene podkategorije?",
        category_added: "Kategorija uspešno dodana",
        category_updated: "Kategorija uspešno posodobljena",
        category_deleted: "Kategorija uspešno izbrisana",
        subcategory_name: "Ime podkategorije",
        parent_category: "Nadrejena kategorija",
        subcategories: "Podkategorije",
        categories_and_subcategories: "Kategorije in podkategorije",
        information: "Informacije",
        tips: "Nasveti",
        category_info_text: "Upravljajte kategorije in podkategorije dokumentov. Kategorije pomagajo organizirati in samodejno razvrstiti dokumente.",
        category_tip_1: "Ustvarite kategorije, ki ustrezajo vašim vrstam dokumentov",
        category_tip_2: "Uporabite podkategorije za natančnejšo razvrstitev",
        category_tip_3: "Umetna inteligenca se bo učila iz vaših popravkov",
        no_categories: "Ni kategorij. Kliknite 'Dodaj kategorijo', da ustvarite prvo.",
        no_description: "Ni opisa",
        
        // Settings
        pdf_passwords: "PDF Gesla",
        pdf_passwords_desc: "Upravljajte gesla za šifrirane PDF dokumente. Ta gesla bodo samodejno poskušena pri predogledu ali obdelavi šifriranih PDF-jev.",
        add_password: "Dodaj geslo",
        save_passwords: "Shrani gesla",
        user_info: "Podatki o uporabniku",
        member_since: "Član od",
        password_placeholder: "Vnesite PDF geslo",
        passwords_saved: "Gesla uspešno shranjena",
        remove: "Odstrani",
        no_passwords_configured: "Ni nastavljenih gesel"
    }
};

// Get browser language
function getBrowserLanguage() {
    const lang = navigator.language || navigator.userLanguage;
    const shortLang = lang.split('-')[0];
    return ['en', 'sl'].includes(shortLang) ? shortLang : 'en';
}

// Get current language from localStorage or browser
function getCurrentLanguage() {
    return localStorage.getItem('language') || getBrowserLanguage();
}

// Set language
function setLanguage(lang) {
    localStorage.setItem('language', lang);
    location.reload();
}

// Translation function
function t(key) {
    const lang = getCurrentLanguage();
    return translations[lang][key] || key;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString(getCurrentLanguage() === 'sl' ? 'sl-SI' : 'en-US');
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const container = document.getElementById('toast-container');
    if (container) {
        container.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = container.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
    }
}

// API wrapper
const API = {
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    get(url) {
        return this.request(url);
    },
    
    post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
};
