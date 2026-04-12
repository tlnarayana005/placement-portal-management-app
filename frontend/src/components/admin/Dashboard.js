export default {
    data() {
        return {
            stats: { students: 0, companies: 0, drives: 0, applications: 0, selected: 0 },
            companies: [],
            students: [],
            pendingDrives: [],
            allApplications: [],
            auditLogs: [],
            error: null,
            searchCompany: '',
            searchStudent: '',
            activeTab: 'overview',
            editingStudent: null,
            editingCompany: null,
            editingDrive: null,
            isLoading: true
        }
    },
    async mounted() {
        await this.loadData();
    },
    computed: {
        filteredCompanies() {
            if (!this.searchCompany) return this.companies;
            const t = this.searchCompany.toLowerCase();
            return this.companies.filter(c => c.name.toLowerCase().includes(t) || c.email.toLowerCase().includes(t));
        },
        filteredStudents() {
            if (!this.searchStudent) return this.students;
            const t = this.searchStudent.toLowerCase();
            return this.students.filter(s => s.name.toLowerCase().includes(t) || s.email.toLowerCase().includes(t));
        }
    },
    methods: {
        async loadData() {
            this.isLoading = true;
            try {
                const [statsRes, compRes, driveRes, studRes, appsRes, logsRes] = await Promise.all([
                    axios.get('/api/admin/stats'),
                    axios.get('/api/admin/companies'),
                    axios.get('/api/admin/drives/pending'),
                    axios.get('/api/admin/students'),
                    axios.get('/api/admin/applications'),
                    axios.get('/api/admin/audit-logs')
                ]);
                this.stats = statsRes.data;
                this.companies = compRes.data;
                this.pendingDrives = driveRes.data;
                this.students = studRes.data;
                this.allApplications = appsRes.data;
                this.auditLogs = logsRes.data;
            } catch (err) {
                this.error = 'Failed to synchronize with administrative records.';
            } finally {
                this.isLoading = false;
            }
        },
        async approveCompany(id) {
            await axios.post('/api/admin/companies/' + id + '/approve');
            window.showToast?.('Company approved.');
            await this.loadData();
        },
        async approveDrive(id) {
            await axios.post('/api/admin/drives/' + id + '/approve');
            window.showToast?.('Drive approved.');
            await this.loadData();
        },
        async updateAppStatus(id, status) {
            await axios.post(`/api/admin/applications/${id}/status`, { status });
            window.showToast?.('Status overridden by admin.');
            await this.loadData();
        },
        openEditStudent(s) {
            this.editingStudent = { ...s };
            new bootstrap.Modal('#editStudentModal').show();
        },
        async saveStudent() {
            await axios.put('/api/admin/students/' + this.editingStudent.id, this.editingStudent);
            bootstrap.Modal.getInstance('#editStudentModal').hide();
            window.showToast?.('Student profile updated.');
            await this.loadData();
        }
    },
    template: `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="fw-800 tracking-tight mb-1">Administrative Center</h2>
                    <p class="text-muted small mb-0">Operational control and placement auditing</p>
                </div>
                <button class="btn btn-outline-crh btn-sm" @click="loadData" :disabled="isLoading">
                    <i class="bi bi-arrow-repeat me-1" :class="{'spin-slow': isLoading}"></i> Refresh Records
                </button>
            </div>

            <!-- Stats Grid -->
            <div class="row g-3 mb-5">
                <div class="col-md-2" v-for="(val, label) in { Students: stats.students, Partners: stats.companies, Drives: stats.drives, Apps: stats.applications, Hired: stats.selected }">
                    <div class="card-crh p-3 text-center">
                        <div class="small fw-700 text-muted text-uppercase mb-1" style="font-size: 0.65rem; letter-spacing: 1px;">{{ label }}</div>
                        <div class="fs-4 fw-800 text-primary">{{ val }}</div>
                    </div>
                </div>
            </div>

            <!-- Tabs Navigation -->
            <div class="mb-4 d-flex gap-2 p-1 bg-white border rounded-3 shadow-sm w-fit">
                <button v-for="t in ['overview', 'companies', 'students', 'applications', 'logs']" 
                        class="btn btn-sm px-3 fw-600 br-8 transition-all"
                        :class="activeTab===t ? 'btn-primary shadow-sm' : 'btn-link text-decoration-none text-muted'"
                        @click="activeTab=t">
                    {{ t.charAt(0).toUpperCase() + t.slice(1) }}
                </button>
            </div>

            <!-- Tab Content -->
            <div class="card-crh p-4 min-vh-50">
                <div v-if="isLoading" class="text-center py-5">
                    <div class="spinner-border text-primary opacity-25" role="status"></div>
                    <p class="mt-2 text-muted small fw-500">Retrieving secure data...</p>
                </div>

                <div v-else class="fade-in">
                    <!-- Overview: Pending Drives -->
                    <div v-if="activeTab==='overview'">
                        <h5 class="fw-800 mb-4">Pending Drive Approvals</h5>
                        <div class="table-responsive">
                            <table class="table table-hover table-crh align-middle">
                                <thead>
                                    <tr><th>Role / Job</th><th>Organization</th><th>CPC / CTC</th><th>Status</th></tr>
                                </thead>
                                <tbody>
                                    <tr v-for="d in pendingDrives" :key="d.id">
                                        <td class="fw-700">{{ d.job_title }}</td>
                                        <td>{{ d.company_name }}</td>
                                        <td><span class="badge bg-light text-dark border fw-600">{{ d.base_ctc || 'TBD' }}</span></td>
                                        <td>
                                            <button @click="approveDrive(d.id)" class="btn btn-primary-crh btn-sm px-3">Approve Drive</button>
                                        </td>
                                    </tr>
                                    <tr v-if="pendingDrives.length===0"><td colspan="4" class="text-center py-5 text-muted">No pending authorizations requested.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Companies -->
                    <div v-if="activeTab==='companies'">
                        <div class="d-flex justify-content-between mb-4">
                            <h5 class="fw-800 m-0">Organization Partners</h5>
                            <input type="text" class="form-control form-control-sm w-25" placeholder="Search by name..." v-model="searchCompany">
                        </div>
                        <div class="table-responsive">
                            <table class="table table-crh align-middle">
                                <thead>
                                    <tr><th>Corporate Entity</th><th>Vertical</th><th>System Status</th><th>Control</th></tr>
                                </thead>
                                <tbody>
                                    <tr v-for="c in filteredCompanies">
                                        <td><strong>{{ c.name }}</strong><br><small class="text-muted">{{ c.email }}</small></td>
                                        <td>{{ c.industry }}</td>
                                        <td><span class="badge" :class="c.approval_status==='approved'?'bg-success-subtle text-success':'bg-warning-subtle text-warning'">{{ c.approval_status }}</span></td>
                                        <td>
                                            <button v-if="c.approval_status==='pending'" @click="approveCompany(c.id)" class="btn btn-primary-crh btn-sm">Verify Member</button>
                                            <span v-else class="text-muted small">Verified</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Students -->
                    <div v-if="activeTab==='students'">
                        <div class="d-flex justify-content-between mb-4">
                            <h5 class="fw-800 m-0">Student Registry</h5>
                            <input type="text" class="form-control form-control-sm w-25" placeholder="Filter candidates..." v-model="searchStudent">
                        </div>
                        <div class="table-responsive">
                            <table class="table table-crh align-middle">
                                <thead>
                                    <tr><th>Candidate</th><th>Academic Path</th><th>CGPA</th><th>Actions</th></tr>
                                </thead>
                                <tbody>
                                    <tr v-for="s in filteredStudents">
                                        <td><strong>{{ s.name }}</strong><br><small class="text-muted">{{ s.email }}</small></td>
                                        <td>{{ s.branch }} ({{ s.graduation_year }})</td>
                                        <td class="fw-800">{{ s.cgpa }}</td>
                                        <td><button @click="openEditStudent(s)" class="btn btn-outline-crh btn-sm">Edit Data</button></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Applications Override -->
                    <div v-if="activeTab==='applications'">
                        <h5 class="fw-800 mb-4">Placement Auditing</h5>
                        <div class="table-responsive">
                            <table class="table table-crh align-middle">
                                <thead>
                                    <tr><th>Student</th><th>Application Target</th><th>Current Status</th><th>Admin Override</th></tr>
                                </thead>
                                <tbody>
                                    <tr v-for="a in allApplications">
                                        <td>{{ a.student_name }}</td>
                                        <td>{{ a.job_title }} @ {{ a.company_name }}</td>
                                        <td><span class="badge border" :class="a.status==='selected'?'bg-success text-white':'bg-light text-dark'">{{ a.status.toUpperCase() }}</span></td>
                                        <td>
                                            <select class="form-select form-select-sm" @change="updateAppStatus(a.id, $event.target.value)">
                                                <option value="" disabled selected>Override to...</option>
                                                <option value="shortlisted">Shortlisted</option>
                                                <option value="selected">Selected</option>
                                                <option value="rejected">Rejected</option>
                                            </select>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Logs -->
                    <div v-if="activeTab==='logs'">
                        <h5 class="fw-800 mb-4">Action Audit Trail</h5>
                        <div class="list-group list-group-flush shadow-sm br-12 overflow-hidden border">
                            <div v-for="log in auditLogs" class="list-group-item p-3 bg-transparent border-0 border-bottom">
                                <div class="d-flex justify-content-between">
                                    <h6 class="fw-700 mb-1 text-primary">{{ log.admin_name }}</h6>
                                    <small class="text-muted">{{ log.timestamp }}</small>
                                </div>
                                <p class="mb-0 text-dark small" style="opacity: 0.8">{{ log.action }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Edit Modals -->
            <div class="modal fade" id="editStudentModal" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg br-12 overflow-hidden" v-if="editingStudent">
                        <div class="modal-header border-0 bg-light">
                            <h5 class="modal-title fw-800">Edit Data: {{ editingStudent.name }}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="mb-3">
                                <label class="form-label small fw-700 text-uppercase tracking-wider">Branch</label>
                                <input class="form-control" v-model="editingStudent.branch">
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-700 text-uppercase tracking-wider">CGPA</label>
                                <input class="form-control" type="number" step="0.01" v-model="editingStudent.cgpa">
                            </div>
                        </div>
                        <div class="modal-footer border-0">
                            <button @click="saveStudent" class="btn btn-primary-crh w-100 py-2 br-8">Update Records</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
