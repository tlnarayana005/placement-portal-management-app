export default {
    template: `
        <div class="hero-section text-center animate-in">
            <div class="mb-2">
                <span class="badge rounded-pill bg-primary bg-opacity-10 text-primary px-3 py-2 fw-700" style="font-size: 0.75rem;">
                    OFFICIAL PLACEMENT HUB
                </span>
            </div>
            <h1 class="display-4 fw-800 mb-3 tracking-tight" style="color: var(--crh-text-main);">
                Empowering the Future of <span class="text-primary">Recruitment</span>
            </h1>
            <p class="lead mx-auto mb-5 text-muted" style="max-width: 640px;">
                The centralized gateway for IIT Madras students and global industry leaders. 
                Experience a streamlined, high-performance career management platform.
            </p>
            
            <div class="d-flex justify-content-center gap-3 mb-5">
                <router-link to="/login" class="btn btn-primary-crh btn-lg shadow-sm">
                    Access Portal
                </router-link>
                <router-link to="/register" class="btn btn-outline-crh btn-lg shadow-sm">
                    Registration
                </router-link>
            </div>

            <div class="row mt-5 justify-content-center g-4 text-start">
                <div class="col-md-4">
                    <div class="card-crh p-4 h-100">
                        <div class="mb-3 text-primary"><i class="bi bi-shield-lock-fill fs-3"></i></div>
                        <h5 class="fw-700">Enterprise Security</h5>
                        <p class="small text-muted mb-0">Role-based access control and encrypted credentials for all users.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card-crh p-4 h-100">
                        <div class="mb-3 text-success"><i class="bi bi-bar-chart-fill fs-3"></i></div>
                        <h5 class="fw-700">Dynamic Analytics</h5>
                        <p class="small text-muted mb-0">Centralized dashboard for tracking applications and placement statistics.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card-crh p-4 h-100">
                        <div class="mb-3 text-warning"><i class="bi bi-lightning-fill fs-3"></i></div>
                        <h5 class="fw-700">Instant Workflow</h5>
                        <p class="small text-muted mb-0">Automated offer letter generation and one-click applications.</p>
                    </div>
                </div>
            </div>
        </div>
    `
};
