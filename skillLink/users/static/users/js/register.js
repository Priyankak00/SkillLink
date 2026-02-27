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

// Form submission
const registrationForm = document.getElementById('registrationForm');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const spinner = document.getElementById('spinner');

registrationForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    clearFieldErrors();
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';

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

    // Get selected role
    const selectedRole = document.querySelector('input[name="role"]:checked');
    if (!selectedRole) {
        showError('Please select whether you are a Freelancer or Client!');
        spinner.style.display = 'none';
        return;
    }

    // Collect form data
    const formData = new FormData(this);
    
    // Add selected skills as array
    const selectedSkills = Array.from(document.querySelectorAll('input[name="skills"]:checked'))
        .map(skill => skill.value);
    
    // Remove existing skills checkboxes from formData
    formData.delete('skills');
    
    // Add skills as JSON array
    formData.append('skills', JSON.stringify(selectedSkills));

    // Debug: Log form data
    console.log('Form data being sent:');
    for (let [key, value] of formData.entries()) {
        console.log(`  ${key}: ${value}`);
    }

    try {
        // Get CSRF token from form
        const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrf_token = csrfElement ? csrfElement.value : '';
        
        if (!csrf_token) {
            throw new Error('CSRF token not found');
        }
        
        // Use FormData to support file upload
        const response = await fetch('/users/register/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf_token,
            },
            credentials: 'same-origin',
            body: formData
        });

        spinner.style.display = 'none';

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (response.ok) {
            const result = await response.json();
            showSuccess('Account created successfully! Redirecting to your dashboard...');
            
            // Determine dashboard URL based on user role
            const userRole = result.user?.role || formData.get('role');
            let dashboardURL = '/users/dashboard/';
            
            if (userRole === 'freelancer') {
                dashboardURL = '/users/dashboard/freelancer/';
            } else if (userRole === 'client') {
                dashboardURL = '/users/dashboard/client/';
            }
            
            setTimeout(() => {
                window.location.href = dashboardURL;
            }, 1500);
        } else {
            // Clone response to read it multiple times if needed
            const responseClone = response.clone();
            let error;
            try {
                error = await response.json();
                console.log('Registration error:', error);
            } catch (e) {
                console.error('Failed to parse error response as JSON:', e);
                try {
                    const text = await responseClone.text();
                    console.log('Raw response:', text);
                } catch (textError) {
                    console.error('Failed to read response text:', textError);
                }
                showError('Server error. Please check the console and try again.');
                return;
            }
            
            clearFieldErrors();

            // Show field-specific errors
            if (error && typeof error === 'object') {
                showFieldErrors(error);
            }

            // Extract main error message
            let errorMsg = '';
            
            if (error.email) {
                errorMsg = Array.isArray(error.email) ? error.email[0] : error.email;
            } else if (error.password) {
                errorMsg = Array.isArray(error.password) ? error.password[0] : error.password;
            } else if (error.confirm_password) {
                errorMsg = Array.isArray(error.confirm_password) ? error.confirm_password[0] : error.confirm_password;
            } else if (error.first_name) {
                errorMsg = Array.isArray(error.first_name) ? error.first_name[0] : error.first_name;
            } else if (error.last_name) {
                errorMsg = Array.isArray(error.last_name) ? error.last_name[0] : error.last_name;
            } else if (error.bio) {
                errorMsg = Array.isArray(error.bio) ? error.bio[0] : error.bio;
            } else if (error.role) {
                errorMsg = Array.isArray(error.role) ? error.role[0] : error.role;
            } else if (error.detail) {
                errorMsg = typeof error.detail === 'string' ? error.detail : 'Registration failed. Please review your inputs.';
            } else if (error.non_field_errors) {
                errorMsg = Array.isArray(error.non_field_errors) ? error.non_field_errors[0] : error.non_field_errors;
            } else {
                // Get first error from any field
                const firstKey = Object.keys(error)[0];
                if (firstKey) {
                    const firstError = error[firstKey];
                    errorMsg = Array.isArray(firstError) ? firstError[0] : firstError;
                } else {
                    errorMsg = 'Registration failed. Please try again.';
                }
            }
            
            showError(errorMsg);
        }
    } catch (error) {
        spinner.style.display = 'none';
        showError('An error occurred. Please try again.');
        console.error('Error:', error);
    }
});

function clearFieldErrors() {
    document.querySelectorAll('.field-error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
}

function showFieldErrors(errors) {
    if (!errors || typeof errors !== 'object') {
        return;
    }

    Object.entries(errors).forEach(([field, messages]) => {
        const target = document.querySelector(`.field-error[data-field="${field}"]`);
        if (!target) {
            return;
        }
        const text = Array.isArray(messages) ? messages.join(' ') : String(messages);
        target.textContent = text;
        target.style.display = 'block';
    });
}

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
