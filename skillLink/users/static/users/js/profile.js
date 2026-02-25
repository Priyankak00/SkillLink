let currentUserId = null;
let currentUserData = null;

// Load user profile data on page load
async function loadUserProfile() {
    try {
        const response = await fetch('/api/users/profile/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            currentUserData = await response.json();
            currentUserId = currentUserData.id;
            populateProfile(currentUserData);
        } else if (response.status === 403) {
            window.location.href = '/api/users/login/';
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
    
    // Populate avatar if exists
    if (userData.profile_picture) {
        document.getElementById('avatarPreview').src = userData.profile_picture;
    }

    // Populate skills section
    if (userData.skills && userData.skills.length > 0) {
        const skillsContainer = document.querySelector('.skills-list');
        if (skillsContainer) {
            skillsContainer.innerHTML = userData.skills.map(skill => 
                `<span class="skill-badge">${skill}</span>`
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

// Edit Profile Button
document.getElementById('editProfileBtn').addEventListener('click', () => {
    const modal = document.getElementById('editModal');
    document.getElementById('modalTitle').textContent = 'Edit Profile';
    
    // Pre-fill form with current data
    if (currentUserData) {
        document.getElementById('editName').value = `${currentUserData.first_name || ''} ${currentUserData.last_name || ''}`.trim();
        document.getElementById('editTitle').value = currentUserData.title || '';
        document.getElementById('editAbout').value = currentUserData.bio || '';
        document.getElementById('editEmail').value = currentUserData.email || '';
    }
    
    modal.classList.add('active');
});

// Modal Functions
function editSection(section) {
    const modal = document.getElementById('editModal');
    document.getElementById('modalTitle').textContent = `Edit ${section.charAt(0).toUpperCase() + section.slice(1)}`;
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('editModal').classList.remove('active');
}

// Remove Skill
function removeSkill(element) {
    element.parentElement.remove();
}

// Avatar Upload
document.getElementById('avatarUpload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const avatarPreview = document.getElementById('avatarPreview');
            if (avatarPreview.tagName === 'IMG') {
                avatarPreview.src = event.target.result;
            }
        };
        reader.readAsDataURL(file);
    }
});

// Form Submission
document.getElementById('editForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const fullName = document.getElementById('editName').value || '';
    const nameParts = fullName.trim().split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || '';

    const data = {
        first_name: firstName,
        last_name: lastName,
        title: document.getElementById('editTitle').value,
        bio: document.getElementById('editAbout').value,
        email: document.getElementById('editEmail').value,
    };

    try {
        const csrf_token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        const response = await fetch(`/api/users/${currentUserId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                ...(csrf_token && { 'X-CSRFToken': csrf_token })
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const updatedData = await response.json();
            currentUserData = updatedData;
            populateProfile(updatedData);
            showSuccess('Profile updated successfully!');
            setTimeout(() => {
                closeModal();
            }, 1500);
        } else {
            const error = await response.json();
            showError(error.detail || 'Failed to update profile.');
        }
    } catch (error) {
        showError('An error occurred. Please try again.');
        console.error('Error:', error);
    }
});

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    document.getElementById('successMessage').style.display = 'none';
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
}

// Close modal on background click
document.getElementById('editModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Load profile on page load
window.addEventListener('load', loadUserProfile);
