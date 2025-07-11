import axios from 'axios';

const API_BASE_URL = 'https://pxqw7ufbci.execute-api.us-east-1.amazonaws.com/Prod';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 60000,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('google_access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Get all CRNs for the user
async function getCRNs() {
    const res = await api.get('/crns');
    // The backend returns the CRNs array directly
    return res.data || [];
}

// Add a CRN (returns new CRN info)
async function addCRN(crn) {
    const res = await api.post('/crns', { crn });
    // The backend returns the CRN object directly
    return res.data;
}

// Remove a CRN
async function removeCRN(crn) {
    await api.delete(`/crns/${crn}`);
}

// Register push notification subscription
async function registerPushSubscription(subscription) {
    const res = await api.post('/register-push', {
        push_subscription: subscription
    });
    return res.data;
}

export const crnService = {
    getCRNs,
    addCRN,
    removeCRN,
    registerPushSubscription,
}; 