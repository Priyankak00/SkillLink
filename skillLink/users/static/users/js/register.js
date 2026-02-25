// Show/Hide fields based on role selection
const roleRadios = document.querySelectorAll('input[name="role"]');
const titleField = document.getElementById('titleField');
const categoryField = document.getElementById('categoryField');
const skillsField = document.getElementById('skillsField');
const submitBtnText = document.getElementById('submitBtnText');

roleRadios.forEach(radio => {
    radio.addEventListener('change', function() {
        if (this.value === 'freelancer') {
            titleField.style.display = 'block';
            categoryField.style.display = 'block';
            skillsField.style.display = 'block';
            document.getElementById('title').required = true;
            document.getElementById('category').required = true;
            submitBtnText.textContent = 'Create Account & Start Earning';
        } else {
            titleField.style.display = 'block';
            categoryField.style.display = 'none';
            skillsField.style.display = 'none';
            document.getElementById('title').required = false;
            document.getElementById('category').required = false;
            submitBtnText.textContent = 'Create Account & Start Hiring';
        }
    });
});

// Password strength checker
const passwordInput = document.getElementById('password');
const passwordStrengthBar = document.getElementById('passwordStrengthBar');

passwordInput.addEventListener('input', function() {
    const password = this.value;
    let strength = 0;

    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;

    const strengthClasses = ['', 'strength-weak', 'strength-fair', 'strength-good', 'strength-strong'];
    const widths = ['0%', '25%', '50%', '75%', '100%'];

    passwordStrengthBar.style.width = widths[strength];
    passwordStrengthBar.className = 'password-strength-bar ' + strengthClasses[strength];
});

// Profile picture preview
const fileInput = document.getElementById('profilePicture');
const previewImage = document.getElementById('previewImage');

fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            previewImage.src = event.target.result;
            previewImage.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

// Drag and drop
const fileUploadBtn = document.querySelector('.file-upload-btn');
fileUploadBtn.addEventListener('dragover', function(e) {
    e.preventDefault();
    this.style.background = 'rgba(102, 126, 234, 0.2)';
});

fileUploadBtn.addEventListener('dragleave', function() {
    this.style.background = 'rgba(102, 126, 234, 0.05)';
});

fileUploadBtn.addEventListener('drop', function(e) {
    e.preventDefault();
    this.style.background = 'rgba(102, 126, 234, 0.05)';
    if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    }
});

// Form submission
const registrationForm = document.getElementById('registrationForm');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const spinner = document.getElementById('spinner');

registrationForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Validate passwords match
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        showError('Passwords do not match!');
        return;
    }

    if (password.length < 8) {
        showError('Password must be at least 8 characters long!');
        return;
    }

    // Show loading spinner
    spinner.style.display = 'block';

    // Collect form data
    const formData = new FormData(this);
    const selectedSkills = Array.from(document.querySelectorAll('input[name="skills"]:checked'))
        .map(skill => skill.value);
    
    // Get selected role
    const selectedRole = document.querySelector('input[name="role"]:checked');
    if (!selectedRole) {
        showError('Please select whether you are a Freelancer or Client!');
        spinner.style.display = 'none';
        return;
    }

    const data = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        email: formData.get('email'),
        password: formData.get('password'),
        title: formData.get('title'),
        category: formData.get('category'),
        bio: formData.get('bio'),
        skills: selectedSkills,
        role: selectedRole.value
    };

    try {
        // Get CSRF token from form
        const csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const response = await fetch('/api/users/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
            },
            body: JSON.stringify(data)
        });

        spinner.style.display = 'none';

        if (response.ok) {
            const result = await response.json();
            showSuccess('Account created successfully! Redirecting to login...');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            const error = await response.json();
            showError(error.detail || 'Registration failed. Please try again.');
        }
    } catch (error) {
        spinner.style.display = 'none';
        showError('An error occurred. Please try again.');
        console.error('Error:', error);
    }
});

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}
