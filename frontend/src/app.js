import Home from './components/Home.js';
import Login from './components/Login.js';
import Register from './components/Register.js';

import AdminDashboard from './components/admin/Dashboard.js';
import CompanyDashboard from './components/company/Dashboard.js';
import StudentDashboard from './components/student/Dashboard.js';

const { createApp, ref, computed, watch } = Vue;
const { createRouter, createWebHistory } = VueRouter;

// Centralized state management for Auth
const authState = {
    token: ref(localStorage.getItem('token')),
    user: ref(JSON.parse(localStorage.getItem('user') || '{}')),
    setAuth(token, user) {
        this.token.value = token;
        this.user.value = user;
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    },
    clearAuth() {
        this.token.value = null;
        this.user.value = {};
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        delete axios.defaults.headers.common['Authorization'];
    }
};

// Initial Axios setup
if (authState.token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authState.token.value}`;
}

// Global Axios Interceptor for 401
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response && (error.response.status === 401 || error.response.status === 403)) {
            authState.clearAuth();
            window.location.hash = '/login'; // Fallback redirect
        }
        return Promise.reject(error);
    }
);

const routes = [
    { path: '/', component: Home, name: 'home' },
    { path: '/login', component: Login, name: 'login' },
    { path: '/register', component: Register, name: 'register' },
    { path: '/admin', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
    { path: '/company', component: CompanyDashboard, meta: { requiresAuth: true, role: 'company' } },
    { path: '/student', component: StudentDashboard, meta: { requiresAuth: true, role: 'student' } }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

router.beforeEach((to, from, next) => {
    const token = authState.token.value;
    const user = authState.user.value;

    if (to.meta.requiresAuth && !token) {
        return next({ name: 'login' });
    }
    if (to.meta.role && user.role !== to.meta.role) {
        return next({ name: 'home' });
    }
    next();
});

const app = createApp({
    setup() {
        const toastMessage = ref('');
        const isLoggedIn = computed(() => !!authState.token.value);
        const userName = computed(() => {
            const name = authState.user.value?.name;
            return name && name.trim() ? name : 'User';
        });

        const logout = () => {
            authState.clearAuth();
            router.push({ name: 'login' });
        };

        const showToast = (msg) => {
            toastMessage.value = msg;
            const toastEl = document.getElementById('crhToast');
            if (toastEl) {
                const bToast = bootstrap.Toast.getOrCreateInstance(toastEl);
                bToast.show();
            }
        };

        // EXPOSE TO GLOBALS for easy access
        window.showToast = showToast;
        // Make authState globally accessible to other components if needed
        window.authState = authState;

        return {
            isLoggedIn,
            userName,
            toastMessage,
            logout
        }
    }
});

app.use(router);
app.mount('#app');
