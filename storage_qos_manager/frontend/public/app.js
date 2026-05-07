// Storage QoS Manager - Frontend JavaScript

const API_BASE = '';
let throughputChart = null;
let usageChart = null;
let metricsHistoryChart = null;
let currentAlertFilter = 'all';

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadDashboard();
    loadTenants();
    loadPolicies();
    loadAlerts();
    
    // Auto-refresh every 5 seconds
    setInterval(() => {
        refreshData();
    }, 5000);
});

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            switchPage(page);
            
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchPage(page) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => p.classList.remove('active'));
    
    const targetPage = document.getElementById(`page-${page}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Update page title
    const titles = {
        dashboard: 'Dashboard Overview',
        tenants: 'Tenant Management',
        policies: 'Traffic Shaping Policies',
        metrics: 'Historical Metrics',
        alerts: 'System Alerts'
    };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';
    
    // Load page-specific data
    if (page === 'metrics') {
        loadMetrics();
    } else if (page === 'alerts') {
        loadAlerts();
    }
}

// Data Loading
async function refreshData() {
    updateTimestamp();
    await loadDashboard();
    await loadTenants();
    await loadPolicies();
    await loadAlerts();
    
    // Refresh charts if on metrics page
    if (document.getElementById('page-metrics').classList.contains('active')) {
        loadMetrics();
    }
}

function updateTimestamp() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = 
        `Last update: ${now.toLocaleTimeString()}`;
}

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/dashboard/stats`);
        const stats = await response.json();
        
        document.getElementById('totalTenants').textContent = stats.total_tenants;
        document.getElementById('activeTenants').textContent = stats.active_tenants;
        document.getElementById('warningTenants').textContent = stats.warning_tenants;
        document.getElementById('overallUsage').textContent = `${stats.overall_usage_percent}%`;
        document.getElementById('totalThroughput').textContent = `${stats.total_throughput_mbps.toLocaleString()} Mbps`;
        document.getElementById('unackAlerts').textContent = stats.unacknowledged_alerts;
        
        // Update alert badge
        document.getElementById('alertBadge').textContent = stats.unacknowledged_alerts;
        
        // Update top consumers table
        const tbody = document.getElementById('topConsumersTable');
        tbody.innerHTML = stats.top_consumers.map((consumer, index) => {
            const tenant = stats.top_consumers.find(t => t.tenant_id === consumer.tenant_id);
            const usagePercent = ((consumer.throughput / tenant.quota_mbps) * 100).toFixed(1);
            return `
                <tr>
                    <td>${index + 1}</td>
                    <td>${consumer.name}</td>
                    <td>${consumer.throughput.toLocaleString()}</td>
                    <td>${tenant.quota_mbps.toLocaleString()}</td>
                    <td>${usagePercent}%</td>
                </tr>
            `;
        }).join('');
        
        // Update charts
        updateCharts(stats);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadTenants() {
    try {
        const response = await fetch(`${API_BASE}/api/tenants`);
        const tenants = await response.json();
        
        const tbody = document.getElementById('tenantsTable');
        tbody.innerHTML = tenants.map(tenant => `
            <tr>
                <td><strong>${tenant.id}</strong></td>
                <td>${tenant.name}</td>
                <td>${tenant.department}</td>
                <td>${tenant.current_throughput_mbps.toLocaleString()}</td>
                <td>${tenant.quota_mbps.toLocaleString()}</td>
                <td>${tenant.burst_limit_mbps.toLocaleString()}</td>
                <td><span class="priority-badge priority-${tenant.priority}">${tenant.priority}</span></td>
                <td><span class="status-badge ${tenant.status}">${tenant.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="editTenant('${tenant.id}')">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTenant('${tenant.id}')">Delete</button>
                </td>
            </tr>
        `).join('');
        
        // Update tenant filter for metrics and policy modal
        updateTenantFilters(tenants);
        
    } catch (error) {
        console.error('Error loading tenants:', error);
    }
}

