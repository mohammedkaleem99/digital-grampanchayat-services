// =============================================================
// Digital Gram Panchayat — Shared JS Utilities (app.js)
// All pages include this file for common helpers
// =============================================================

const API_BASE = 'http://localhost:5000/api';

// -------------------------------------------------------
// Notification Toast (bottom-right popup)
// -------------------------------------------------------
function showNotification(message, type = 'success') {
    const notif = document.getElementById('notification');
    if (!notif) return;

    // Set icon based on type
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    notif.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;
    notif.className = `show ${type}`;

    setTimeout(() => { notif.className = ''; }, 3500);
}

// -------------------------------------------------------
// Auth helpers (UNCHANGED — existing logic preserved)
// -------------------------------------------------------
function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}

function checkAuth(roleRequired = null) {
    const user = getUser();
    if (!user) {
        window.location.href = 'index.html';
        return null;
    }
    if (roleRequired && user.role !== roleRequired) {
        window.location.href = user.role === 'admin' ? 'admin.html' : 'dashboard.html';
        return null;
    }
    return user;
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// -------------------------------------------------------
// Login (UNCHANGED)
// -------------------------------------------------------
async function handleLogin(e) {
    e.preventDefault();
    const email    = document.getElementById('log-email').value;
    const password = document.getElementById('log-password').value;

    try {
        const res  = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('user', JSON.stringify(data.user));
            showNotification('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = data.user.role === 'admin' ? 'admin.html' : 'dashboard.html';
            }, 900);
        } else {
            showNotification(data.error, 'error');
        }
    } catch (err) {
        showNotification('Cannot connect to server. Is Flask running?', 'error');
    }
}

// -------------------------------------------------------
// Register (UNCHANGED)
// -------------------------------------------------------
async function handleRegister(e) {
    e.preventDefault();
    const name     = document.getElementById('reg-name').value;
    const email    = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        const res  = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (res.ok) {
            showNotification('Registration successful! Please login.', 'success');
            toggleAuthMode('login');
        } else {
            showNotification(data.error, 'error');
        }
    } catch (err) {
        showNotification('Cannot connect to server.', 'error');
    }
}

// Toggle between Login / Register panels
function toggleAuthMode(mode) {
    document.getElementById('login-form').classList.toggle('hidden', mode !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', mode !== 'register');
}

// -------------------------------------------------------
// Sidebar mobile toggle
// -------------------------------------------------------
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('open');
}

// -------------------------------------------------------
// Status badge helper
// -------------------------------------------------------
function statusBadge(status) {
    const map = {
        'Pending':     'badge-pending',
        'Approved':    'badge-approved',
        'Rejected':    'badge-rejected',
        'Resolved':    'badge-resolved',
        'In Progress': 'badge-progress',
        'urgent':      'badge-urgent',
        'normal':      'badge-normal',
    };
    return `<span class="badge ${map[status] || 'badge-blue'}">${status}</span>`;
}

// -------------------------------------------------------
// Format date nicely
// -------------------------------------------------------
function fmtDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric'
    });
}

