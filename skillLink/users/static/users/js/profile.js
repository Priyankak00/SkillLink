let currentUserData = null;
let currentAvatarFile = null;
let skillsList = []; // Local copy of skills being edited

function getCsrfToken() {
    // Try to get from hidden input first
    let token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // If not found, try to get from cookies
    if (!token) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                token = cookie.substring('csrftoken='.length);
                break;
            }
        }
    }
    
    return token || '';
}

async function getJsonSafely(response) {
    const text = await response.text();
    if (!text) {
        return null;
    }
    try {
        return JSON.parse(text);
    } catch (error) {
        return { detail: text };
    }
}

// Load user profile data on page load
async function loadUserProfile() {
    try {
        const response = await fetch('/users/profile/', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            currentUserData = await getJsonSafely(response);
            if (currentUserData) {
                populateProfile(currentUserData);
            }
        } else if (response.status === 403) {
            window.location.href = '/users/login/';
        } else {
            showError('Failed to load profile data');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showError('An error occurred while loading your profile');
    }
}

// Populate profile with user data
function populateProfile(userData) {
    const fullName = `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || userData.username;
    
    document.getElementById('profileName').textContent = fullName;
    document.getElementById('profileTitle').textContent = userData.title || 'No title set';
    document.getElementById('aboutText').textContent = userData.bio || 'No bio provided';
    const contactEmail = document.getElementById('contactEmail');
    if (contactEmail) {
        contactEmail.textContent = userData.email || 'No email set';
    }
    
    // Populate avatar if exists
    const avatarUrl = userData.profile_picture_url || userData.profile_picture;
    if (avatarUrl) {
        document.getElementById('avatarPreview').src = avatarUrl;
    }

    // Populate skills section
    if (userData.skills && userData.skills.length > 0) {
        const skillsContainer = document.getElementById('skillsContainer');
        if (skillsContainer) {
            skillsContainer.innerHTML = userData.skills.map(skill => 
                `<div class="skill-tag">${skill}<span class="skill-remove" onclick="removeSkill(this)">✕</span></div>`
            ).join('');
        }
    }
}

// Tab switching
function switchTab(e, tabName) {
    e.preventDefault();
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
    e.target.closest('.tab-btn').classList.add('active');
}

function prefillEditForm() {
    if (!currentUserData) {
        return;
    }
    const fullName = `${currentUserData.first_name || ''} ${currentUserData.last_name || ''}`.trim();
    const editName = document.getElementById('editName');
    const editTitle = document.getElementById('editTitle');
    const editAbout = document.getElementById('editAbout');
    const editBio = document.getElementById('editBio');
    const editEmail = document.getElementById('editEmail');

    if (editName) {
        editName.value = fullName;
    }
    if (editTitle) {
        editTitle.value = currentUserData.title || '';
    }
    if (editAbout) {
        editAbout.value = currentUserData.bio || '';
    }
    if (editBio) {
        editBio.value = currentUserData.bio || '';
    }
    if (editEmail) {
        editEmail.value = currentUserData.email || '';
    }
}

// Modal Functions
function editSection(section) {
    const modal = document.getElementById('editModal');
    document.getElementById('modalTitle').textContent = `Edit ${section.charAt(0).toUpperCase() + section.slice(1)}`;
    prefillEditForm();
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('editModal').classList.remove('active');
}

// Remove Skill
function removeSkill(element) {
    element.parentElement.remove();
}

// Upload profile picture immediately when selected
async function uploadProfilePicture(file) {
    const formData = new FormData();
    formData.append('profile_picture', file);
    
    try {
        const csrf_token = getCsrfToken();
        
        const headers = {
            'X-CSRFToken': csrf_token || ''
        };
        
        const response = await fetch('/users/profile/', {
            method: 'PATCH',
            headers: headers,
            body: formData,
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const updatedData = await response.json();
            if (updatedData) {
                currentUserData = updatedData;
                populateProfile(updatedData);
            }
            currentAvatarFile = null;
            showSuccess('Profile picture updated successfully!');
        } else {
            let error = null;
            try {
                error = await response.json();
            } catch (e) {
                error = { detail: 'Upload failed' };
            }
            showError((error && error.detail) || 'Failed to upload profile picture');
        }
    } catch (error) {
        showError('An error occurred while uploading. Please try again.');
    }
}

// Avatar Upload
function bindAvatarUpload() {
    const avatarUpload = document.getElementById('avatarUpload');
    if (!avatarUpload) {
        return;
    }
    avatarUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showError('Please select a valid image file');
                return;
            }
            
            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                showError('File size must be less than 5MB');
                return;
            }
            
            currentAvatarFile = file;
            const reader = new FileReader();
            reader.onload = function(event) {
                const avatarPreview = document.getElementById('avatarPreview');
                if (avatarPreview && avatarPreview.tagName === 'IMG') {
                    avatarPreview.src = event.target.result;
                }
            };
            reader.readAsDataURL(file);
            
            // Automatically save the profile picture
            uploadProfilePicture(file);
        }
    });
}

// Form Submission
function bindEditForm() {
    const editForm = document.getElementById('editForm');
    if (!editForm) {
        console.error('Edit form not found');
        return;
    }
    editForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted');

        const editName = document.getElementById('editName');
        const fullName = editName ? editName.value || '' : '';
        const nameParts = fullName.trim().split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';

        const formData = new FormData();
        formData.append('first_name', firstName);
        formData.append('last_name', lastName);
        const editTitle = document.getElementById('editTitle');
        formData.append('title', editTitle ? editTitle.value || '' : '');
        const editBio = document.getElementById('editBio');
        const editAbout = document.getElementById('editAbout');
        const bioValue = (editBio && editBio.value) ? editBio.value : (editAbout ? editAbout.value || '' : '');
        formData.append('bio', bioValue);
        const editEmail = document.getElementById('editEmail');
        formData.append('email', editEmail ? editEmail.value || '' : '');
        if (currentAvatarFile) {
            formData.append('profile_picture', currentAvatarFile);
        }

        console.log('FormData:', {
            first_name: firstName,
            last_name: lastName,
            title: editTitle?.value,
            bio: bioValue,
            email: editEmail?.value
        });

        try {
            const csrf_token = getCsrfToken();
            console.log('CSRF Token:', csrf_token ? 'Present' : 'Missing');
            
            const response = await fetch('/users/profile/', {
                method: 'PATCH',
                headers: {
                    ...(csrf_token && { 'X-CSRFToken': csrf_token }),
                    'Accept': 'application/json'
                },
                body: formData,
                credentials: 'same-origin'
            });

            console.log('Response status:', response.status);

            if (response.ok) {
                const updatedData = await getJsonSafely(response);
                console.log('Updated data:', updatedData);
                if (updatedData) {
                    currentUserData = updatedData;
                    populateProfile(updatedData);
                }
                currentAvatarFile = null;
                showSuccess('Profile updated successfully!');
                setTimeout(() => {
                    closeModal();
                }, 1500);
            } else {
                const error = await getJsonSafely(response);
                console.log('Error response:', error);
                showError((error && error.detail) || `Failed to update profile. Status: ${response.status}`);
            }
        } catch (error) {
            console.error('Catch error:', error);
            showError('An error occurred. Please try again.');
        }
    });
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    if (!errorDiv) {
        return;
    }
    errorDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + message;
    errorDiv.style.display = 'block';
    if (successDiv) {
        successDiv.style.display = 'none';
    }
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    const errorDiv = document.getElementById('errorMessage');
    if (!successDiv) {
        return;
    }
    successDiv.innerHTML = '<i class="fas fa-check-circle"></i> ' + message;
    successDiv.style.display = 'block';
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}

// Close modal on background click
function bindModalCloseOnBackdrop() {
    const editModal = document.getElementById('editModal');
    if (!editModal) {
        return;
    }
    editModal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

function bindEditButton() {
    const editProfileBtn = document.getElementById('editProfileBtn');
    const modalTitle = document.getElementById('modalTitle');
    const editModal = document.getElementById('editModal');
    if (!editProfileBtn || !modalTitle || !editModal) {
        return;
    }
    editProfileBtn.addEventListener('click', () => {
        modalTitle.textContent = 'Edit Profile';
        prefillEditForm();
        editModal.classList.add('active');
    });
}

function bindProfileEvents() {
    bindEditButton();
    bindEditForm();
    bindAvatarUpload();
    bindModalCloseOnBackdrop();
    bindSkillsModal();
}

// ===== SKILLS MANAGEMENT =====
function openSkillsModal() {
    const skillsModal = document.getElementById('skillsModal');
    if (!skillsModal) {
        return;
    }
    // Initialize skills list from current user data
    skillsList = currentUserData && currentUserData.skills ? [...currentUserData.skills] : [];
    renderSkillsList();
    skillsModal.classList.add('active');
}

function closeSkillsModal() {
    const skillsModal = document.getElementById('skillsModal');
    if (skillsModal) {
        skillsModal.classList.remove('active');
    }
    skillsList = [];
}

function renderSkillsList() {
    const container = document.getElementById('skillsListContainer');
    if (!container) {
        return;
    }
    
    if (skillsList.length === 0) {
        container.innerHTML = '<p style="color: #999; font-style: italic; width: 100%;">No skills added yet</p>';
        return;
    }
    
    container.innerHTML = skillsList.map((skill, index) => 
        `<div class="skill-tag" style="display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 20px; font-size: 0.9rem;">
            ${skill}
            <span style="cursor: pointer; font-weight: bold; font-size: 1.1rem;" onclick="removeSkillFromModal(${index})">✕</span>
        </div>`
    ).join('');
}

function removeSkillFromModal(index) {
    skillsList.splice(index, 1);
    renderSkillsList();
}

function bindSkillsModal() {
    const addSkillBtnModal = document.getElementById('addSkillBtnModal');
    const newSkillInput = document.getElementById('newSkillInput');
    const skillsModal = document.getElementById('skillsModal');
    
    if (!addSkillBtnModal || !newSkillInput) {
        return;
    }
    
    addSkillBtnModal.addEventListener('click', () => {
        const skillName = newSkillInput.value.trim();
        if (!skillName) {
            showSkillsError('Please enter a skill name');
            return;
        }
        
        if (skillsList.includes(skillName)) {
            showSkillsError('This skill is already added');
            return;
        }
        
        skillsList.push(skillName);
        newSkillInput.value = '';
        renderSkillsList();
        clearSkillsMessages();
    });
    
    // Also allow pressing Enter to add skill
    newSkillInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addSkillBtnModal.click();
        }
    });
    
    // Close modal on backdrop click
    if (skillsModal) {
        skillsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeSkillsModal();
            }
        });
    }
}

async function saveSkills() {
    try {
        const csrf_token = getCsrfToken();
        
        const response = await fetch('/users/profile/', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                skills: skillsList
            }),
            credentials: 'same-origin'
        });

        if (response.ok) {
            const updatedData = await getJsonSafely(response);
            if (updatedData) {
                currentUserData = updatedData;
                populateProfile(updatedData);
            }
            showSkillsSuccess('Skills updated successfully!');
            setTimeout(() => {
                closeSkillsModal();
            }, 1500);
        } else {
            const error = await getJsonSafely(response);
            showSkillsError((error && error.detail) || 'Failed to update skills.');
        }
    } catch (error) {
        console.error('Error saving skills:', error);
        showSkillsError('An error occurred. Please try again.');
    }
}

function showSkillsError(message) {
    const errorDiv = document.getElementById('skillsErrorMessage');
    const successDiv = document.getElementById('skillsSuccessMessage');
    if (!errorDiv) {
        return;
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    if (successDiv) {
        successDiv.style.display = 'none';
    }
}

function showSkillsSuccess(message) {
    const successDiv = document.getElementById('skillsSuccessMessage');
    const errorDiv = document.getElementById('skillsErrorMessage');
    if (!successDiv) {
        return;
    }
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function clearSkillsMessages() {
    const errorDiv = document.getElementById('skillsErrorMessage');
    const successDiv = document.getElementById('skillsSuccessMessage');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
    if (successDiv) {
        successDiv.style.display = 'none';
    }
}

// Load profile on page load
window.addEventListener('load', () => {
    bindProfileEvents();
    loadUserProfile();
});
