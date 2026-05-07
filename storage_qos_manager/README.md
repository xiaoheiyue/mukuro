# Storage Network Throughput Dynamic Shaping & Quota Management System

A professional enterprise-grade web application for managing storage network QoS (Quality of Service), including dynamic throughput shaping and quota management.

## 🚀 Features

### Dashboard
- Real-time system overview with key metrics
- Live throughput monitoring per tenant
- Quota usage visualization with charts
- Top consumers ranking
- Alert summary with badge notifications

### Tenant Management
- Create, edit, and delete tenants (departments/teams)
- Configure bandwidth quotas and burst limits
- Priority assignment (1-5 levels)
- Real-time status monitoring (Active/Warning/Suspended)

### Traffic Shaping Policies
- Multiple shaping algorithms:
  - Token Bucket
  - Leaky Bucket
  - Weighted Fair Queuing
- Configurable min/max bandwidth
- Burst duration settings
- Priority queue assignment
- Enable/disable policies on-the-fly

### Metrics & Analytics
- Historical throughput tracking
- Time-series visualization
- Per-tenant or aggregate views
- Auto-refresh every 5 seconds

### Alert System
- Automatic quota violation detection
- Severity-based alerts (Warning/Critical)
- Alert acknowledgment workflow
- Filterable alert views

## 🛠️ Technology Stack

**Backend:**
- Python 3.x
- Flask RESTful API
- Flask-CORS for cross-origin support

**Frontend:**
- Vanilla JavaScript (ES6+)
- Chart.js for data visualization
- Modern CSS3 with custom properties
- Responsive design

## 📦 Installation

### 1. Install Dependencies

```bash
cd /workspace/storage_qos_manager/backend
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

## 🎯 Usage Guide

### Dashboard Overview
- View real-time statistics at a glance
- Monitor total tenants, active/warning counts
- See overall network usage percentage
- Track unacknowledged alerts

### Managing Tenants
1. Navigate to **Tenants** page
2. Click **+ Add Tenant** to create new
3. Fill in name, department, quota, burst limit, priority
4. Edit existing tenants to adjust quotas
5. Delete tenants when no longer needed

### Creating Policies
1. Go to **Policies** page
2. Click **+ Create Policy**
3. Select target tenant
4. Configure bandwidth limits and algorithm
5. Set priority queue and burst duration
6. Toggle policies on/off as needed

### Monitoring Metrics
1. Visit **Metrics** page
2. Filter by specific tenant or view all
3. Analyze throughput trends over time
4. Identify patterns and anomalies

### Handling Alerts
1. Check **Alerts** page for notifications
2. Filter by All/Unacknowledged/Acknowledged
3. Click **Acknowledge** to mark as handled
4. Critical alerts shown in red, warnings in yellow

## 📊 Sample Data

The system comes pre-loaded with 5 sample tenants:
- Finance Department (1 Gbps quota)
- R&D Lab Alpha (5 Gbps quota)
- Marketing Team (500 Mbps quota)
- HR Systems (200 Mbps quota)
- Video Production (10 Gbps quota)

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tenants` | List all tenants |
| POST | `/api/tenants` | Create tenant |
| PUT | `/api/tenants/<id>` | Update tenant |
| DELETE | `/api/tenants/<id>` | Delete tenant |
| GET | `/api/policies` | List all policies |
| POST | `/api/policies` | Create policy |
| PUT | `/api/policies/<id>` | Update policy |
| POST | `/api/policies/<id>/toggle` | Toggle policy |
| GET | `/api/metrics` | Get historical metrics |
| GET | `/api/alerts` | Get alerts |
| POST | `/api/alerts/<id>/acknowledge` | Acknowledge alert |
| GET | `/api/dashboard/stats` | Dashboard statistics |

## ⚙️ Configuration

The application uses in-memory storage for demonstration. For production use, consider:
- PostgreSQL/MySQL for persistent storage
- Redis for caching and real-time updates
- Authentication middleware
- Rate limiting

## 🎨 UI Features

- Modern dark sidebar navigation
- Color-coded status indicators
- Interactive charts with hover tooltips
- Responsive grid layouts
- Toast notifications for actions
- Smooth animations and transitions

## 📝 License

This project is provided as-is for educational and demonstration purposes.

---

**Storage QoS Manager** - Enterprise Network Traffic Management Solution
