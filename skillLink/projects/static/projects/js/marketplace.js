/**
 * Projects Marketplace Frontend
 * Handles browsing available projects, submitting bids, and managing proposals
 */

// ============ CONFIGURATION ============
const API_BASE_URL = '/projects/api';
const PROJECTS_PER_PAGE = 12;

// ============ UTILITY FUNCTIONS ============

/**
 * Get CSRF token from DOM
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Get authentication token from localStorage
 */
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastHtml = `
        <div class="toast show alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'}" 
             role="alert" style="min-width: 300px;">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        const toasts = toastContainer.querySelectorAll('.toast');
        if (toasts.length > 0) {
            const bsToast = new bootstrap.Toast(toasts[toasts.length - 1]);
            bsToast.hide();
        }
    }, 5000);
}

// ============ API FUNCTIONS ============

/**
 * Fetch available projects with optional filters
 */
async function fetchAvailableProjects(filters = {}) {
    try {
        const queryParams = new URLSearchParams();
        
        if (filters.search) queryParams.append('search', filters.search);
        if (filters.status) queryParams.append('status', filters.status);
        if (filters.minBudget) queryParams.append('min_budget', filters.minBudget);
        if (filters.maxBudget) queryParams.append('max_budget', filters.maxBudget);
        if (filters.ordering) queryParams.append('ordering', filters.ordering);
        if (filters.page) queryParams.append('page', filters.page);

        const url = `${API_BASE_URL}/available/?${queryParams.toString()}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching projects:', error);
        throw error;
    }
}

/**
 * Fetch single project details
 */
async function fetchProjectDetail(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/${projectId}/`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching project details:', error);
        throw error;
    }
}

/**
 * Submit a bid on a project
 */
async function submitBid(projectId, bidData) {
    try {
        const token = getAuthToken();
        if (!token) {
            showToast('Please log in to submit a bid', 'error');
            return null;
        }

        const response = await fetch(`${API_BASE_URL}/${projectId}/bid/create/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(bidData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Error submitting bid');
        }

        return data;
    } catch (error) {
        console.error('Error submitting bid:', error);
        throw error;
    }
}

/**
 * Fetch user's bids
 */
