"""
Storage Network Throughput Dynamic Shaping & Quota Management System
Backend API - Flask RESTful Service

Features:
- Real-time throughput monitoring simulation
- Dynamic quota management per tenant/department
- Traffic shaping policy configuration
- Alert system for quota violations
- Historical data tracking and analytics
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import random
import threading
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

app = Flask(__name__, static_folder='../frontend/public', static_url_path='')
CORS(app)

# In-memory database (for demo purposes)
tenants_db: Dict[str, dict] = {}
policies_db: Dict[str, dict] = {}
metrics_history: List[dict] = []
alerts_db: List[dict] = []

@dataclass
class Tenant:
    id: str
    name: str
    department: str
    current_throughput_mbps: float
    quota_mbps: float
    burst_limit_mbps: float
    priority: int  # 1-5, 1 being highest
    status: str  # active, suspended, warning
    created_at: str

@dataclass
class ShapingPolicy:
    id: str
    name: str
    tenant_id: str
    min_bandwidth_mbps: float
    max_bandwidth_mbps: float
    burst_duration_sec: int
    priority_queue: str  # high, medium, low
    shaping_algorithm: str  # token_bucket, leaky_bucket, weighted_fair
    enabled: bool

def init_sample_data():
    """Initialize sample data for demonstration"""
    global tenants_db, policies_db
    
    sample_tenants = [
        Tenant("T001", "Finance Department", "Finance", 450.5, 1000.0, 1500.0, 2, "active", datetime.now().isoformat()),
        Tenant("T002", "R&D Lab Alpha", "Research", 2340.8, 5000.0, 7500.0, 1, "active", datetime.now().isoformat()),
        Tenant("T003", "Marketing Team", "Marketing", 180.2, 500.0, 750.0, 3, "warning", datetime.now().isoformat()),
        Tenant("T004", "HR Systems", "Human Resources", 95.6, 200.0, 300.0, 4, "active", datetime.now().isoformat()),
        Tenant("T005", "Video Production", "Media", 8500.3, 10000.0, 12000.0, 1, "active", datetime.now().isoformat()),
    ]
    
    for tenant in sample_tenants:
        tenants_db[tenant.id] = asdict(tenant)
    
    sample_policies = [
        ShapingPolicy("P001", "Finance Standard", "T001", 100.0, 1000.0, 30, "medium", "token_bucket", True),
        ShapingPolicy("P002", "R&D High Priority", "T002", 1000.0, 5000.0, 60, "high", "weighted_fair", True),
        ShapingPolicy("P003", "Marketing Basic", "T003", 50.0, 500.0, 15, "low", "leaky_bucket", True),
        ShapingPolicy("P004", "HR Conservative", "T004", 25.0, 200.0, 20, "low", "token_bucket", True),
        ShapingPolicy("P005", "Media Ultra", "T005", 5000.0, 10000.0, 120, "high", "weighted_fair", True),
    ]
    
    for policy in sample_policies:
        policies_db[policy.id] = asdict(policy)

init_sample_data()

def simulate_metrics():
    """Simulate real-time network metrics"""
    while True:
        timestamp = datetime.now().isoformat()
        
        for tenant_id, tenant in tenants_db.items():
            # Simulate realistic throughput variations
            base_throughput = tenant['current_throughput_mbps']
            variation = random.uniform(-0.15, 0.15)
            new_throughput = max(0, base_throughput * (1 + variation))
            
            # Update tenant metrics
            tenant['current_throughput_mbps'] = round(new_throughput, 2)
            
            # Check quota violations
            usage_ratio = new_throughput / tenant['quota_mbps']
            if usage_ratio > 0.95:
                tenant['status'] = 'warning'
                if usage_ratio > 1.0:
                    alert = {
                        'id': f"A{len(alerts_db)+1:04d}",
                        'tenant_id': tenant_id,
                        'tenant_name': tenant['name'],
                        'type': 'quota_exceeded',
                        'severity': 'critical' if usage_ratio > 1.2 else 'warning',
                        'message': f"Throughput {new_throughput:.2f} Mbps exceeds quota {tenant['quota_mbps']} Mbps",
                        'timestamp': timestamp,
                        'acknowledged': False
                    }
                    alerts_db.insert(0, alert)
            elif usage_ratio < 0.8:
                tenant['status'] = 'active'
            
            # Record metrics history
            metric = {
                'timestamp': timestamp,
                'tenant_id': tenant_id,
                'tenant_name': tenant['name'],
                'throughput_mbps': new_throughput,
                'quota_mbps': tenant['quota_mbps'],
                'usage_percent': round((new_throughput / tenant['quota_mbps']) * 100, 2),
                'burst_limit_mbps': tenant['burst_limit_mbps'],
                'priority': tenant['priority']
            }
            metrics_history.append(metric)
        
        # Keep only last 1000 metrics
        if len(metrics_history) > 1000:
            metrics_history.pop(0)
        
        time.sleep(2)  # Update every 2 seconds

# Start metrics simulation thread
metrics_thread = threading.Thread(target=simulate_metrics, daemon=True)
metrics_thread.start()

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/tenants', methods=['GET'])
def get_tenants():
    """Get all tenants with current metrics"""
    return jsonify(list(tenants_db.values()))

@app.route('/api/tenants/<tenant_id>', methods=['GET'])
def get_tenant(tenant_id):
    """Get specific tenant details"""
    if tenant_id not in tenants_db:
        return jsonify({'error': 'Tenant not found'}), 404
    return jsonify(tenants_db[tenant_id])

@app.route('/api/tenants', methods=['POST'])
def create_tenant():
    """Create a new tenant"""
    data = request.json
    tenant_id = f"T{len(tenants_db)+1:03d}"
    
    tenant = Tenant(
        id=tenant_id,
        name=data.get('name', 'Unknown'),
        department=data.get('department', 'General'),
        current_throughput_mbps=0.0,
        quota_mbps=data.get('quota_mbps', 100.0),
        burst_limit_mbps=data.get('burst_limit_mbps', 150.0),
        priority=data.get('priority', 3),
        status='active',
        created_at=datetime.now().isoformat()
    )
    
    tenants_db[tenant_id] = asdict(tenant)
    return jsonify(tenant), 201

@app.route('/api/tenants/<tenant_id>', methods=['PUT'])
def update_tenant(tenant_id):
    """Update tenant quota and settings"""
    if tenant_id not in tenants_db:
        return jsonify({'error': 'Tenant not found'}), 404
    
    data = request.json
    tenant = tenants_db[tenant_id]
    
    if 'quota_mbps' in data:
        tenant['quota_mbps'] = float(data['quota_mbps'])
    if 'burst_limit_mbps' in data:
        tenant['burst_limit_mbps'] = float(data['burst_limit_mbps'])
    if 'priority' in data:
        tenant['priority'] = int(data['priority'])
    
    return jsonify(tenant)

@app.route('/api/tenants/<tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    """Delete a tenant"""
    if tenant_id not in tenants_db:
        return jsonify({'error': 'Tenant not found'}), 404
    
    del tenants_db[tenant_id]
    # Also remove associated policies
    policies_to_remove = [pid for pid, p in policies_db.items() if p['tenant_id'] == tenant_id]
    for pid in policies_to_remove:
        del policies_db[pid]
    
    return jsonify({'message': 'Tenant deleted successfully'})

@app.route('/api/policies', methods=['GET'])
def get_policies():
    """Get all shaping policies"""
    return jsonify(list(policies_db.values()))

@app.route('/api/policies', methods=['POST'])
def create_policy():
    """Create a new traffic shaping policy"""
    data = request.json
    policy_id = f"P{len(policies_db)+1:03d}"
    
    policy = ShapingPolicy(
        id=policy_id,
        name=data.get('name', 'New Policy'),
        tenant_id=data.get('tenant_id'),
        min_bandwidth_mbps=float(data.get('min_bandwidth_mbps', 0)),
        max_bandwidth_mbps=float(data.get('max_bandwidth_mbps', 1000)),
        burst_duration_sec=int(data.get('burst_duration_sec', 30)),
        priority_queue=data.get('priority_queue', 'medium'),
        shaping_algorithm=data.get('shaping_algorithm', 'token_bucket'),
        enabled=data.get('enabled', True)
    )
    
    policies_db[policy_id] = asdict(policy)
    return jsonify(policy), 201

@app.route('/api/policies/<policy_id>', methods=['PUT'])
def update_policy(policy_id):
    """Update a shaping policy"""
    if policy_id not in policies_db:
        return jsonify({'error': 'Policy not found'}), 404
    
    data = request.json
    policy = policies_db[policy_id]
    
    for key in ['min_bandwidth_mbps', 'max_bandwidth_mbps', 'burst_duration_sec', 
                'priority_queue', 'shaping_algorithm', 'enabled']:
        if key in data:
            policy[key] = data[key]
    
    return jsonify(policy)

@app.route('/api/policies/<policy_id>/toggle', methods=['POST'])
def toggle_policy(policy_id):
    """Enable/disable a policy"""
    if policy_id not in policies_db:
        return jsonify({'error': 'Policy not found'}), 404
    
    policy = policies_db[policy_id]
    policy['enabled'] = not policy['enabled']
    
    return jsonify(policy)

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get historical metrics with optional filtering"""
    tenant_id = request.args.get('tenant_id')
    limit = int(request.args.get('limit', 100))
    
    filtered = metrics_history
    if tenant_id:
        filtered = [m for m in metrics_history if m['tenant_id'] == tenant_id]
    
    return jsonify(filtered[-limit:])

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    acknowledged = request.args.get('acknowledged')
    
    filtered = alerts_db
    if acknowledged is not None:
        ack_bool = acknowledged.lower() == 'true'
        filtered = [a for a in alerts_db if a['acknowledged'] == ack_bool]
    
    return jsonify(filtered)

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    for alert in alerts_db:
        if alert['id'] == alert_id:
            alert['acknowledged'] = True
            return jsonify(alert)
    
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    total_tenants = len(tenants_db)
    active_tenants = sum(1 for t in tenants_db.values() if t['status'] == 'active')
    warning_tenants = sum(1 for t in tenants_db.values() if t['status'] == 'warning')
    
    total_throughput = sum(t['current_throughput_mbps'] for t in tenants_db.values())
    total_quota = sum(t['quota_mbps'] for t in tenants_db.values())
    overall_usage = (total_throughput / total_quota * 100) if total_quota > 0 else 0
    
    unacknowledged_alerts = sum(1 for a in alerts_db if not a['acknowledged'])
    
    # Top consumers
    top_consumers = sorted(
        [{'tenant_id': t['id'], 'name': t['name'], 'throughput': t['current_throughput_mbps']} 
         for t in tenants_db.values()],
        key=lambda x: x['throughput'],
        reverse=True
    )[:5]
    
    return jsonify({
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'warning_tenants': warning_tenants,
        'total_throughput_mbps': round(total_throughput, 2),
        'total_quota_mbps': round(total_quota, 2),
        'overall_usage_percent': round(overall_usage, 2),
        'unacknowledged_alerts': unacknowledged_alerts,
        'top_consumers': top_consumers
    })

if __name__ == '__main__':
    print("🚀 Storage QoS Manager Backend Starting...")
    print("📊 Dashboard: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
