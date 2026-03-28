const { createApp, reactive } = Vue;

const template = `
  <div>
    <div v-if="errorBanner" class="alert alert-warning">{{ errorBanner }}</div>

    <div v-if="!token">
      <div class="card shadow-sm">
        <div class="card-body">
          <h3 class="card-title mb-3">Login</h3>

          <div class="mb-3">
            <label class="form-label">Role</label>
            <select class="form-select" v-model="login.selectedRole">
              <option value="student">Student</option>
              <option value="company">Company</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label">Email</label>
            <input class="form-control" v-model="login.email" type="email" />
          </div>

          <div class="mb-3">
            <label class="form-label">Password</label>
            <input class="form-control" v-model="login.password" type="password" />
          </div>

          <div v-if="login.error" class="alert alert-danger">{{ login.error }}</div>
          <button class="btn btn-primary" :disabled="login.busy" @click="doLogin">
            {{ login.busy ? 'Signing in...' : 'Sign in' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else>
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 class="mb-0">Dashboard - {{ role }}</h4>
          <div class="text-muted" style="font-size: 0.95rem;">{{ user && user.email ? user.email : '' }}</div>
        </div>
        <button class="btn btn-outline-secondary" @click="logout">Logout</button>
      </div>

      <div v-if="role === 'admin'" class="row g-3">
        <div class="col-12 col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Admin Stats</h5>
              <div v-if="admin.stats">
                <div>Total students: <b>{{ admin.stats.total_students }}</b></div>
                <div>Total companies: <b>{{ admin.stats.total_companies }}</b></div>
                <div>Total drives: <b>{{ admin.stats.total_drives }}</b></div>
                <div>Pending companies: <b>{{ admin.stats.pending_companies }}</b></div>
              </div>
              <div v-else class="text-muted">Loading...</div>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Approvals</h5>
              <div v-if="admin.error" class="alert alert-danger">{{ admin.error }}</div>

              <div class="mb-3">
                <label class="form-label">Company ID</label>
                <input class="form-control" v-model="admin.companyId" />
              </div>
              <div class="d-flex gap-2 mb-3">
                <button class="btn btn-success" :disabled="admin.busy" @click="adminApproveCompany">Approve Company</button>
                <button class="btn btn-danger" :disabled="admin.busy" @click="adminRejectCompany">Reject Company</button>
              </div>

              <div class="mb-3">
                <label class="form-label">Drive ID</label>
                <input class="form-control" v-model="admin.driveId" />
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-success" :disabled="admin.busy" @click="adminApproveDrive">Approve Drive</button>
                <button class="btn btn-danger" :disabled="admin.busy" @click="adminRejectDrive">Reject Drive</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="role === 'company'" class="row g-3">
        <div class="col-12">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Company Profile</h5>
              <div v-if="company.me">
                <div><b>{{ company.me.company_name }}</b></div>
                <div class="text-muted">Approval: {{ company.me.approval_status }}</div>
              </div>
              <div v-else class="text-muted">Loading...</div>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-7">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Placement Drives</h5>
              <div v-if="company.drives.length === 0" class="text-muted">No drives yet.</div>
              <div v-for="d in company.drives" :key="d.id" class="border rounded p-2 mb-2 bg-white">
                <div class="fw-semibold">{{ d.job_title }}</div>
                <div class="text-muted">Deadline: {{ d.application_deadline }}</div>
                <div class="text-muted">Status: {{ d.status }} | Applicants: {{ d.applicant_count }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-5">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Create Drive</h5>
              <div class="mb-2">
                <label class="form-label">Job Title</label>
                <input class="form-control" v-model="company.createForm.job_title" />
              </div>
              <div class="mb-2">
                <label class="form-label">Eligibility Branch</label>
                <input class="form-control" v-model="company.createForm.eligibility_branch" />
              </div>
              <div class="row g-2">
                <div class="col-6">
                  <label class="form-label">Min CGPA</label>
                  <input class="form-control" v-model="company.createForm.eligibility_cgpa_min" />
                </div>
                <div class="col-6">
                  <label class="form-label">Min Year</label>
                  <input class="form-control" v-model="company.createForm.eligibility_year_min" />
                </div>
              </div>
              <div class="mb-2 mt-2">
                <label class="form-label">Application Deadline (ISO)</label>
                <input class="form-control" v-model="company.createForm.application_deadline" placeholder="2026-04-01T18:00:00" />
              </div>
              <div class="mb-2">
                <label class="form-label">Job Description</label>
                <textarea class="form-control" v-model="company.createForm.job_description" rows="3"></textarea>
              </div>
              <div v-if="company.error" class="alert alert-danger">{{ company.error }}</div>
              <button class="btn btn-primary w-100" :disabled="company.busy" @click="createCompanyDrive">Create</button>
            </div>
          </div>
        </div>

        <div class="col-12">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Drive Applications</h5>
              <div class="row g-2">
                <div class="col-md-4">
                  <input class="form-control" v-model="company.appsDriveId" placeholder="Drive ID" />
                </div>
                <div class="col-md-2">
                  <button class="btn btn-secondary w-100" :disabled="company.busy" @click="companyLoadApplications">Load</button>
                </div>
              </div>
              <div v-if="company.driveApplications && company.driveApplications.drive" class="mt-3">
                <div class="text-muted">Drive: {{ company.driveApplications.drive.job_title }} | Status: {{ company.driveApplications.drive.status }}</div>
                <div v-for="a in company.driveApplications.items" :key="a.application_id" class="border rounded p-2 mb-2 bg-white">
                  <div class="fw-semibold">{{ a.student.full_name }}</div>
                  <div class="text-muted">Branch: {{ a.student.branch }} | CGPA: {{ a.student.cgpa }}</div>
                  <div class="text-muted">Application Status: {{ a.status }} | Final: {{ a.final_selection_status }}</div>
                  <div class="d-flex gap-2 mt-2">
                    <button class="btn btn-sm btn-outline-primary" @click="companyUpdateApplication(a.application_id, 'shortlisted')">Shortlist</button>
                    <button class="btn btn-sm btn-outline-success" @click="companyUpdateApplication(a.application_id, 'selected')">Select</button>
                    <button class="btn btn-sm btn-outline-danger" @click="companyUpdateApplication(a.application_id, 'rejected')">Reject</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="role === 'student'" class="row g-3">
        <div class="col-12 col-md-7">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Approved Eligible Drives</h5>
              <div v-if="student.drives.length === 0" class="text-muted">No eligible drives right now.</div>
              <div v-for="d in student.drives" :key="d.id" class="border rounded p-2 mb-2 bg-white">
                <div class="fw-semibold">{{ d.job_title }}</div>
                <div class="text-muted">Deadline: {{ d.application_deadline }}</div>
                <button class="btn btn-primary btn-sm mt-2" :disabled="student.busy" @click="applyToDrive(d.id)">Apply</button>
              </div>
              <div v-if="student.error" class="alert alert-danger mt-2">{{ student.error }}</div>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-5">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Placement History</h5>
              <div class="text-muted" v-if="!student.applications || student.applications.length === 0">No applications yet.</div>
              <div v-for="a in student.applications" :key="a.application_id" class="border rounded p-2 mb-2 bg-white">
                <div class="text-muted">Drive ID: {{ a.drive_id }}</div>
                <div>Status: <b>{{ a.status }}</b></div>
                <div class="text-muted">Applied: {{ a.application_date }}</div>
                <div class="text-muted">Final: {{ a.final_selection_status }}</div>
              </div>
              <button class="btn btn-outline-secondary w-100" @click="refreshStudent">Refresh</button>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Export Applications (CSV)</h5>
              <button class="btn btn-primary" :disabled="student.busy" @click="exportStudentCSV">Export CSV</button>
              <div v-if="student.exportTask" class="text-muted mt-2">Task ID: {{ student.exportTask }}</div>
              <div v-if="student.exportStatus" class="mt-2">
                <div class="text-muted">State: {{ student.exportStatus.state }}</div>
                <div v-if="student.exportStatus.result && student.exportStatus.result.csv_path" class="mt-2">
                  <a class="btn btn-success btn-sm" :href="'/api/student/export/applications/' + student.exportTask + '/download'">Download</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5>Notifications</h5>
              <div v-if="student.notifications.length === 0" class="text-muted">No notifications.</div>
              <div v-for="n in student.notifications" :key="n.id" class="border rounded p-2 mb-2 bg-white">
                <div class="text-muted" style="font-size: 0.9rem;">{{ n.created_at }}</div>
                <div>{{ n.message }}</div>
              </div>
              <button class="btn btn-outline-secondary w-100" @click="hydrateDashboard">Refresh</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
`;