async function fetchMyBids() {
    try {
        const token = getAuthToken();
        if (!token) return null;

        const response = await fetch(`${API_BASE_URL}/my-bids/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching user bids:', error);
        return null;
    }
}

/**
 * Fetch bids on a project (for project owner)
 */
async function fetchProjectBids(projectId) {
    try {
        const token = getAuthToken();
        if (!token) return null;

        const response = await fetch(`${API_BASE_URL}/${projectId}/bids/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching project bids:', error);
        return null;
    }
}

/**
 * Accept a bid
 */
async function acceptBid(bidId) {
    try {
        const token = getAuthToken();
        if (!token) throw new Error('Not authenticated');

        const response = await fetch(`${API_BASE_URL}/bids/${bidId}/accept/`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Error accepting bid');
        return await response.json();
    } catch (error) {
        console.error('Error accepting bid:', error);
        throw error;
    }
}

/**
 * Reject a bid
 */
async function rejectBid(bidId) {
    try {
        const token = getAuthToken();
        if (!token) throw new Error('Not authenticated');

        const response = await fetch(`${API_BASE_URL}/bids/${bidId}/reject/`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Error rejecting bid');
        return await response.json();
    } catch (error) {
        console.error('Error rejecting bid:', error);
        throw error;
    }
}

// ============ UI RENDERING FUNCTIONS ============

/**
 * Render project cards
 */
function renderProjectCards(projects, container) {
    if (!projects || projects.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-center text-muted">No projects found</p></div>';
        return;
    }

    const cardsHtml = projects.map(project => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100 shadow-sm project-card" data-project-id="${project.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title">${project.title}</h5>
                        <span class="badge bg-success">${project.status}</span>
                    </div>
                    
                    <p class="card-text text-muted small">${project.description.substring(0, 100)}...</p>
                    
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="h5 text-primary">${formatCurrency(project.budget)}</span>
                        <span class="badge bg-light text-dark">${project.bid_count} bid${project.bid_count !== 1 ? 's' : ''}</span>
                    </div>
                    
                    <div class="mb-3 small">
                        <div class="text-muted">Client: <strong>${project.client_name}</strong></div>
                        <div class="text-muted">Posted: ${formatDate(project.created_at)}</div>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary btn-sm view-project-btn" data-project-id="${project.id}">
                            View Details
                        </button>
                        ${!project.user_has_bid ? `
                            <button class="btn btn-success btn-sm submit-bid-btn" data-project-id="${project.id}">
                                Submit Proposal
                            </button>
                        ` : `
                            <div class="alert alert-info alert-sm mb-0 py-2">
                                <small>You've already bid on this project</small>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = cardsHtml;

    // Add event listeners
    container.querySelectorAll('.view-project-btn').forEach(btn => {
        btn.addEventListener('click', handleViewProject);
    });

    container.querySelectorAll('.submit-bid-btn').forEach(btn => {
        btn.addEventListener('click', handleSubmitBid);
    });
}

/**
 * Render project detail modal
 */
function renderProjectDetailModal(project) {
    const modal = document.getElementById('projectDetailModal');
    if (!modal) return;

    const modalBody = modal.querySelector('.modal-body');
    modalBody.innerHTML = `
        <div class="project-detail">
            <div class="mb-3">
                <h4 class="mb-2">${project.title}</h4>
                <div class="mb-2">
                    <span class="badge bg-success">${project.status}</span>
                    <span class="badge bg-light text-dark">${project.bid_count} bid${project.bid_count !== 1 ? 's' : ''}</span>
                </div>
            </div>
            
            <div class="mb-3">
                <h6 class="text-muted">Budget</h6>
                <h5 class="text-primary">${formatCurrency(project.budget)}</h5>
            </div>
            
            <div class="mb-3">
                <h6 class="text-muted">Description</h6>
                <p>${project.description}</p>
            </div>
            
            <div class="mb-3">
                <h6 class="text-muted">Client</h6>
                <div class="d-flex align-items-center">
                    <div>
                        <strong>${project.client_name}</strong>
                        <div class="small text-muted">${project.client_details.email}</div>
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <h6 class="text-muted">Posted</h6>
                <p>${formatDate(project.created_at)}</p>
            </div>
            
            ${!project.user_has_bid && project.status === 'open' ? `
                <div class="alert alert-info">
                    <small>Ready to submit your proposal? Click the button below to get started.</small>
                </div>
            ` : ''}
        </div>
    `;

    // Update modal footer buttons
    const modalFooter = modal.querySelector('.modal-footer');
    modalFooter.innerHTML = `
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        ${!project.user_has_bid && project.status === 'open' ? `
            <button type="button" class="btn btn-success" id="submitBidFromDetail" data-project-id="${project.id}">
                Submit Proposal
            </button>
        ` : `
            <div class="alert alert-info mb-0">
                <small>${project.user_has_bid ? 'You have already submitted a proposal' : 'This project is not accepting bids'}</small>
            </div>
        `}
    `;

    // Add event listener
    const submitBtn = document.getElementById('submitBidFromDetail');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            handleSubmitBid({
                target: { dataset: { projectId: project.id } }
            });
            // Close the detail modal and show bid form
            const detailModal = bootstrap.Modal.getInstance(modal);
            detailModal.hide();
        });
    }

    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Render bid form modal
 */
function renderBidFormModal(projectId) {
    const modal = document.getElementById('bidFormModal');
    if (!modal) return;

    const modalBody = modal.querySelector('.modal-body');
    modalBody.innerHTML = `
        <form id="bidForm">
            <div class="mb-3">
                <label for="bidAmount" class="form-label">Your Bid Amount *</label>
                <div class="input-group">
                    <span class="input-group-text">INR</span>
                    <input type="number" class="form-control" id="bidAmount" 
                           placeholder="e.g., 15000" min="1" step="0.01" required>
                </div>
                <small class="text-muted">Enter your proposed budget for this project</small>
            </div>
            
            <div class="mb-3">
                <label for="deliveryDays" class="form-label">Delivery Time (Days) *</label>
                <input type="number" class="form-control" id="deliveryDays" 
                       placeholder="e.g., 30" min="1" required>
                <small class="text-muted">How many days will you take to complete this project?</small>
            </div>
            
            <div class="mb-3">
                <label for="proposalText" class="form-label">Your Proposal *</label>
                <textarea class="form-control" id="proposalText" rows="5" 
                          placeholder="Describe your experience, approach, and why you're the best fit for this project..." 
                          required></textarea>
                <small class="text-muted">Write a compelling proposal about yourself and your experience</small>
            </div>
        </form>
    `;

    const modalFooter = modal.querySelector('.modal-footer');
    modalFooter.innerHTML = `
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-success" id="submitBidBtn">Submit Proposal</button>
    `;

    const submitBtn = document.getElementById('submitBidBtn');
    submitBtn.addEventListener('click', function() {
        handleBidFormSubmit(projectId, modal);
    });

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// ============ EVENT HANDLERS ============

/**
 * Handle view project click
 */
async function handleViewProject(event) {
    const projectId = event.target.dataset.projectId;
    try {
        const project = await fetchProjectDetail(projectId);
        renderProjectDetailModal(project);
    } catch (error) {
        showToast('Error loading project details', 'error');
    }
}

/**
 * Handle submit bid click
 */
function handleSubmitBid(event) {
    const projectId = event.target.dataset.projectId;
    const token = getAuthToken();
    
    if (!token) {
        showToast('Please log in to submit a bid', 'error');
        window.location.href = '/users/login/';
        return;
    }
    
    renderBidFormModal(projectId);
}

/**
 * Handle bid form submission
 */
async function handleBidFormSubmit(projectId, modal) {
    const bidAmount = document.getElementById('bidAmount').value;
    const deliveryDays = document.getElementById('deliveryDays').value;
    const proposal = document.getElementById('proposalText').value;

    if (!bidAmount || !deliveryDays || !proposal) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    try {
        const bid = await submitBid(projectId, {
            amount: parseFloat(bidAmount),
            delivery_days: parseInt(deliveryDays),
            proposal: proposal
        });

        if (bid) {
            showToast('Proposal submitted successfully!', 'success');
            const bsModal = bootstrap.Modal.getInstance(modal);
            bsModal.hide();
            
            // Reload projects to update UI
            loadProjects();
        }
    } catch (error) {
        showToast(error.message || 'Error submitting proposal', 'error');
    }
}

/**
 * Handle search form submission
 */
function handleSearch(event) {
    event.preventDefault();
    const searchQuery = document.getElementById('projectSearch')?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const minBudget = document.getElementById('minBudget')?.value || '';
    const maxBudget = document.getElementById('maxBudget')?.value || '';

    loadProjects({
        search: searchQuery,
        status: statusFilter,
        minBudget: minBudget,
        maxBudget: maxBudget
    });
}

// ============ MAIN LOAD FUNCTION ============

/**
 * Load and display projects
 */
async function loadProjects(filters = {}) {
    try {
        const projectsContainer = document.getElementById('projectsContainer');
        if (!projectsContainer) return;

        // Show loading state
        projectsContainer.innerHTML = '<div class="col-12 text-center"><div class="spinner-border" role="status"></div></div>';

        const data = await fetchAvailableProjects(filters);
        renderProjectCards(data.results || data, projectsContainer);
    } catch (error) {
        console.error('Error loading projects:', error);
        document.getElementById('projectsContainer').innerHTML = 
            '<div class="col-12"><div class="alert alert-danger">Error loading projects. Please try again later.</div></div>';
    }
}

/**
 * Initialize marketplace page
 */
function initializeMarketplace() {
    // Load projects on page load
    loadProjects();

    // Setup search form
    const searchForm = document.getElementById('projectSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }

    // Setup clear filters button
    const clearBtn = document.getElementById('clearFiltersBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            document.getElementById('projectSearch').value = '';
            document.getElementById('statusFilter').value = '';
            document.getElementById('minBudget').value = '';
            document.getElementById('maxBudget').value = '';
            loadProjects();
        });
    }
}

// ============ INITIALIZE ON DOM READY ============
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the marketplace page
    if (document.getElementById('projectsContainer')) {
        initializeMarketplace();
    }
});
