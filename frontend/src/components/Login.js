export default {
    data() {
        return { email: '', password: '', error: null, showPass: false, isLoading: false }
    },
    methods: {
        async login() {
            this.isLoading = true;
            this.error = null;
            try {
                const res = await axios.post('/api/auth/login', {
                    email: this.email,
                    password: this.password
                });
                
                // Use centralized authState
                window.authState.setAuth(res.data.token, res.data.user);

                const roleRouteMap = { admin: '/admin', company: '/company', student: '/student' };
                this.$router.push(roleRouteMap[res.data.user.role] || '/');
            } catch (err) {
                this.error = err.response?.data?.error || 'Authentication failed. Please verify your credentials.';
            } finally {
                this.isLoading = false;
            }
        }
    },
    template: `
        <div class="row justify-content-center animate-in">
            <div class="col-lg-5 col-md-7">
                <div class="card-crh p-4 mt-5">
                    <div class="text-center mb-4">
                        <div class="bg-primary bg-opacity-10 text-primary rounded-circle d-inline-flex p-3 mb-3">
                            <i class="bi bi-person-lock fs-2"></i>
                        </div>
                        <h3 class="fw-800 tracking-tight text-crh-text-main">Sign In</h3>
                        <p class="text-muted small">Access your IIT Madras Recruitment Portal</p>
                    </div>

                    <div v-if="error" class="alert alert-danger border-0 small py-2 d-flex align-items-center gap-2">
                        <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
                    </div>

                    <form @submit.prevent="login">
                        <div class="mb-3">
                            <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Email Address</label>
                            <input type="email" class="form-control py-2" v-model="email" placeholder="name@iitm.ac.in" required>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Password</label>
                                <a href="#" class="small text-primary text-decoration-none fw-600">Forgot?</a>
                            </div>
                            <div class="position-relative">
                                <input :type="showPass ? 'text' : 'password'" class="form-control py-2 pe-5" v-model="password" required>
                                <button type="button" class="btn btn-link position-absolute end-0 top-50 translate-middle-y text-muted"
                                        @click="showPass = !showPass" style="text-decoration:none;">
                                    <i :class="showPass ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
                                </button>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary-crh w-100 py-2 mt-2" :disabled="isLoading">
                            <span v-if="isLoading"><i class="bi bi-arrow-repeat spin-slow me-1"></i>Signing in...</span>
                            <span v-else>Sign In</span>
                        </button>
                    </form>
                    
                    <div class="text-center mt-4 pt-3 border-top">
                        <p class="small text-muted mb-0">
                            New member? <router-link to="/register" class="text-primary fw-700 text-decoration-none">Create Account</router-link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `
};