async function loadPolicies() {
    try {
        const response = await fetch(`${API_BASE}/api/policies`);
        const policies = await response.json();
        
        const tbody = document.getElementById('policiesTable');
        tbody.innerHTML = policies.map(policy => `
            <tr>
                <td><strong>${policy.id}</strong></td>
                <td>${policy.name}</td>
                <td>${policy.tenant_id}</td>
                <td>${policy.min_bandwidth_mbps}</td>
                <td>${policy.max_bandwidth_mbps}</td>
                <td>${policy.burst_duration_sec}s</td>
                <td><span class="status-badge ${policy.priority_queue === 'high' ? 'active' : policy.priority_queue === 'medium' ? 'warning' : ''}">${policy.priority_queue}</span></td>
                <td>${policy.shaping_algorithm.replace('_', ' ')}</td>
                <td>
                    <span class="status-badge ${policy.enabled ? 'active' : 'suspended'}">
                        ${policy.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="togglePolicy('${policy.id}')">
                        ${policy.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editPolicy('${policy.id}')">Edit</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading policies:', error);
    }
}

async function loadMetrics() {
    const tenantId = document.getElementById('metricsTenantFilter').value;
    
    try {
        const url = tenantId 
            ? `${API_BASE}/api/metrics?tenant_id=${tenantId}&limit=50`
            : `${API_BASE}/api/metrics?limit=50`;
        
        const response = await fetch(url);
        const metrics = await response.json();
        
        // Group metrics by tenant
        const metricsByTenant = {};
        metrics.forEach(m => {
            if (!metricsByTenant[m.tenant_id]) {
                metricsByTenant[m.tenant_id] = [];
            }
            metricsByTenant[m.tenant_id].push(m);
        });
        
        // Update or create chart
        const ctx = document.getElementById('metricsHistoryChart').getContext('2d');
        
        if (metricsHistoryChart) {
            metricsHistoryChart.destroy();
        }
        
        const datasets = Object.entries(metricsByTenant).map(([tenantId, data], index) => {
            const colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
            return {
                label: data[0]?.tenant_name || tenantId,
                data: data.map(m => m.throughput_mbps),
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                tension: 0.4,
                fill: false
            };
        });
        
        metricsHistoryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: metrics.slice(0, 50).map(m => {
                    const time = new Date(m.timestamp);
                    return time.toLocaleTimeString();
                }),
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Throughput Over Time (Mbps)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Throughput (Mbps)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

async function loadAlerts() {
    try {
        let url = `${API_BASE}/api/alerts`;
        if (currentAlertFilter === 'unacknowledged') {
            url += '?acknowledged=false';
        } else if (currentAlertFilter === 'acknowledged') {
            url += '?acknowledged=true';
        }
        
        const response = await fetch(url);
        const alerts = await response.json();
        
        const container = document.getElementById('alertsList');
        
        if (alerts.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">No alerts to display</div>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.severity}">
                <div class="alert-info">
                    <div class="alert-type">
                        ${alert.severity === 'critical' ? '🚨' : '⚠️'} 
                        ${alert.type.replace('_', ' ').toUpperCase()}
                    </div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">
                        Tenant: ${alert.tenant_name} | ${new Date(alert.timestamp).toLocaleString()}
                        ${alert.acknowledged ? ' | ✅ Acknowledged' : ''}
                    </div>
                </div>
                ${!alert.acknowledged ? `
                    <button class="btn btn-sm btn-primary" onclick="acknowledgeAlert('${alert.id}')">
                        Acknowledge
                    </button>
                ` : ''}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Charts
function updateCharts(stats) {
    // Fetch detailed tenant data for charts
    fetch(`${API_BASE}/api/tenants`)
        .then(r => r.json())
        .then(tenants => {
            // Throughput Chart
            const throughputCtx = document.getElementById('throughputChart').getContext('2d');
            
            if (throughputChart) {
                throughputChart.destroy();
            }
            
            throughputChart = new Chart(throughputCtx, {
                type: 'bar',
                data: {
                    labels: tenants.map(t => t.name),
                    datasets: [{
                        label: 'Current Throughput (Mbps)',
                        data: tenants.map(t => t.current_throughput_mbps),
                        backgroundColor: '#2563eb',
                        borderRadius: 8
                    }, {
                        label: 'Quota (Mbps)',
                        data: tenants.map(t => t.quota_mbps),
                        backgroundColor: '#e0e7ff',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Mbps'
                            }
                        }
                    }
                }
            });
            
            // Usage Percentage Chart
            const usageCtx = document.getElementById('usageChart').getContext('2d');
            
            if (usageChart) {
                usageChart.destroy();
            }
            
            const usageData = tenants.map(t => ({
                name: t.name,
                percent: (t.current_throughput_mbps / t.quota_mbps) * 100
            }));
            
            usageChart = new Chart(usageCtx, {
                type: 'doughnut',
                data: {
                    labels: tenants.map(t => t.name),
                    datasets: [{
                        data: usageData.map(u => u.percent),
                        backgroundColor: usageData.map(u => {
                            if (u.percent > 100) return '#ef4444';
                            if (u.percent > 90) return '#f59e0b';
                            if (u.percent > 70) return '#10b981';
                            return '#3b82f6';
                        }),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.raw.toFixed(1)}%`;
                                }
                            }
                        }
                    }
                }
            });
        });
}

