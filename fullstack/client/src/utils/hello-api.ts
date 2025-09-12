import axios from 'axios';
import { API_BASE_URL, getAuthHeaders } from './api-config';

export const hello_public = async () => {
    try {
        const res = await axios.post(`${API_BASE_URL}/hello`);

        if (res.status === 200) {
            return res.data;
        }

    } catch (err) {
        if (err.response) {
            return { error: err.response.data || "Invalid credentials" };
        } else if (err.request) {
            return { error: "No response from server. Check your connection." };
        } else {
            return { error: "An unexpected error occurred." };
        }
    }
}; 


export const hello_protected = async () => {
    try {
        const res = await axios.get(`${API_BASE_URL}/hello/protected`, {
            headers: getAuthHeaders(),
        });

        if (res.status === 200) {
            return res.data;
        }

    } catch (err) {
        if (err.response) {
            return { error: err.response.data || "Invalid credentials" };
        } else if (err.request) {
            return { error: "No response from server. Check your connection." };
        } else {
            return { error: "An unexpected error occurred." };
        }
    }
};