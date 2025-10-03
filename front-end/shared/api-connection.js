/**
 * Frontend-Backend Connection Script for Evergrow360
 * 
 * This script provides integration between the static frontend
 * and the Flask backend API for a seamless user experience.
 */

class EvergrowAPI {
    constructor() {
        this.baseURL = this.getAPIBaseURL();
        this.token = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        
        // Set up automatic token refresh
        this.setupTokenRefresh();
    }
    
    getAPIBaseURL() {
        // Determine API base URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:5001';
        } else {
            return 'https://api.evergrow360.com'; // Production API URL
        }
    }
    
    // Authentication methods
    async register(userData) {
        try {
            const response = await this.makeRequest('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify(userData)
            });
            
            if (response.access_token) {
                this.setTokens(response.access_token, response.refresh_token);
            }
            
            return response;
        } catch (error) {
            console.error('Registration failed:', error);
            throw error;
        }
    }
    
    async login(credentials) {
        try {
            const response = await this.makeRequest('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials)
            });
            
            if (response.access_token) {
                this.setTokens(response.access_token, response.refresh_token);
            }
            
            return response;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }
    
    async logout() {
        try {
            await this.makeRequest('/api/auth/logout', {
                method: 'POST'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearTokens();
            window.location.href = '/app/auth/login.html';
        }
    }
    
    // Assessment methods
    async submitAssessment(assessmentData) {
        return this.makeRequest('/api/assessment/submit', {
            method: 'POST',
            body: JSON.stringify(assessmentData)
        });
    }
    
    async getAssessmentResults(assessmentId) {
        return this.makeRequest(`/api/assessment/results/${assessmentId}`);
    }
    
    // Coaching methods
    async generateCoachingPlan(planData) {
        return this.makeRequest('/api/coaching/plan/generate', {
            method: 'POST',
            body: JSON.stringify(planData)
        });
    }
    
    async getCoachingPlans() {
        return this.makeRequest('/api/coaching/plans');
    }
    
    async getCoachingRecommendations() {
        return this.makeRequest('/api/coaching/recommendations');
    }
    
    // Marketplace methods
    async getCoaches(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        return this.makeRequest(`/api/marketplace/coaches?${queryParams}`);
    }
    
    async getCourses(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        return this.makeRequest(`/api/marketplace/courses?${queryParams}`);
    }
    
    // User profile methods
    async getUserProfile() {
        return this.makeRequest('/api/user/profile');
    }
    
    async updateUserProfile(profileData) {
        return this.makeRequest('/api/user/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }
    
    // Utility methods
    setTokens(accessToken, refreshToken) {
        this.token = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }
    
    clearTokens() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }
    
    async refreshAccessToken() {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.refreshToken}`
                },
                mode: 'cors',
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access_token, this.refreshToken);
                return data.access_token;
            } else {
                throw new Error('Token refresh failed');
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            this.clearTokens();
            window.location.href = '/app/auth/login.html';
            throw error;
        }
    }
    
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        // Add authentication token if available
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        try {
            const response = await fetch(url, {
                ...options,
                headers,
                mode: 'cors',
                credentials: 'include'
            });
            
            // Handle token expiration
            if (response.status === 401 && this.refreshToken) {
                await this.refreshAccessToken();
                headers['Authorization'] = `Bearer ${this.token}`;
                
                // Retry the original request
                const retryResponse = await fetch(url, {
                    ...options,
                    headers
                });
                
                return this.handleResponse(retryResponse);
            }
            
            return this.handleResponse(response);
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || data.error || 'Request failed');
            }
            
            return data;
        } else {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        }
    }
    
    setupTokenRefresh() {
        // Automatically refresh token 5 minutes before expiration
        if (this.token) {
            // Decode JWT to get expiration time (simplified - in production use a proper JWT library)
            try {
                const payload = JSON.parse(atob(this.token.split('.')[1]));
                const expirationTime = payload.exp * 1000; // Convert to milliseconds
                const refreshTime = expirationTime - (5 * 60 * 1000); // 5 minutes before expiration
                const now = Date.now();
                
                if (refreshTime > now) {
                    setTimeout(() => {
                        this.refreshAccessToken().catch(console.error);
                    }, refreshTime - now);
                }
            } catch (error) {
                console.error('Token parsing error:', error);
            }
        }
    }
    
    // Helper method to check if user is authenticated
    isAuthenticated() {
        return !!this.token;
    }
    
    // Helper method to get current user ID from token
    getCurrentUserId() {
        if (!this.token) return null;
        
        try {
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            return payload.sub;
        } catch (error) {
            console.error('Token parsing error:', error);
            return null;
        }
    }
}

// Global API instance
window.evergrowAPI = new EvergrowAPI();

// Frontend integration functions
window.EvergrowFrontend = {
    // Initialize authentication check
    checkAuth() {
        const api = window.evergrowAPI;
        
        if (!api.isAuthenticated()) {
            // Redirect to login if not authenticated and not on auth pages
            const currentPath = window.location.pathname;
            if (!currentPath.includes('/auth/')) {
                window.location.href = '/app/auth/login.html';
                return false;
            }
        }
        
        return true;
    },
    
    // Handle form submissions
    async handleFormSubmit(formElement, apiMethod, successCallback) {
        const formData = new FormData(formElement);
        const data = Object.fromEntries(formData.entries());
        
        try {
            // Show loading state
            this.showLoading(formElement);
            
            const response = await apiMethod(data);
            
            if (successCallback) {
                successCallback(response);
            }
            
            return response;
        } catch (error) {
            this.showError(error.message);
            throw error;
        } finally {
            this.hideLoading(formElement);
        }
    },
    
    // UI helper methods
    showLoading(element) {
        element.classList.add('loading');
        const submitButton = element.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Loading...';
        }
    },
    
    hideLoading(element) {
        element.classList.remove('loading');
        const submitButton = element.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = submitButton.getAttribute('data-original-text') || 'Submit';
        }
    },
    
    showError(message) {
        // Create or update error message element
        let errorElement = document.querySelector('.error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            document.body.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    },
    
    showSuccess(message) {
        // Create or update success message element
        let successElement = document.querySelector('.success-message');
        if (!successElement) {
            successElement = document.createElement('div');
            successElement.className = 'success-message';
            document.body.appendChild(successElement);
        }
        
        successElement.textContent = message;
        successElement.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successElement.style.display = 'none';
        }, 3000);
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication for protected pages
    window.EvergrowFrontend.checkAuth();
    
    // Store original button text for loading states
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.setAttribute('data-original-text', button.textContent);
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EvergrowAPI, EvergrowFrontend };
}