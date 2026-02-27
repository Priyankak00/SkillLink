// Form submission
const loginForm = document.getElementById('loginForm');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const spinner = document.getElementById('spinner');
const rememberMe = document.getElementById('rememberMe');

// Load saved email if available
window.addEventListener('load', function() {
    const savedEmail = localStorage.getItem('savedEmail');
    if (savedEmail) {
        document.getElementById('email').value = savedEmail;
        rememberMe.checked = true;
    }
});

loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Show loading spinner
    spinner.style.display = 'block';
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';

    const data = {
        email: email,
        password: password
    };

    try {
        // Get CSRF token from form
        const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrf_token = csrfElement ? csrfElement.value : '';
        
        if (!csrf_token) {
            throw new Error('CSRF token not found');
        }

        const response = await fetch('/users/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        });

        spinner.style.display = 'none';

        if (response.ok) {
            const result = await response.json();
            
            // Save email if remember me is checked
            if (rememberMe.checked) {
                localStorage.setItem('savedEmail', email);
            } else {
                localStorage.removeItem('savedEmail');
            }

            showSuccess('Login successful! Redirecting to dashboard...');
            
            // Store token if provided
            if (result.token) {
                localStorage.setItem('authToken', result.token);
            }

            // Redirect to appropriate dashboard based on role
            const userRole = result.user?.role || 'client';
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
            const error = await response.json();
            showError(error.detail || error.error || 'Login failed. Please check your credentials.');
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
