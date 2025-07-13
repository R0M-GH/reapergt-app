import axios from 'axios';

const API_BASE_URL = 'https://i968t9scwl.execute-api.us-east-1.amazonaws.com/Prod';

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

// Send test notification
async function sendTestNotification() {
    const res = await api.post('/test-notification');
    return res.data;
}

// Send test SMS
async function sendTestSms() {
    const res = await api.post('/test-sms');
    return res.data;
}

// Manually refresh all CRNs for real-time updates
async function refreshCRNs() {
    const res = await api.post('/refresh');
    return res.data;
}

// Register phone number for SMS notifications
async function registerPhoneNumber(phoneNumber) {
    const res = await api.post('/register-phone', {
        phone_number: phoneNumber
    });
    return res.data;
}

// Get user profile data
async function getUserProfile() {
    const res = await api.get('/user/profile');
    return res.data;
}

// Update user profile
async function updateUserProfile(profileData) {
    const res = await api.put('/user/profile', profileData);
    return res.data;
}

// Remove phone number from notifications
async function removePhoneNumber() {
    const res = await api.post('/remove-phone');
    return res.data;
}

export const crnService = {
    getCRNs,
    addCRN,
    removeCRN,
    refreshCRNs,
    registerPushSubscription,
    registerPhoneNumber,
    getUserProfile,
    updateUserProfile,
    removePhoneNumber,
    sendTestNotification,
    sendTestSms
}; 