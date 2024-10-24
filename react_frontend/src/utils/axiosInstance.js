import axios from 'axios';
import Cookies from 'js-cookie';

const axiosInstance = axios.create({
    baseURL: 'https://llama.cnu.ac.kr/api/',
    headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', 
    },
});

axiosInstance.interceptors.request.use((config) => {
    const token = Cookies.get('csrftoken');
    if (token) {
        config.headers['X-CSRFToken'] = token;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

export const fetchCsrfToken = async () => {
    try {
        await axiosInstance.get('get_csrf_token');
        const csrfToken = Cookies.get('csrftoken');
        if (csrfToken) {
            localStorage.setItem('csrfToken', csrfToken);
            console.error('csrfToken set');
        }
    } catch (error) {
        console.error('Error fetching CSRF token:', error);
    }
};

export default axiosInstance;