import axios from 'axios';
import { API_BASE_URL, getAuthHeaders } from './api-config';

export const getToken = async (username: string, password: string) => {
    try {
        const formData = new URLSearchParams();
        formData.append('grant_type', 'password');
        formData.append('username', username);
        formData.append('password', password);

        const res = await axios.post(`${API_BASE_URL}/auth/token`, formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        if (res.status === 200) {
            return res.data;
        }

    } catch (err) {
        if (err.response) {
            if (err.response.status === 422) {
                const validationErrors = err.response.data?.detail || [];
                return { 
                    error: "Validation failed", 
                    validationErrors: validationErrors,
                    status: 422
                };
            }

            const errorMessage = err.response.data?.detail || err.response.data?.message || "Invalid credentials";
            return { error: errorMessage };
            
        } else if (err.request) {
            return { error: "No response from server. Check your connection." };
        } else {
            return { error: "An unexpected error occurred." };
        }
    }
};


export const getMe = async () => {
    try {
        const res = await axios.get(`${API_BASE_URL}/auth/me`, {
            headers: getAuthHeaders(),
        });

        if (res.status === 200) {
            return res.data;
        }

    } catch (err) {
        if (err.response) {
            const errorMessage = err.response.data?.detail || err.response.data?.message || "Invalid credentials";
            return { error: errorMessage };
        } else if (err.request) {
            return { error: "No response from server. Check your connection." };
        } else {
            return { error: "An unexpected error occurred." };
        }
    }
}; 