// -------------------------------------------------------
// Service form config — defines fields per service
// Each entry: { id, label, type, required, placeholder, ... }
// -------------------------------------------------------
const SERVICE_FORMS = {
    // ---- Birth Certificate ----
    1: {
        title: 'Birth Certificate Application',
        sections: [
            {
                title: 'Child Information',
                fields: [
                    { id: 'full_name',    label: "Child's Full Name",  type: 'text', required: true },
                    { id: 'date_of_birth',label: 'Date of Birth',       type: 'date', required: true },
                    { id: 'gender',       label: 'Gender',               type: 'select',
                      options: ['Male','Female','Other'], required: true },
                    { id: 'father_name',  label: "Father's Name",        type: 'text', required: true },
                    { id: 'mother_name',  label: "Mother's Name",        type: 'text', required: true },
                ]
            },
            {
                title: 'Contact Details',
                fields: [
                    { id: 'address', label: 'Residential Address', type: 'textarea', required: true },
                    { id: 'village', label: 'Village / Ward',      type: 'text', required: true },
                    { id: 'district',label: 'District',            type: 'text', required: true },
                    { id: 'state',   label: 'State',               type: 'text', required: true },
                    { id: 'pincode', label: 'PIN Code',            type: 'text', required: true },
                    { id: 'mobile',  label: 'Mobile Number',       type: 'tel',  required: true },
                    { id: 'aadhar_number', label: "Parent's Aadhaar No.", type: 'text' },
                ]
            },
            {
                title: 'Required Documents',
                fields: [
                    { id: 'photo',        label: "Child's Photo",        type: 'file' },
                    { id: 'aadhar_card',  label: "Parent's Aadhaar Card", type: 'file', required: true },
                    { id: 'ration_card',  label: 'Ration Card',           type: 'file' },
                    { id: 'other_doc',    label: 'Hospital Birth Record', type: 'file' },
                ]
            }
        ]
    },

    // ---- Death Certificate ----
    2: {
        title: 'Death Certificate Application',
        sections: [
            {
                title: 'Deceased Person Information',
                fields: [
                    { id: 'deceased_name', label: "Deceased Person's Name", type: 'text', required: true },
                    { id: 'date_of_death', label: 'Date of Death',           type: 'date', required: true },
                    { id: 'cause_of_death',label: 'Cause of Death',          type: 'text' },
                    { id: 'gender',        label: 'Gender',                  type: 'select',
                      options: ['Male','Female','Other'] },
                ]
            },
            {
                title: 'Applicant (Next of Kin) Details',
                fields: [
                    { id: 'full_name',  label: "Applicant's Full Name", type: 'text', required: true },
                    { id: 'father_name',label: 'Relation to Deceased',  type: 'text' },
                    { id: 'address',    label: 'Address',               type: 'textarea', required: true },
                    { id: 'village',    label: 'Village / Ward',        type: 'text' },
                    { id: 'district',   label: 'District',              type: 'text' },
                    { id: 'state',      label: 'State',                 type: 'text' },
                    { id: 'mobile',     label: 'Mobile Number',         type: 'tel', required: true },
                    { id: 'aadhar_number', label: "Applicant's Aadhaar", type: 'text' },
                ]
            },
            {
                title: 'Required Documents',
                fields: [
                    { id: 'aadhar_card', label: "Deceased's Aadhaar / ID Proof", type: 'file', required: true },
                    { id: 'other_doc',   label: 'Medical / Hospital Certificate', type: 'file' },
                ]
            }
        ]
    },

    // ---- Income Certificate ----
    3: {
        title: 'Income Certificate Application',
        sections: [
            {
                title: 'Personal Details',
                fields: [
                    { id: 'full_name',   label: 'Full Name',         type: 'text', required: true },
                    { id: 'father_name', label: "Father's Name",     type: 'text', required: true },
                    { id: 'date_of_birth',label: 'Date of Birth',    type: 'date' },
                    { id: 'gender',      label: 'Gender',            type: 'select',
                      options: ['Male','Female','Other'] },
                    { id: 'occupation',  label: 'Occupation',        type: 'text', required: true },
                    { id: 'annual_income', label: 'Annual Income (₹)', type: 'number', required: true },
                ]
            },
            {
                title: 'Address Details',
                fields: [
                    { id: 'address', label: 'Residential Address', type: 'textarea', required: true },
                    { id: 'village', label: 'Village / Ward',      type: 'text', required: true },
                    { id: 'district',label: 'District',            type: 'text', required: true },
                    { id: 'state',   label: 'State',               type: 'text', required: true },
                    { id: 'pincode', label: 'PIN Code',            type: 'text' },
                    { id: 'mobile',  label: 'Mobile',              type: 'tel', required: true },
                    { id: 'aadhar_number', label: 'Aadhaar Number', type: 'text', required: true },
                ]
            },
            {
                title: 'Required Documents',
                fields: [
                    { id: 'photo',       label: 'Passport-size Photo', type: 'file', required: true },
                    { id: 'aadhar_card', label: 'Aadhaar Card',         type: 'file', required: true },
                    { id: 'ration_card', label: 'Ration Card',           type: 'file' },
                    { id: 'other_doc',   label: 'Salary Slip / IT Return', type: 'file' },
                ]
            }
        ]
    },

    // ---- Water Connection ----
    4: {
        title: 'Water Connection Request',
        sections: [
            {
                title: 'Applicant Details',
                fields: [
                    { id: 'full_name',   label: 'Full Name',        type: 'text', required: true },
                    { id: 'father_name', label: "Father's Name",    type: 'text' },
                    { id: 'mobile',      label: 'Mobile Number',    type: 'tel', required: true },
                    { id: 'aadhar_number', label: 'Aadhaar Number', type: 'text', required: true },
                    { id: 'address',     label: 'Property Address', type: 'textarea', required: true },
                    { id: 'village',     label: 'Village / Ward',   type: 'text', required: true },
                    { id: 'district',    label: 'District',         type: 'text' },
                    { id: 'pincode',     label: 'PIN Code',         type: 'text' },
                ]
            },
            {
                title: 'Request Details',
                fields: [
                    { id: 'request_details', label: 'Describe your water issue / request', type: 'textarea', required: true },
                ]
            },
            {
                title: 'Documents',
                fields: [
                    { id: 'aadhar_card', label: 'Aadhaar Card',        type: 'file', required: true },
                    { id: 'other_doc',   label: 'Property Documents',  type: 'file' },
                ]
            }
        ]
    },

    // ---- Electricity Request ----
    5: {
        title: 'Electricity Connection Request',
        sections: [
            {
                title: 'Applicant Details',
                fields: [
                    { id: 'full_name',   label: 'Full Name',        type: 'text', required: true },
                    { id: 'father_name', label: "Father's Name",    type: 'text' },
                    { id: 'mobile',      label: 'Mobile Number',    type: 'tel', required: true },
                    { id: 'aadhar_number', label: 'Aadhaar Number', type: 'text', required: true },
                    { id: 'address',     label: 'Property Address', type: 'textarea', required: true },
                    { id: 'village',     label: 'Village / Ward',   type: 'text', required: true },
                    { id: 'district',    label: 'District',         type: 'text' },
                    { id: 'pincode',     label: 'PIN Code',         type: 'text' },
                ]
            },
            {
                title: 'Request Details',
                fields: [
                    { id: 'request_details', label: 'Describe your electricity issue / new connection request', 
                      type: 'textarea', required: true },
                ]
            },
            {
                title: 'Documents',
                fields: [
                    { id: 'aadhar_card', label: 'Aadhaar Card',      type: 'file', required: true },
                    { id: 'other_doc',   label: 'Property Documents', type: 'file' },
                ]
            }
        ]
    },

    // ---- Residence Certificate ----
    6: {
        title: 'Residence Certificate Application',
        sections: [
            {
                title: 'Personal Details',
                fields: [
                    { id: 'full_name',    label: 'Full Name',        type: 'text', required: true },
                    { id: 'father_name',  label: "Father's Name",    type: 'text', required: true },
                    { id: 'mother_name',  label: "Mother's Name",    type: 'text' },
                    { id: 'date_of_birth',label: 'Date of Birth',    type: 'date' },
                    { id: 'gender',       label: 'Gender',           type: 'select',
                      options: ['Male','Female','Other'] },
                    { id: 'mobile',       label: 'Mobile Number',    type: 'tel', required: true },
                    { id: 'aadhar_number',label: 'Aadhaar Number',   type: 'text', required: true },
                ]
            },
            {
                title: 'Residence Address',
                fields: [
                    { id: 'address', label: 'Full Address', type: 'textarea', required: true },
                    { id: 'village', label: 'Village / Ward', type: 'text', required: true },
                    { id: 'district',label: 'District', type: 'text', required: true },
                    { id: 'state',   label: 'State', type: 'text', required: true },
                    { id: 'pincode', label: 'PIN Code', type: 'text' },
                ]
            },
            {
                title: 'Documents',
                fields: [
                    { id: 'photo',       label: 'Passport Photo',  type: 'file', required: true },
                    { id: 'aadhar_card', label: 'Aadhaar Card',     type: 'file', required: true },
                    { id: 'ration_card', label: 'Ration Card',       type: 'file' },
                    { id: 'other_doc',   label: 'Utility Bill / Proof of Address', type: 'file' },
                ]
            }
        ]
    },

    // ---- Caste Certificate ----
    7: {
        title: 'Caste Certificate Application',
        sections: [
            {
                title: 'Personal Details',
                fields: [
                    { id: 'full_name',    label: 'Full Name',      type: 'text', required: true },
                    { id: 'father_name',  label: "Father's Name",  type: 'text', required: true },
                    { id: 'mother_name',  label: "Mother's Name",  type: 'text' },
                    { id: 'date_of_birth',label: 'Date of Birth',  type: 'date', required: true },
                    { id: 'gender',       label: 'Gender',         type: 'select',
                      options: ['Male','Female','Other'], required: true },
                    { id: 'mobile',       label: 'Mobile Number',  type: 'tel', required: true },
                    { id: 'aadhar_number',label: 'Aadhaar Number', type: 'text', required: true },
                    { id: 'occupation',   label: 'Caste Category', type: 'text',
                      placeholder: 'e.g. SC / ST / OBC', required: true },
                ]
            },
            {
                title: 'Address',
                fields: [
                    { id: 'address', label: 'Full Address', type: 'textarea', required: true },
                    { id: 'village', label: 'Village / Ward', type: 'text', required: true },
                    { id: 'district',label: 'District', type: 'text', required: true },
                    { id: 'state',   label: 'State', type: 'text', required: true },
                    { id: 'pincode', label: 'PIN Code', type: 'text' },
                ]
            },
            {
                title: 'Documents',
                fields: [
                    { id: 'photo',       label: 'Passport Photo',              type: 'file', required: true },
                    { id: 'aadhar_card', label: 'Aadhaar Card',                 type: 'file', required: true },
                    { id: 'ration_card', label: 'Ration Card',                  type: 'file' },
                    { id: 'other_doc',   label: "Father's Caste Certificate",   type: 'file', required: true },
                ]
            }
        ]
    }
};

