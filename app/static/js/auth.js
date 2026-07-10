// Token Management Module
const AuthManager = {
    // Get token from localStorage
    getToken() {
        return localStorage.getItem('token');
    },

    // Set token in localStorage
    setToken(token) {
        localStorage.setItem('token', token);
    },

    decodeBase64Url(value) {
        if (!value) return null;

        const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
        const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
        const binary = atob(padded);
        const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
        return new TextDecoder().decode(bytes);
    },

    decodeTokenPayload(token) {
        if (!token) return null;

        const parts = token.split('.');
        if (parts.length !== 3) return null;

        try {
            return JSON.parse(this.decodeBase64Url(parts[1]));
        } catch (error) {
            return null;
        }
    },

    // Remove token
    removeToken() {
        localStorage.removeItem('token');
    },

    // Check if token is valid
    isTokenValid() {
        const token = this.getToken();
        if (!token) return false;

        const payload = this.decodeTokenPayload(token);
        if (!payload || typeof payload.exp !== 'number') return false;

        return payload.exp * 1000 > Date.now();
    },

    // Check if user is authenticated
    isAuthenticated() {
        return this.isTokenValid();
    },

    // Redirect to login if not authenticated
    requireAuth() {
        if (!this.isAuthenticated()) {
            this.removeToken();
            window.location.href = '/login';
            return false;
        }
        return true;
    },

    // Add token to fetch headers
    addAuthHeader(headers = {}) {
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    // Make authenticated fetch request
    async fetchWithAuth(url, options = {}) {
        const headers = this.addAuthHeader(options.headers || {});
        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'same-origin',
            cache: 'no-store'
        });
        
        // If 401, token might be expired
        if (response.status === 401) {
            this.removeToken();
            window.location.href = '/login';
        }
        // If backend reissued a token (normalized `sub`), pick it up and store it
        const reissued = response.headers.get('X-Reissued-Token');
        if (reissued) {
            this.setToken(reissued);
        }
        
        return response;
    },

    // Logout: remove token, unregister service workers (optional), redirect to login
    logout() {
        this.removeToken();
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(regs => regs.forEach(r => r.unregister())).catch(()=>{});
        }
        window.location.href = '/login';
    }
};

// NOTE: Do NOT attach tokens to navigation links or use sessionStorage/meta hacks.
// Frontend should store token in localStorage and use `AuthManager.fetchWithAuth` for API calls.

// Attach logout nav if present
document.addEventListener('DOMContentLoaded', () => {
    const logoutNav = document.getElementById('logout-nav');
    if (logoutNav) {
        logoutNav.addEventListener('click', (e) => {
            e.preventDefault();
            AuthManager.logout();
        });
    }
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            AuthManager.logout();
        });
    }
});
