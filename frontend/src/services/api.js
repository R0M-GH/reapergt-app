import axios from 'axios';

const API_BASE_URL = 'https://xv3or5zxu6.execute-api.us-east-1.amazonaws.com/Prod';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 60000,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('oidc.user:https://us-east-1_ZErx06uN7.auth.us-east-1.amazoncognito.com:ghq72js41cdk53vcren6v436e');
    if (token) {
        try {
            const userData = JSON.parse(token);
            if (userData.access_token) {
                config.headers.Authorization = `Bearer ${userData.access_token}`;
            }
        } catch (error) {
            console.error('Error parsing auth token:', error);
        }
    }
    return config;
});

// Get all CRNs for the user
async function getCRNs() {
    const res = await api.get('/crns');
    // The backend now returns { crns: [{ crn, course_id, course_name, course_section, isOpen }, ...] }
    return res.data.crns || [];
}

// Add a CRN (returns new CRN info)
async function addCRN(crn) {
    const res = await api.post('/crns', { crn });
    // The backend should now return the full CRN object with isOpen status
    // If it doesn't, we'll need to fetch the updated CRN list
    return {
        crn: res.data.crn,
        course_id: res.data.course_info.course_id,
        course_name: res.data.course_info.course_name,
        course_section: res.data.course_info.course_section,
        isOpen: res.data.isOpen || false // Use backend value if available
    };
}

// Remove a CRN
async function removeCRN(crn) {
    await api.delete(`/crns/${crn}`);
}

export const crnService = {
    getCRNs,
    addCRN,
    removeCRN,
}; 