function updateTenantFilters(tenants) {
    // Metrics filter
    const metricsFilter = document.getElementById('metricsTenantFilter');
    const currentValue = metricsFilter.value;
    metricsFilter.innerHTML = '<option value="">All Tenants</option>' + 
        tenants.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
    metricsFilter.value = currentValue;
    
    // Policy modal tenant select
    const policySelect = document.getElementById('policyTenantSelect');
    policySelect.innerHTML = tenants.map(t => 
        `<option value="${t.id}">${t.name} (${t.id})</option>`
    ).join('');
}

// Modal Functions
function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// CRUD Operations
async function createTenant(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('name'),
        department: formData.get('department'),
        quota_mbps: parseFloat(formData.get('quota_mbps')),
        burst_limit_mbps: parseFloat(formData.get('burst_limit_mbps')),
        priority: parseInt(formData.get('priority'))
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/tenants`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('tenantModal');
            form.reset();
            refreshData();
            showNotification('Tenant created successfully!', 'success');
        }
    } catch (error) {
        console.error('Error creating tenant:', error);
        showNotification('Failed to create tenant', 'error');
    }
}

async function editTenant(tenantId) {
    const tenant = await fetch(`${API_BASE}/api/tenants/${tenantId}`).then(r => r.json());
    
    const newQuota = prompt(`Enter new quota for ${tenant.name} (Mbps):`, tenant.quota_mbps);
    if (newQuota && !isNaN(newQuota)) {
        try {
            await fetch(`${API_BASE}/api/tenants/${tenantId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quota_mbps: parseFloat(newQuota) })
            });
            refreshData();
            showNotification('Tenant updated successfully!', 'success');
        } catch (error) {
            showNotification('Failed to update tenant', 'error');
        }
    }
}

async function deleteTenant(tenantId) {
    if (confirm('Are you sure you want to delete this tenant? This will also remove associated policies.')) {
        try {
            await fetch(`${API_BASE}/api/tenants/${tenantId}`, {
                method: 'DELETE'
            });
            refreshData();
            showNotification('Tenant deleted successfully!', 'success');
        } catch (error) {
            showNotification('Failed to delete tenant', 'error');
        }
    }
}

async function createPolicy(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('name'),
        tenant_id: formData.get('tenant_id'),
        min_bandwidth_mbps: parseFloat(formData.get('min_bandwidth_mbps')),
        max_bandwidth_mbps: parseFloat(formData.get('max_bandwidth_mbps')),
        burst_duration_sec: parseInt(formData.get('burst_duration_sec')),
        priority_queue: formData.get('priority_queue'),
        shaping_algorithm: formData.get('shaping_algorithm'),
        enabled: true
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/policies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('policyModal');
            form.reset();
            refreshData();
            showNotification('Policy created successfully!', 'success');
        }
    } catch (error) {
        console.error('Error creating policy:', error);
        showNotification('Failed to create policy', 'error');
    }
}

async function togglePolicy(policyId) {
    try {
        await fetch(`${API_BASE}/api/policies/${policyId}/toggle`, {
            method: 'POST'
        });
        refreshData();
        showNotification('Policy toggled successfully!', 'success');
    } catch (error) {
        showNotification('Failed to toggle policy', 'error');
    }
}

async function editPolicy(policyId) {
    const policy = await fetch(`${API_BASE}/api/policies/${policyId}`).then(r => r.json());
    
    const newMaxBw = prompt(`Enter new max bandwidth for ${policy.name} (Mbps):`, policy.max_bandwidth_mbps);
    if (newMaxBw && !isNaN(newMaxBw)) {
        try {
            await fetch(`${API_BASE}/api/policies/${policyId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ max_bandwidth_mbps: parseFloat(newMaxBw) })
            });
            refreshData();
            showNotification('Policy updated successfully!', 'success');
        } catch (error) {
            showNotification('Failed to update policy', 'error');
        }
    }
}

async function acknowledgeAlert(alertId) {
    try {
        await fetch(`${API_BASE}/api/alerts/${alertId}/acknowledge`, {
            method: 'POST'
        });
        loadAlerts();
        loadDashboard(); // Update badge count
        showNotification('Alert acknowledged!', 'success');
    } catch (error) {
        showNotification('Failed to acknowledge alert', 'error');
    }
}

function filterAlerts(filter) {
    currentAlertFilter = filter;
    
    // Update button states
    document.querySelectorAll('.filter-buttons .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    loadAlerts();
}

// Notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);