createApp({
  template,
  setup() {
    const state = reactive({
      token: localStorage.getItem("ppa_token") || "",
      role: localStorage.getItem("ppa_role") || "",
      user: null,

      login: {
        email: "",
        password: "",
        selectedRole: "student",
        busy: false,
        error: "",
      },

      admin: { stats: null, companyId: "", driveId: "", busy: false, error: "" },
      company: {
        me: null,
        drives: [],
        createForm: {
          job_title: "",
          job_description: "",
          eligibility_branch: "",
          eligibility_cgpa_min: "",
          eligibility_year_min: "",
          application_deadline: "",
        },
        busy: false,
        error: "",
        driveApplications: { drive: null, items: [] },
        appsDriveId: "",
      },
      student: {
        me: null,
        drives: [],
        applications: [],
        exportTask: null,
        exportStatus: null,
        notifications: [],
        busy: false,
        error: "",
      },
      errorBanner: "",
    });

    function setAuth(token, role, user) {
      state.token = token;
      state.role = role;
      state.user = user;
      localStorage.setItem("ppa_token", token);
      localStorage.setItem("ppa_role", role);
    }

    function clearAuth() {
      state.token = "";
      state.role = "";
      state.user = null;
      localStorage.removeItem("ppa_token");
      localStorage.removeItem("ppa_role");
    }

    async function hydrateDashboard() {
      state.errorBanner = "";

      if (!state.role) return;

      if (state.role === "admin") {
        const stats = await API.apiGet("/api/admin/dashboard/stats");
        state.admin.stats = stats;
      }

      if (state.role === "company") {
        state.company.me = await API.apiGet("/api/company/me");
        const drives = await API.apiGet("/api/company/drives");
        state.company.drives = drives.items || [];
      }

      if (state.role === "student") {
        state.student.me = await API.apiGet("/api/student/me");
        const drives = await API.apiGet("/api/student/drives");
        state.student.drives = drives.items || [];
        const apps = await API.apiGet("/api/student/applications");
        state.student.applications = apps.items || [];
        const notifs = await API.apiGet("/api/student/notifications");
        state.student.notifications = notifs.items || [];
      }
    }

    async function doLogin() {
      state.login.busy = true;
      state.login.error = "";
      try {
        const payload = { email: state.login.email, password: state.login.password };
        let res;

        if (state.login.selectedRole === "admin") {
          res = await API.apiPost("/api/auth/admin/login", payload);
        } else if (state.login.selectedRole === "company") {
          res = await API.apiPost("/api/auth/company/login", payload);
        } else {
          res = await API.apiPost("/api/auth/student/login", payload);
        }

        setAuth(res.access_token, res.user.role, res.user);
        await hydrateDashboard();
      } catch (e) {
        state.login.error = e.message || String(e);
      } finally {
        state.login.busy = false;
      }
    }

    function logout() {
      clearAuth();
      window.location.reload();
    }

    async function applyToDrive(driveId) {
      state.student.error = "";
      state.student.busy = true;
      try {
        await API.apiPost(`/api/student/drives/${driveId}/apply`);
        await hydrateDashboard();
      } catch (e) {
        state.student.error = e.message || String(e);
      } finally {
        state.student.busy = false;
      }
    }

    async function refreshStudent() {
      await hydrateDashboard();
    }

    async function createCompanyDrive() {
      state.company.error = "";
      state.company.busy = true;
      try {
        const f = state.company.createForm;
        const payload = {
          job_title: f.job_title,
          job_description: f.job_description,
          eligibility_branch: f.eligibility_branch,
          eligibility_cgpa_min: f.eligibility_cgpa_min,
          eligibility_year_min: f.eligibility_year_min,
          application_deadline: f.application_deadline,
        };
        await API.apiPost("/api/company/drives", payload);
        const drives = await API.apiGet("/api/company/drives");
        state.company.drives = drives.items || [];
      } catch (e) {
        state.company.error = e.message || String(e);
      } finally {
        state.company.busy = false;
      }
    }

    async function companyLoadApplications() {
      state.company.error = "";
      state.company.busy = true;
      try {
        state.company.driveApplications = await API.apiGet(
          `/api/company/drives/${state.company.appsDriveId}/applications`
        );
      } catch (e) {
        state.company.error = e.message || String(e);
      } finally {
        state.company.busy = false;
      }
    }

    async function companyUpdateApplication(appId, newStatus) {
      state.company.error = "";
      state.company.busy = true;
      try {
        await API.apiPost(
          `/api/company/drives/${state.company.appsDriveId}/applications/${appId}/status`,
          { status: newStatus }
        );
        await companyLoadApplications();
      } catch (e) {
        state.company.error = e.message || String(e);
      } finally {
        state.company.busy = false;
      }
    }

    async function adminApproveCompany() {
      state.admin.error = "";
      state.admin.busy = true;
      try {
        await API.apiPost(`/api/admin/companies/${state.admin.companyId}/approve`);
        await hydrateDashboard();
      } catch (e) {
        state.admin.error = e.message || String(e);
      } finally {
        state.admin.busy = false;
      }
    }

    async function adminRejectCompany() {
      state.admin.error = "";
      state.admin.busy = true;
      try {
        await API.apiPost(`/api/admin/companies/${state.admin.companyId}/reject`);
        await hydrateDashboard();
      } catch (e) {
        state.admin.error = e.message || String(e);
      } finally {
        state.admin.busy = false;
      }
    }

    async function adminApproveDrive() {
      state.admin.error = "";
      state.admin.busy = true;
      try {
        await API.apiPost(`/api/admin/drives/${state.admin.driveId}/approve`);
        await hydrateDashboard();
      } catch (e) {
        state.admin.error = e.message || String(e);
      } finally {
        state.admin.busy = false;
      }
    }

    async function adminRejectDrive() {
      state.admin.error = "";
      state.admin.busy = true;
      try {
        await API.apiPost(`/api/admin/drives/${state.admin.driveId}/reject`);
        await hydrateDashboard();
      } catch (e) {
        state.admin.error = e.message || String(e);
      } finally {
        state.admin.busy = false;
      }
    }

    async function exportStudentCSV() {
      state.student.error = "";
      state.student.busy = true;
      state.student.exportTask = null;
      state.student.exportStatus = null;
      try {
        const res = await API.apiPost("/api/student/export/applications", {});
        state.student.exportTask = res.task_id;

        // Poll
        let tries = 0;
        while (tries < 30) {
          tries += 1;
          const status = await API.apiGet(
            `/api/student/export/applications/${state.student.exportTask}/status`
          );
          state.student.exportStatus = status;
          if (status.state === "SUCCESS") break;
          await new Promise((r) => setTimeout(r, 1500));
        }
        await hydrateDashboard();
      } catch (e) {
        state.student.error = e.message || String(e);
      } finally {
        state.student.busy = false;
      }
    }

    if (state.token && state.role) {
      hydrateDashboard().catch(() => {
        state.errorBanner = "Session invalid. Please log in again.";
        clearAuth();
      });
    }

    return {
      ...state,
      doLogin,
      logout,
      hydrateDashboard,
      applyToDrive,
      refreshStudent,
      createCompanyDrive,
      companyLoadApplications,
      companyUpdateApplication,
      adminApproveCompany,
      adminRejectCompany,
      adminApproveDrive,
      adminRejectDrive,
      exportStudentCSV,
    };
  },
}).mount("#app");

