export default {
    data() {
        return {
            profile: null,
            drives: [],
            applications: [],
            activeDrive: null,
            newDrive: {
                job_title: '', job_description: '', base_ctc: '',
                eligibility_branch: 'All', min_cgpa: 0, deadline: ''
            },
            activeTab: 'drives',
            offerLetterData: null,
            isLoading: true
        }
    },
    async mounted() {
        await this.loadProfile();
        await this.loadDrives();
    },
    methods: {
        async loadProfile() {
            try {
                const res = await axios.get('/api/company/profile');
                this.profile = res.data;
            } catch (err) { /* ignore */ }
        },
        async loadDrives() {
            this.isLoading = true;
            try {
                const res = await axios.get('/api/company/drives');
                this.drives = res.data;
            } catch (err) {
                window.showToast?.('Could not load company drives.');
            } finally {
                this.isLoading = false;
            }
        },
        async createDrive() {
            try {
                await axios.post('/api/company/drives', this.newDrive);
                window.showToast?.('Drive submitted for authorization.');
                this.newDrive = { job_title: '', job_description: '', base_ctc: '', eligibility_branch: 'All', min_cgpa: 0, deadline: '' };
                await this.loadDrives();
                this.activeTab = 'drives';
            } catch (err) {
                window.showToast?.('Submission failed. Check all fields.');
            }
        },
        async viewApplications(driveId) {
            try {
                const res = await axios.get('/api/company/drives/' + driveId + '/applications');
                this.applications = res.data;
                this.activeDrive = driveId;
            } catch (err) { window.showToast?.('Could not load target applications.'); }
        },
        async updateAppStatus(appId, status) {
            try {
                await axios.post('/api/company/applications/' + appId + '/status', { status });
                window.showToast?.('Status updated.');
                await this.viewApplications(this.activeDrive);
            } catch (err) { window.showToast?.('Update failed.'); }
        },
        generateOfferLetter(app) {
            this.offerLetterData = app;
            const modal = new bootstrap.Modal(document.getElementById('offerModal'));
            modal.show();
        }
    },
    template: `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="fw-800 tracking-tight mb-1">Recruitment Hub</h2>
                    <p class="text-muted small mb-0">Organization dashboard and candidate selection</p>
                </div>
                <div v-if="profile">
                    <span class="badge rounded-pill fw-700 px-3 py-2 border" 
                          :class="profile.approval_status==='approved'?'bg-success-subtle text-success border-success-subtle':'bg-warning-subtle text-warning border-warning-subtle'">
                        <i class="bi" :class="profile.approval_status==='approved'?'bi-check-circle-fill':'bi-clock-fill'"></i>
                        {{ profile.approval_status.toUpperCase() }}
                    </span>
                </div>
            </div>

            <!-- Profile Info Row -->
            <div v-if="profile" class="card-crh p-4 mb-4 border-0 shadow-sm" style="background: white;">
                <div class="row align-items-center g-4">
                    <div class="col-md-auto">
                        <div class="bg-success bg-opacity-10 text-success rounded-pill d-flex align-items-center justify-content-center" style="width:50px; height:50px; font-weight:700;">
                            {{ profile.name.charAt(0) }}
                        </div>
                    </div>
                    <div class="col">
                        <h5 class="fw-800 m-0 text-dark">{{ profile.name }}</h5>
                        <p class="text-muted small m-0">{{ profile.industry }} &bull; {{ profile.website }}</p>
                    </div>
                    <div class="col-md-3">
                        <div class="small fw-700 text-muted text-uppercase tracking-wider mb-1" style="font-size:0.65rem;">HR Focal Point</div>
                        <div class="fw-700 text-dark">{{ profile.hr_contact }}</div>
                    </div>
                </div>
            </div>

            <div class="row g-4">
                <!-- Left: Drive Control -->
                <div class="col-md-5">
                    <div class="mb-4 d-flex gap-2 p-1 bg-white border rounded-3 shadow-sm w-fit">
                        <button class="btn btn-sm px-3 fw-600 br-8" :class="activeTab==='drives'?'btn-primary shadow-sm':'btn-link text-muted text-decoration-none'" @click="activeTab='drives'">Engagements</button>
                        <button class="btn btn-sm px-3 fw-600 br-8" :class="activeTab==='create'?'btn-primary shadow-sm':'btn-link text-muted text-decoration-none'" @click="activeTab='create'">Post Drive</button>
                    </div>

                    <div v-if="activeTab==='create'" class="card-crh p-4 animate-in" style="background: white;">
                        <h5 class="fw-800 mb-4">Post Placement Drive</h5>
                        <form @submit.prevent="createDrive">
                            <div class="mb-3">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Role Title</label>
                                <input type="text" class="form-control" v-model="newDrive.job_title" placeholder="e.g. SDE-I" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Short Description</label>
                                <textarea class="form-control" rows="3" v-model="newDrive.job_description" required></textarea>
                            </div>
                            <div class="row g-3 mb-3">
                                <div class="col-6">
                                    <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">CTC Package</label>
                                    <input type="text" class="form-control" v-model="newDrive.base_ctc" placeholder="20 LPA" required>
                                </div>
                                <div class="col-6">
                                    <label class="form-label small fw-700 text-muted text-uppercase tracking-wider">Deadline</label>
                                    <input type="date" class="form-control" v-model="newDrive.deadline" required>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-primary-crh w-100 py-2 br-10">Submit Drive Request</button>
                        </form>
                    </div>

                    <div v-if="activeTab==='drives'" class="animate-in">
                        <h5 class="fw-800 mb-3">Professional Drives</h5>
                        <div v-if="drives.length===0" class="card-crh p-5 text-center text-muted border-0 shadow-sm" style="background: white;">No drives recorded.</div>
                        <div v-for="d in drives" :key="d.id" 
                             class="card-crh p-3 mb-2 border-0 shadow-sm clickable-card transition-all"
                             :class="{'border-primary shadow': activeDrive===d.id}"
                             @click="viewApplications(d.id)" style="background: white; cursor: pointer;">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="fw-800 mb-1" :class="{'text-primary': activeDrive===d.id}">{{ d.job_title }}</h6>
                                    <div class="small fw-700 mt-1" :class="d.status==='approved'?'text-success':'text-warning'">{{ d.status.toUpperCase() }}</div>
                                    <div class="text-muted" style="font-size: 0.7rem;">Applicants: {{ d.applicant_count }} &bull; Ends on {{ d.deadline }}</div>
                                </div>
                                <i class="bi bi-chevron-right text-muted small"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right: Application Review -->
                <div class="col-md-7">
                    <div v-if="activeDrive" class="card-crh overflow-hidden animate-in border-0 shadow-sm" style="background: white;">
                        <div class="p-3 border-bottom bg-light bg-opacity-50">
                            <h6 class="fw-800 m-0">Candidate Ledger &mdash; Drive #{{ activeDrive }}</h6>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-crh align-middle">
                                <thead>
                                    <tr><th>Candidate</th><th>Acad. Record</th><th>Status</th><th>Review</th></tr>
                                </thead>
                                <tbody>
                                    <tr v-for="a in applications" :key="a.application_id">
                                        <td><strong>{{ a.student_name }}</strong><br><small class="text-muted">{{ a.email || 'Verified Student' }}</small></td>
                                        <td>{{ a.branch }} ({{ a.cgpa }})</td>
                                        <td><span class="badge border" :class="a.status==='selected'?'bg-success text-white border-success':'bg-light text-dark'">{{ a.status.toUpperCase() }}</span></td>
                                        <td>
                                            <select class="form-select form-select-sm mb-1" @change="updateAppStatus(a.application_id, $event.target.value)" :value="a.status">
                                                <option value="applied">Applied</option>
                                                <option value="selected">Selected</option>
                                                <option value="rejected">Rejected</option>
                                            </select>
                                            <button v-if="a.status==='selected'" @click="generateOfferLetter(a)" class="btn btn-sm btn-link text-success p-0 fw-700 text-decoration-none small">Generate Offer</button>
                                        </td>
                                    </tr>
                                    <tr v-if="applications.length===0"><td colspan="4" class="text-center py-5 text-muted opacity-50">No candidates have applied to this engagement.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div v-else class="card-crh p-5 text-center text-muted opacity-50 h-100 d-flex flex-column align-items-center justify-content-center" style="background: white;">
                        <i class="bi bi-journal-check mb-3 fs-1"></i>
                        <h5 class="fw-800">Review Selection</h5>
                        <p class="small">Choose an engagement from the list to begin candidate review.</p>
                    </div>
                </div>
            </div>

            <!-- Professional Offer Letter -->
            <div class="modal fade" id="offerModal" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content border-0 shadow-lg br-12 overflow-hidden" style="background: white;">
                        <div class="modal-header border-0 bg-primary text-white p-4">
                            <h5 class="modal-title fw-800">Personnel Recruitment Confirmation</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-5" v-if="offerLetterData">
                            <div class="text-center mb-5">
                                <h1 class="fw-900 tracking-tight text-success mb-2">OFFICIAL OFFER</h1>
                                <p class="text-muted small">Generated via IIT Madras Placement Portal</p>
                            </div>
                            <div class="animate-in" style="animation-delay: 0.1s;">
                                <h4 class="fw-800 mb-4">Dear {{ offerLetterData.student_name }},</h4>
                                <p class="text-dark opacity-75">Following a careful review of your academic path in <strong>{{ offerLetterData.branch }}</strong> (CGPA: {{ offerLetterData.cgpa }}), 
                                we are pleased to confirm your professional selection at <strong>{{ profile.name }}</strong>.</p>
                                
                                <div class="bg-light p-4 rounded-3 my-4 border">
                                    <div class="row g-3">
                                        <div class="col-sm-6">
                                            <div class="small fw-700 text-muted uppercase">Selection Hub</div>
                                            <div class="fw-800">Placement Cell, IITM</div>
                                        </div>
                                        <div class="col-sm-6 text-sm-end">
                                            <div class="small fw-700 text-muted uppercase">Verification Date</div>
                                            <div class="fw-800">{{ new Date().toLocaleDateString() }}</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <p class="text-muted smaller mt-5 pt-3 border-top italic">Our human resources division will synchronize with the campus placement office regarding onboarding documentation.</p>
                            </div>
                        </div>
                        <div class="modal-footer border-0 p-4 pt-0">
                            <button type="button" class="btn btn-outline-crh fw-700" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary-crh fw-700 shadow-sm" onclick="window.print()">Print Official Confirmation</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