// -------------------------------------------------------
// Build dynamic service application form HTML
// -------------------------------------------------------
function buildServiceForm(serviceId) {
    const config = SERVICE_FORMS[serviceId];
    if (!config) return '<p>Form not available for this service.</p>';

    let html = '';
    config.sections.forEach(section => {
        html += `<div class="form-section-title">${section.title}</div>`;
        html += '<div class="form-row">';
        let colCount = 0;

        section.fields.forEach((field, idx) => {
            const req = field.required ? '<span class="required">*</span>' : '';
            const placeholder = field.placeholder || '';

            if (field.type === 'textarea') {
                // Textareas span full width
                if (colCount % 2 !== 0) { html += '</div><div class="form-row">'; }
                html += `</div>
                <div class="form-group">
                    <label for="f_${field.id}">${field.label} ${req}</label>
                    <textarea class="form-control" id="f_${field.id}" name="${field.id}"
                        ${field.required ? 'required' : ''}
                        placeholder="${placeholder || 'Enter details...'}"></textarea>
                </div>
                <div class="form-row">`;
                colCount = 0;
                return;
            }

            html += `<div class="form-group">
                <label for="f_${field.id}">${field.label} ${req}</label>`;

            if (field.type === 'select') {
                html += `<select class="form-control" id="f_${field.id}" name="${field.id}" ${field.required ? 'required' : ''}>
                    <option value="">-- Select --</option>
                    ${field.options.map(o => `<option>${o}</option>`).join('')}
                </select>`;
            } else if (field.type === 'file') {
                html += `<input type="file" class="form-control file-input"
                    id="f_${field.id}" name="${field.id}"
                    accept="image/*,.pdf" ${field.required ? 'required' : ''}>`;
            } else {
                html += `<input type="${field.type}" class="form-control"
                    id="f_${field.id}" name="${field.id}"
                    placeholder="${placeholder}"
                    ${field.required ? 'required' : ''}>`;
            }

            html += `</div>`;
            colCount++;

            // close and reopen form-row every 2 items
            if (colCount % 2 === 0 && idx < section.fields.length - 1) {
                html += '</div><div class="form-row">';
            }
        });
        html += '</div>'; // close last form-row
    });
    return html;
}
