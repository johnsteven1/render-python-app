// JavaScript for Ethical Monitor Dashboard
let lastManualCheck = 0;
const CHECK_COOLDOWN = 30000; // 30 seconds cooldown

// Format timestamp
function formatTime(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Format time difference
function timeAgo(timestamp) {
    if (!timestamp) return 'Never';
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// Load dashboard data
async function loadDashboard() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) throw new Error('Failed to fetch status');
        
        const data = await response.json();
        updateDashboard(data);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

// Update dashboard UI
function updateDashboard(data) {
    // Update last check
    const lastCheck = data.checks?.[data.checks.length - 1];
    if (lastCheck) {
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${timeAgo(lastCheck.timestamp)}`;
        
        // Update status indicator
        const indicatorDot = document.getElementById('indicatorDot');
        const statusText = document.getElementById('statusText');
        const statusCode = document.getElementById('statusCode');
        const responseTime = document.getElementById('responseTime');
        
        if (lastCheck.success) {
            indicatorDot.className = 'indicator-dot up';
            statusText.textContent = 'Website is UP';
            statusText.style.color = '#10b981';
        } else {
            indicatorDot.className = 'indicator-dot down';
            statusText.textContent = 'Website is DOWN';
            statusText.style.color = '#ef4444';
        }
        
        statusCode.textContent = lastCheck.status_code;
        responseTime.textContent = lastCheck.response_time ? 
            `${(lastCheck.response_time * 1000).toFixed(0)} ms` : 'N/A';
    }
    
    // Update stats
    const stats = data.statistics || {};
    document.getElementById('uptimePercentage').textContent = 
        `${stats.uptime ? stats.uptime.toFixed(2) : '100.00'}%`;
    
    document.getElementById('totalChecks').textContent = 
        stats.total_checks || 0;
    
    // Calculate average response time
    const checks = data.checks || [];
    if (checks.length > 0) {
        const validTimes = checks
            .filter(c => c.response_time && c.response_time > 0)
            .map(c => c.response_time);
        
        if (validTimes.length > 0) {
            const avgTime = validTimes.reduce((a, b) => a + b) / validTimes.length;
            document.getElementById('avgResponse').textContent = 
                `${(avgTime * 1000).toFixed(0)} ms`;
        }
        
        // Calculate last 24h checks
        const now = new Date();
        const last24h = checks.filter(c => {
            const checkTime = new Date(c.timestamp);
            return (now - checkTime) < (24 * 60 * 60 * 1000);
        }).length;
        
        document.getElementById('last24h').textContent = last24h;
    }
    
    // Load history
    loadHistory();
}

// Load history table
async function loadHistory() {
    try {
        const limit = document.getElementById('historyLimit').value;
        const response = await fetch(`/api/history?limit=${limit}`);
        if (!response.ok) throw new Error('Failed to fetch history');
        
        const history = await response.json();
        updateHistoryTable(history);
        
    } catch (error) {
        console.error('Error loading history:', error);
        showError('Failed to load history');
    }
}

// Update history table
function updateHistoryTable(history) {
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = '';
    
    if (!history || history.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: #64748b;">
                    No checks recorded yet
                </td>
            </tr>
        `;
        return;
    }
    
    history.forEach(check => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${formatTime(check.timestamp)}</td>
            <td>
                <span class="status-badge ${check.success ? 'success' : 'error'}">
                    ${check.status_code || 'Error'}
                </span>
            </td>
            <td>${check.response_time ? (check.response_time * 1000).toFixed(0) + ' ms' : 'N/A'}</td>
            <td>
                ${check.success ? 
                    '<span style="color: #10b981;">✓ Success</span>' : 
                    '<span style="color: #ef4444;">✗ Failed</span>'
                }
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Manual check button
async function checkNow() {
    const now = Date.now();
    const btn = document.getElementById('checkNowBtn');
    
    // Rate limiting
    if (now - lastManualCheck < CHECK_COOLDOWN) {
        showError('Please wait 30 seconds between manual checks');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
    
    try {
        const response = await fetch('/api/check-now', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Check failed');
        
        const result = await response.json();
        lastManualCheck = now;
        
        // Reload dashboard
        loadDashboard();
        
        // Show success message
        showMessage('Check completed successfully', 'success');
        
        // Re-enable button after delay
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sync-alt"></i> Check Now';
        }, 5000);
        
    } catch (error) {
        console.error('Error checking now:', error);
        showError('Failed to check website');
        
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Check Now';
    }
}

// Refresh data
function refreshData() {
    loadDashboard();
    showMessage('Data refreshed', 'info');
}

// Show message
function showMessage(text, type = 'info') {
    // Remove existing message
    const existingMsg = document.querySelector('.message-toast');
    if (existingMsg) existingMsg.remove();
    
    // Create new message
    const message = document.createElement('div');
    message.className = `message-toast ${type}`;
    message.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${text}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add styles
    message.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#4361ee'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(message);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (message.parentElement) {
            message.remove();
        }
    }, 5000);
}

// Show error
function showError(text) {
    showMessage(text, 'error');
}

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);
});
