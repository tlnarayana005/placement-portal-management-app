export default {
    data() {
        return {
            role: 'student', name: '', email: '', password: '', error: null, success: null,
            studentData: { branch: '', cgpa: '', graduation_year: '' },
            companyData: { website: '', hr_contact: '', industry: '' },
            isSubmitting: false,
            currentStep: 1
        }
    },
    computed: {
        stepLabel() {
            return this.currentStep === 1 ? 'Primary Details' : (this.role === 'student' ? 'Academic Records' : 'Corporate Identity');
        }
    },
    methods: {
        proceedToStep2() {
            if (!this.name || !this.email || !this.password) {
                this.error = 'Please complete all required fields.';
                window.showToast?.(this.error);
                return;
            }
            this.error = null;
            this.currentStep = 2;
        },
        async register() {
            this.isSubmitting = true;
            this.error = null;
            try {
                const payload = { role: this.role, name: this.name, email: this.email, password: this.password };
                if (this.role === 'student') Object.assign(payload, this.studentData);
                if (this.role === 'company') Object.assign(payload, this.companyData);

                const res = await axios.post('/api/auth/register', payload);
                this.success = res.data.message;
                window.showToast?.('Registration successful!');
            } catch (err) {
                this.error = err.response?.data?.error || 'Registration failed. Please attempt again.';
                this.success = null;
            } finally {
                this.isSubmitting = false;
            }
        }
    },
    template: `
        <div class="row justify-content-center animate-in">
            <div class="col-lg-7 col-md-9">
                <div class="card-crh mt-4 mb-5 p-0 overflow-hidden">
                    <div class="text-center py-4 bg-light border-bottom">
                        <div class="bg-primary bg-opacity-10 text-primary rounded-circle d-inline-flex p-3 mb-3">
                            <i class="bi bi-person-plus-fill fs-2"></i>
                        </div>
                        <h4 class="fw-800 tracking-tight text-crh-text-main mb-0">Create Professional Account</h4>
                        <p class="text-muted small">Join the IIT Madras official recruitment hub</p>
                    </div>

                    <!-- Modern Progress -->
                    <div class="px-5 pt-4 d-flex align-items-center gap-2 mb-2" v-if="!success">
                        <div class="rounded-pill px-3 py-1 text-white small fw-700 shadow-sm"
                             :class="currentStep >= 1 ? 'bg-primary' : 'bg-light text-muted border'">1. Identity</div>
                        <i class="bi bi-chevron-right text-muted mx-1"></i>
                        <div class="rounded-pill px-3 py-1 small fw-700"
                             :class="currentStep >= 2 ? 'bg-primary text-white shadow-sm' : 'bg-light text-muted border'">2. Profile</div>
                    </div>

                    <div class="p-5 pt-3">
                        <div v-if="error" class="alert alert-danger border-0 small py-2 mb-4 d-flex align-items-center gap-2">
                            <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
                        </div>
                        <div v-if="success" class="text-center py-4">
                            <i class="bi bi-check-circle-fill text-success fs-1"></i>
                            <h4 class="mt-3 fw-800">{{ success }}</h4>
                            <p class="text-muted mb-4">Your account is ready. Proceed to sign in.</p>
                            <router-link to="/login" class="btn btn-primary-crh px-5">Continue to Login</router-link>
                        </div>

                        <form @submit.prevent="register" v-if="!success">
                            <div v-if="currentStep === 1">
                                <div class="mb-4">
                                    <label class="form-label small fw-700 text-muted text-uppercase tracking-wider mb-2">Member Type</label>
                                    <div class="d-flex gap-2">
                                        <button type="button" class="btn flex-fill py-2 fw-600 br-10 shadow-sm"
                                                :class="role==='student' ? 'btn-primary-crh' : 'btn-outline-crh'"
                                                @click="role='student'">
                                            <i class="bi bi-mortarboard-fill me-1"></i>Student
                                        </button>
                                        <button type="button" class="btn flex-fill py-2 fw-600 br-10 shadow-sm"
                                                :class="role==='company' ? 'btn-primary-crh' : 'btn-outline-crh'"
                                                @click="role='company'">
                                            <i class="bi bi-building-fill me-1"></i>Company
                                        </button>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">
                                        {{ role === 'company' ? 'Organization' : 'Full Name' }}
                                    </label>
                                    <input type="text" class="form-control" v-model="name" required>
                                </div>
                                <div class="row g-3 mb-4">
                                    <div class="col-md-6">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Email</label>
                                        <input type="email" class="form-control" v-model="email" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Password</label>
                                        <input type="password" class="form-control" v-model="password" required>
                                    </div>
                                </div>
                                <button type="button" class="btn btn-primary-crh w-100 py-2 br-10" @click="proceedToStep2">
                                    Next Step <i class="bi bi-arrow-right-short ms-1 fs-5"></i>
                                </button>
                            </div>

                            <div v-if="currentStep === 2" class="fade-in">
                                <div v-if="role === 'student'" class="row g-3 mb-4">
                                    <div class="col-md-4">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Branch</label>
                                        <input type="text" class="form-control" v-model="studentData.branch" placeholder="e.g. Mechanical" required>
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">CGPA</label>
                                        <input type="number" step="0.01" class="form-control" v-model="studentData.cgpa" required>
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Batch Year</label>
                                        <input type="number" class="form-control" v-model="studentData.graduation_year" placeholder="2026" required>
                                    </div>
                                </div>

                                <div v-if="role === 'company'" class="row g-3 mb-4">
                                    <div class="col-md-5">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Corporate Site</label>
                                        <input type="url" class="form-control" v-model="companyData.website" placeholder="https://tech.corp" required>
                                    </div>
                                    <div class="col-md-7">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">HR Focal Point</label>
                                        <input type="text" class="form-control" v-model="companyData.hr_contact" placeholder="Name or Email" required>
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Industry Vertical</label>
                                        <input type="text" class="form-control" v-model="companyData.industry" placeholder="e.g. AI / Fintech / Mechanical Engineering" required>
                                    </div>
                                </div>

                                <div class="d-flex gap-3 mt-2">
                                    <button type="button" class="btn btn-outline-crh flex-fill py-2" @click="currentStep=1">
                                        Back
                                    </button>
                                    <button type="submit" class="btn btn-primary-crh flex-fill py-2 shadow-sm" :disabled="isSubmitting">
                                        {{ isSubmitting ? 'Finalizing...' : 'Complete Account Entry' }}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `
};
