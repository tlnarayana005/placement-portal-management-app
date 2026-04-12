export default {
    data() {
        return {
            drives: [],
            applications: [],
            profile: null,
            error: null,
            searchTerm: '',
            editMode: false,
            editData: { name: '', branch: '', cgpa: '', graduation_year: '', projects: [] },
            resumeFile: null,
            isLoading: true
        }
    },
    async mounted() {
        await this.loadData();
        await this.loadProfile();
    },
    computed: {
        filteredDrives() {
            if (!this.searchTerm) return this.drives;
            const t = this.searchTerm.toLowerCase();
            return this.drives.filter(d =>
                d.job_title.toLowerCase().includes(t) ||
                d.company_name.toLowerCase().includes(t) ||
                (d.eligibility_branch && d.eligibility_branch.toLowerCase().includes(t))
            );
        }
    },
    methods: {
        async loadData() {
            this.isLoading = true;
            try {
                const [drivesRes, appsRes] = await Promise.all([
                    axios.get('/api/student/drives'),
                    axios.get('/api/student/applications')
                ]);
                this.drives = drivesRes.data;
                this.applications = appsRes.data;
            } catch (err) {
                this.error = 'Failed to synchronize recruitment data.';
            } finally {
                this.isLoading = false;
            }
        },
        async loadProfile() {
            try {
                const res = await axios.get('/api/student/profile');
                this.profile = res.data;
                this.editData = { 
                    name: res.data.name, 
                    branch: res.data.branch, 
                    cgpa: res.data.cgpa, 
                    graduation_year: res.data.graduation_year,
                    projects: [...(res.data.projects || [])]
                };
            } catch (err) { /* ignore */ }
        },
        hasApplied(driveId) {
            return this.applications.some(a => a.drive_id === driveId);
        },
        async apply(driveId) {
            try {
                await axios.post('/api/student/apply', { drive_id: driveId });
                window.showToast?.('Application submitted successfully.');
                await this.loadData();
            } catch (err) {
                window.showToast?.(err.response?.data?.error || 'Exceeded application limits or ineligible.');
            }
        },
        async saveProfile() {
            try {
                await axios.put('/api/student/profile', this.editData);
                this.editMode = false;
                window.showToast?.('Academic profile updated.');
                await this.loadProfile();
            } catch (err) {
                window.showToast?.('Profile update failed.');
            }
        },
        async uploadResume() {
            if (!this.resumeFile) return;
            const formData = new FormData();
            formData.append('resume', this.resumeFile);
            try {
                const res = await axios.post('/api/student/resume', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                window.showToast?.(res.data.message);
                this.resumeFile = null;
                await this.loadProfile();
            } catch (err) {
                window.showToast?.('Document upload failed.');
            }
        },
        onFileSelect(event) {
            this.resumeFile = event.target.files[0];
        },
        addProject() {
            this.editData.projects.push({ name: '', link: '' });
        },
        removeProject(idx) {
            this.editData.projects.splice(idx, 1);
        },
        async exportCSV() {
            try {
                const res = await axios.post('/api/student/export');
                window.showToast?.(res.data.message);
            } catch (err) {
                window.showToast?.('Export failed. Please try again.');
            }
        }
    },
    template: `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="fw-800 tracking-tight mb-1">Student Hub</h2>
                    <p class="text-muted small mb-0">Track applications and manage your professional profile</p>
                </div>
                <button class="btn btn-primary-crh btn-sm shadow-sm" @click="editMode = !editMode">
                    <i class="bi" :class="editMode ? 'bi-x-lg' : 'bi-pencil-square'"></i> 
                    {{ editMode ? 'Cancel Editing' : 'Edit Profile' }}
                </button>
            </div>

            <!-- Profile Overview Card -->
            <div v-if="profile" class="card-crh p-4 mb-5 border-0 shadow-sm" style="background: white;">
                <div v-if="!editMode" class="row align-items-center g-4">
                    <div class="col-md-auto d-flex align-items-center gap-3">
                        <div class="bg-primary bg-opacity-10 text-primary rounded-pill d-flex align-items-center justify-content-center" style="width:50px; height:50px; font-weight:700;">
                            {{ profile.name.charAt(0) }}
                        </div>
                        <div>
                            <h5 class="fw-800 m-0">{{ profile.name }}</h5>
                            <p class="text-muted small m-0">{{ profile.branch }} &bull; Batch of {{ profile.graduation_year }}</p>
                        </div>
                    </div>
                    <div class="col-md-2 text-md-center">
                        <div class="small fw-700 text-muted text-uppercase tracking-wider mb-1" style="font-size:0.65rem;">Academic CGPA</div>
                        <div class="fw-800 text-primary fs-5">{{ profile.cgpa }}</div>
                    </div>
                    <div class="col-md-3">
                        <div class="small fw-700 text-muted text-uppercase tracking-wider mb-1" style="font-size:0.65rem;">Professional Document</div>
                        <a v-if="profile.resume_url" :href="profile.resume_url" target="_blank" class="text-primary fw-600 text-decoration-none small">
                            <i class="bi bi-file-earmark-pdf me-1"></i> View Registered Resume
                        </a>
                        <span v-else class="text-muted small italic">No resume on file</span>
                    </div>
                    <div class="col">
                        <div class="small fw-700 text-muted text-uppercase tracking-wider mb-2" style="font-size:0.65rem;">Project Links</div>
                        <div class="d-flex flex-wrap gap-2">
                            <a v-for="p in profile.projects" :key="p.name" :href="p.link" target="_blank" class="badge bg-light text-dark border fw-600 text-decoration-none">
                                <i class="bi bi-link-45deg"></i> {{ p.name }}
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Edit Profile UI -->
                <div v-else class="fade-in">
                    <form @submit.prevent="saveProfile">
                        <div class="row g-3 mb-4">
                            <div class="col-md-4">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Full Name</label>
                                <input class="form-control" v-model="editData.name" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Branch</label>
                                <input class="form-control" v-model="editData.branch" required>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">CGPA</label>
                                <input class="form-control" type="number" step="0.01" v-model="editData.cgpa" required>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Year</label>
                                <input class="form-control" type="number" v-model="editData.graduation_year" required>
                            </div>
                        </div>

                        <div class="mb-4">
                            <div class="d-flex justify-content-between mb-2">
                                <label class="small fw-700 text-muted text-uppercase tracking-wider">Professional Projects</label>
                                <button type="button" @click="addProject" class="btn btn-link p-0 text-primary small fw-600 text-decoration-none">+ Add Project</button>
                            </div>
                            <div v-for="(p, idx) in editData.projects" :key="idx" class="row g-2 mb-2 animate-in">
                                <div class="col-md-5"><input class="form-control form-control-sm" placeholder="Project Name" v-model="p.name"></div>
                                <div class="col-md-6"><input class="form-control form-control-sm" placeholder="Link" v-model="p.link"></div>
                                <div class="col-md-1"><button type="button" @click="removeProject(idx)" class="btn btn-sm btn-outline-danger w-100"><i class="bi bi-trash"></i></button></div>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Update Resume (PDF)</label>
                                <div class="input-group">
                                    <input type="file" class="form-control" @change="onFileSelect" accept=".pdf">
                                    <button type="button" class="btn btn-outline-crh" @click="uploadResume" :disabled="!resumeFile">Upload</button>
                                </div>
                            </div>
                            <div class="col-md-6 text-end d-flex align-items-end justify-content-end">
                                <button type="submit" class="btn btn-primary-crh px-5">Save Profile Changes</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>

            <div class="row g-4">
                <!-- Left: Professional Opportunities -->
                <div class="col-md-8">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h5 class="fw-800 m-0">Eligible Drives</h5>
                        <input type="text" class="form-control form-control-sm w-50" placeholder="Search roles or companies..." v-model="searchTerm">
                    </div>

                    <div v-if="isLoading" class="p-5 text-center text-muted opacity-50">
                        <div class="spinner-border spinner-border-sm me-2"></div> Synchronizing...
                    </div>

                    <div v-else class="row g-3">
                        <div v-if="filteredDrives.length===0" class="col-12 text-center py-5 text-muted opacity-50 italic">
                            No eligible drives currently active.
                        </div>
                        <div class="col-12" v-for="d in filteredDrives" :key="d.id">
                            <div class="card-crh p-4 h-100 shadow-sm border-0" style="background: white;">
                                <div class="d-flex justify-content-between mb-1">
                                    <h5 class="fw-800 text-primary m-0">{{ d.job_title }}</h5>
                                    <span class="badge bg-success-subtle text-success fw-700">{{ d.base_ctc }}</span>
                                </div>
                                <p class="fw-600 mb-3" style="font-size:0.95rem;">{{ d.company_name }}</p>
                                <p class="text-muted small mb-4 line-clamp-2" style="white-space:pre-line">{{ d.job_description }}</p>
                                
                                <div class="d-flex flex-wrap gap-2 mb-4">
                                    <span class="badge border bg-light text-muted small fw-600">Min CGPA: {{ d.min_cgpa }}</span>
                                    <span class="badge border bg-light text-muted small fw-600">Deadline: {{ d.deadline }}</span>
                                </div>
                                
                                <button class="btn w-100 fw-700 py-2 br-10 shadow-sm"
                                        :disabled="hasApplied(d.id)"
                                        :class="hasApplied(d.id)?'bg-light text-muted border':'btn-primary-crh'"
                                        @click="apply(d.id)">
                                    {{ hasApplied(d.id) ? 'Application Submitted' : 'Apply for Role' }}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right: Status Tracker -->
                <div class="col-md-4">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h5 class="fw-800 m-0">Activity Records</h5>
                        <button class="btn btn-outline-crh btn-sm" @click="exportCSV">
                            <i class="bi bi-download me-1"></i> Export CSV
                        </button>
                    </div>
                    <div class="card-crh overflow-hidden border-0 shadow-sm" style="background: white;">
                        <div v-if="applications.length===0" class="p-5 text-center text-muted opacity-50 small">
                            No application history found.
                        </div>
                        <div v-else class="list-group list-group-flush">
                            <div v-for="a in applications" class="list-group-item p-4 border-0 border-bottom bg-transparent hover-bg">
                                <div class="d-flex justify-content-between mb-1">
                                    <h6 class="fw-800 m-0" style="font-size:0.9rem;">{{ a.job_title }}</h6>
                                    <span class="badge rounded-pill" :class="a.status==='selected'?'bg-success text-white':(a.status==='rejected'?'bg-danger text-white':'bg-light text-dark border')">
                                        {{ a.status.toUpperCase() }}
                                    </span>
                                </div>
                                <div class="text-muted small fw-600 mb-2">{{ a.company_name }}</div>
                                <div class="text-muted" style="font-size: 0.7rem;">Verified on {{ a.date }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
