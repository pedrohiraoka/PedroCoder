/**
 * AstroWatch Dashboard - Main JavaScript
 * 
 * Handles real-time data polling, Chart.js visualization, and DOM updates.
 * Uses Fetch API for consuming PHP endpoints with automatic fallback.
 * 
 * @package AstroWatch
 * @version 1.0.0
 */

'use strict';

// ============================================================================
// APPLICATION STATE
// ============================================================================

const AppState = {
    lastUpdate: null,
    connectionStatus: 'connected',
    weatherChart: null,
    pollingTimers: {},
    retryCounts: {
        alerts: 0,
        weather: 0,
        instruments: 0
    },
    maxRetries: 3
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format timestamp to locale time string
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Formatted time
 */
function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
}

/**
 * Calculate age from timestamp
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Human-readable age
 */
function calculateAge(isoString) {
    const now = new Date();
    const then = new Date(isoString);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffHours > 0) {
        return `${diffHours}h ${diffMins % 60}m`;
    }
    return `${diffMins}m`;
}

/**
 * Get status color based on value
 * @param {string} status - Status string
 * @returns {string} Color hex code
 */
function getStatusColor(status) {
    const colors = {
        ok: ASTROWATCH_CONFIG.statusColors.ok,
        warning: ASTROWATCH_CONFIG.statusColors.warning,
        error: ASTROWATCH_CONFIG.statusColors.error,
        offline: ASTROWATCH_CONFIG.statusColors.offline
    };
    return colors[status] || colors.ok;
}

/**
 * Determine health level based on percentage
 * @param {number} percentage - Health percentage
 * @returns {string} Health level: 'good', 'warning', or 'critical'
 */
function getHealthLevel(percentage) {
    if (percentage >= 90) return 'good';
    if (percentage >= 70) return 'warning';
    return 'critical';
}

/**
 * Debounce function execution
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================================================
// UPDATE TIMER DISPLAY
// ============================================================================

/**
 * Update countdown timers for each panel
 */
function updateTimers() {
    const timers = {
        'weather-timer': ASTROWATCH_CONFIG.pollingIntervals.weather / 1000,
        'alerts-timer': ASTROWATCH_CONFIG.pollingIntervals.alerts / 1000,
        'instruments-timer': ASTROWATCH_CONFIG.pollingIntervals.instruments / 1000
    };
    
    Object.entries(timers).forEach(([elementId, interval]) => {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        let current = parseInt(element.textContent) || interval;
        current--;
        
        if (current <= 0) {
            current = interval;
        }
        
        element.textContent = `${current}s`;
    });
}

/**
 * Start timer countdown
 */
function startTimerCountdown() {
    setInterval(() => {
        updateTimers();
        updateTimeDisplay();
    }, 1000);
}

/**
 * Update clock display
 */
function updateTimeDisplay() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    }
}

// ============================================================================
// WEATHER PANEL FUNCTIONS
// ============================================================================

/**
 * Update weather panel with new data
 * @param {Object} data - Weather data from API
 */
function updateWeatherPanel(data) {
    if (!data || !data.current) {
        console.warn('[AstroWatch] Invalid weather data received');
        return;
    }
    
    const current = data.current;
    
    // Update quality indicator
    const qualityValue = document.getElementById('quality-value');
    const qualityLabel = document.getElementById('quality-label');
    const qualityCircle = document.getElementById('quality-circle');
    
    if (qualityValue) {
        qualityValue.textContent = current.qualityScore;
    }
    
    if (qualityLabel) {
        qualityLabel.textContent = current.qualityLabel;
    }
    
    if (qualityCircle) {
        const color = current.qualityScore >= 80 ? '#10b981' : 
                     current.qualityScore >= 60 ? '#f59e0b' : '#ef4444';
        qualityCircle.style.stroke = color;
        qualityCircle.style.strokeDasharray = `${current.qualityScore}, 100`;
    }
    
    // Update condition cards
    const elements = {
        'temp-value': `${current.temperature}°C`,
        'humidity-value': `${current.humidity}%`,
        'wind-value': `${current.windSpeed} km/h`,
        'seeing-value': `${current.seeing}"`
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
    
    // Update weather alerts
    updateWeatherAlerts(data.alerts || []);
    
    // Update chart
    updateWeatherChart(data.history || []);
}

/**
 * Display weather alerts
 * @param {Array} alerts - Array of alert objects
 */
function updateWeatherAlerts(alerts) {
    const container = document.getElementById('weather-alerts');
    if (!container) return;
    
    if (alerts.length === 0) {
        container.innerHTML = '<div class="text-muted" style="font-size: 0.875rem; text-align: center;">No active weather alerts</div>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="weather-alert ${alert.level}">
            <div class="alert-message">${alert.message}</div>
            <div class="alert-recommendation">💡 ${alert.recommendation}</div>
        </div>
    `).join('');
}

/**
 * Initialize or update weather trend chart
 * @param {Array} history - Historical weather data
 */
function updateWeatherChart(history) {
    const ctx = document.getElementById('weatherChart');
    if (!ctx) return;
    
    const labels = history.map(h => formatTime(h.timestamp).slice(0, 5));
    
    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Temperature (°C)',
                data: history.map(h => h.temperature),
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                yAxisID: 'y',
                tension: 0.4
            },
            {
                label: 'Humidity (%)',
                data: history.map(h => h.humidity),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                yAxisID: 'y1',
                tension: 0.4
            },
            {
                label: 'Wind (km/h)',
                data: history.map(h => h.windSpeed),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                yAxisID: 'y2',
                tension: 0.4
            }
        ]
    };
    
    if (AppState.weatherChart) {
        AppState.weatherChart.data = chartData;
        AppState.weatherChart.update('none');
    } else {
        AppState.weatherChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#94a3b8',
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxTicksLimit: 6
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#ef4444'
                        },
                        title: {
                            display: true,
                            text: 'Temperature (°C)',
                            color: '#ef4444'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            color: '#3b82f6'
                        },
                        title: {
                            display: true,
                            text: 'Humidity (%)',
                            color: '#3b82f6'
                        }
                    },
                    y2: {
                        type: 'linear',
                        display: false,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            color: '#10b981'
                        }
                    }
                }
            }
        });
    }
}

// ============================================================================
// ALERTS PANEL FUNCTIONS
// ============================================================================

/**
 * Update alerts panel with new data
 * @param {Object} data - Alerts data from API
 */
function updateAlertsPanel(data) {
    if (!data || !Array.isArray(data.alerts)) {
        console.warn('[AstroWatch] Invalid alerts data received');
        return;
    }
    
    const alerts = data.alerts;
    
    // Update summary counts
    const totalCount = document.getElementById('alert-count');
    const highPriorityCount = document.getElementById('high-priority-count');
    
    if (totalCount) {
        totalCount.textContent = alerts.length;
    }
    
    if (highPriorityCount) {
        const highCount = alerts.filter(a => a.priority === 'high').length;
        highPriorityCount.textContent = highCount;
    }
    
    // Update sky map coordinates
    updateSkyMap(alerts);
    
    // Update alerts table
    updateAlertsTable(alerts);
}

/**
 * Update celestial coordinate map visualization
 * @param {Array} alerts - Array of alert objects
 */
function updateSkyMap(alerts) {
    const grid = document.getElementById('coordinate-grid');
    if (!grid) return;
    
    // Clear existing markers
    grid.innerHTML = '';
    
    // Create coordinate markers (simplified visualization)
    const maxMarkers = Math.min(alerts.length, 8);
    
    for (let i = 0; i < maxMarkers; i++) {
        const alert = alerts[i];
        const cell = document.createElement('div');
        cell.className = 'coordinate-cell';
        cell.title = `${alert.typeName}: RA ${alert.coordinates.raFormatted}, Dec ${alert.coordinates.decFormatted}`;
        
        // Size based on priority
        const size = alert.priority === 'high' ? '12px' : 
                    alert.priority === 'medium' ? '8px' : '6px';
        cell.style.width = size;
        cell.style.height = size;
        cell.style.background = alert.priority === 'high' ? '#ef4444' : 
                               alert.priority === 'medium' ? '#f59e0b' : '#10b981';
        cell.style.position = 'relative';
        cell.style.animationDelay = `${i * 0.1}s`;
        
        grid.appendChild(cell);
    }
}

/**
 * Update alerts table
 * @param {Array} alerts - Array of alert objects
 */
function updateAlertsTable(alerts) {
    const tbody = document.getElementById('alerts-tbody');
    if (!tbody) return;
    
    if (alerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-muted" style="text-align: center; padding: 2rem;">
                    No active alerts. System monitoring continues.
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = alerts.map(alert => `
        <tr>
            <td>
                <span class="priority-badge ${alert.priority}">${alert.priority}</span>
            </td>
            <td>${alert.typeName}</td>
            <td style="font-family: monospace;">${alert.coordinates.raFormatted}</td>
            <td style="font-family: monospace;">${alert.coordinates.decFormatted}</td>
            <td>${alert.photometry.magnitude}</td>
            <td>${alert.significance}σ</td>
            <td>${alert.source}</td>
            <td>${calculateAge(alert.timestamp)}</td>
        </tr>
    `).join('');
}

// ============================================================================
// INSTRUMENTS PANEL FUNCTIONS
// ============================================================================

/**
 * Update instruments panel with new data
 * @param {Object} data - Instruments data from API
 */
function updateInstrumentsPanel(data) {
    if (!data || !data.system || !data.instruments) {
        console.warn('[AstroWatch] Invalid instruments data received');
        return;
    }
    
    const system = data.system;
    const instruments = data.instruments;
    
    // Update system overview
    updateSystemOverview(system);
    
    // Update individual instrument cards
    updateInstrumentCard('telescope', instruments.telescope);
    updateInstrumentCard('camera', instruments.camera);
    updateInstrumentCard('spectrograph', instruments.spectrograph);
    updateInstrumentCard('guide_camera', instruments.guide_camera);
}

/**
 * Update system overview section
 * @param {Object} system - System status object
 */
function updateSystemOverview(system) {
    const elements = {
        'system-health': `${system.averageHealth}%`,
        'operational-count': `${system.operational}/${system.totalInstruments}`,
        'ready-status': system.readyForObserving ? 'Yes' : 'No'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
    
    // Update ready icon
    const readyIcon = document.getElementById('ready-icon');
    const readyStatus = document.getElementById('ready-status');
    
    if (readyIcon && readyStatus) {
        if (system.readyForObserving) {
            readyIcon.textContent = '✅';
            readyStatus.classList.add('ready');
            readyStatus.classList.remove('not-ready');
        } else {
            readyIcon.textContent = '⏳';
            readyStatus.classList.remove('ready');
            readyStatus.classList.add('not-ready');
        }
    }
    
    // Update header system status
    updateHeaderStatus(system.status);
}

/**
 * Update header system status indicator
 * @param {string} status - Overall system status
 */
function updateHeaderStatus(status) {
    const indicator = document.getElementById('system-status');
    const statusDot = indicator?.querySelector('.status-dot');
    const statusText = indicator?.querySelector('.status-text');
    
    if (!indicator || !statusDot || !statusText) return;
    
    const statusLabels = {
        ok: 'System Nominal',
        warning: 'System Warning',
        error: 'System Error',
        offline: 'System Offline'
    };
    
    statusDot.setAttribute('data-status', status);
    indicator.setAttribute('data-status', status);
    statusText.textContent = statusLabels[status] || 'Unknown';
}

/**
 * Update individual instrument card
 * @param {string} name - Instrument name/key
 * @param {Object} instrument - Instrument data object
 */
function updateInstrumentCard(name, instrument) {
    if (!instrument) return;
    
    const card = document.getElementById(`card-${name}`);
    if (!card) return;
    
    // Update card status
    card.setAttribute('data-status', instrument.status);
    
    // Update status badge
    const badge = card.querySelector('.status-badge');
    if (badge) {
        badge.setAttribute('data-status', instrument.status);
        badge.textContent = instrument.status;
    }
    
    // Update health bar
    const healthFill = document.getElementById(`${name}-health`);
    if (healthFill) {
        healthFill.style.width = `${instrument.health}%`;
        healthFill.setAttribute('data-health', getHealthLevel(instrument.health));
    }
    
    // Update specific instrument details
    updateInstrumentDetails(name, instrument);
    
    // Update tooltip
    updateInstrumentTooltip(name, instrument);
}

/**
 * Update instrument-specific details
 * @param {string} name - Instrument name
 * @param {Object} instrument - Instrument data
 */
function updateInstrumentDetails(name, instrument) {
    switch (name) {
        case 'telescope':
            updateElement('telescope-mode', instrument.mode);
            updateElement('telescope-health-text', `${instrument.health}%`);
            break;
            
        case 'camera':
            updateElement('camera-filter', instrument.filter.current);
            updateElement('camera-temp', `${instrument.temperature.current}°C`);
            break;
            
        case 'spectrograph':
            updateElement('spectrograph-grating', instrument.configuration.grating);
            updateElement('spectrograph-vacuum', `${instrument.vacuum.pressure} mbar`);
            break;
            
        case 'guide_camera':
            updateElement('guide-locked', instrument.guiding.locked ? 'Yes' : 'No');
            const rms = Math.sqrt(
                Math.pow(instrument.guiding.rmsX, 2) + 
                Math.pow(instrument.guiding.rmsY, 2)
            );
            updateElement('guide-rms', `${rms.toFixed(3)}"`);
            break;
    }
}

/**
 * Update instrument tooltip
 * @param {string} name - Instrument name
 * @param {Object} instrument - Instrument data
 */
function updateInstrumentTooltip(name, instrument) {
    const tooltip = document.getElementById(`tooltip-${name}`);
    if (!tooltip) return;
    
    const issues = instrument.issues && instrument.issues.length > 0 
        ? instrument.issues.join('; ') 
        : 'No issues detected';
    
    tooltip.innerHTML = `
        <div><strong>ID:</strong> ${instrument.id}</div>
        <div><strong>Type:</strong> ${instrument.type}</div>
        <div><strong>Health:</strong> ${instrument.health}%</div>
        <div><strong>Issues:</strong> ${issues}</div>
        <div><strong>Last Update:</strong> ${formatTime(instrument.lastUpdate)}</div>
    `;
}

/**
 * Helper to safely update element text content
 * @param {string} id - Element ID
 * @param {string} value - New text content
 */
function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ============================================================================
// DATA FETCHING
// ============================================================================

/**
 * Fetch data from endpoint with error handling and retries
 * @param {string} endpoint - API endpoint URL
 * @param {string} type - Data type for logging
 * @param {Function} callback - Success callback function
 */
async function fetchData(endpoint, type, callback) {
    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success === false) {
            throw new Error(data.message || 'API returned error');
        }
        
        AppState.retryCounts[type] = 0;
        callback(data.data || data);
        
        return true;
        
    } catch (error) {
        AppState.retryCounts[type]++;
        console.error(`[AstroWatch] ${type} fetch error:`, error.message);
        
        if (AppState.retryCounts[type] >= AppState.maxRetries) {
            console.warn(`[AstroWatch] Max retries exceeded for ${type}, using fallback`);
            handleFallback(type);
            AppState.retryCounts[type] = 0;
        }
        
        return false;
    }
}

/**
 * Handle fallback when API fails
 * @param {string} type - Data type
 */
function handleFallback(type) {
    console.log(`[AstroWatch] Using cached/fallback data for ${type}`);
    // Fallback is handled by the mock data in PHP endpoints
}

/**
 * Fetch weather data
 */
async function fetchWeather() {
    const success = await fetchData(
        ASTROWATCH_CONFIG.endpoints.weather,
        'weather',
        updateWeatherPanel
    );
    
    if (success) {
        AppState.lastUpdate = new Date();
        updateLastUpdateTime();
    }
}

/**
 * Fetch alerts data
 */
async function fetchAlerts() {
    await fetchData(
        ASTROWATCH_CONFIG.endpoints.alerts,
        'alerts',
        updateAlertsPanel
    );
}

/**
 * Fetch instruments data
 */
async function fetchInstruments() {
    await fetchData(
        ASTROWATCH_CONFIG.endpoints.instruments,
        'instruments',
        updateInstrumentsPanel
    );
}

/**
 * Refresh all data
 */
async function refreshAll() {
    console.log('[AstroWatch] Manual refresh triggered');
    await Promise.all([
        fetchWeather(),
        fetchAlerts(),
        fetchInstruments()
    ]);
}

/**
 * Update last update time display
 */
function updateLastUpdateTime() {
    const element = document.getElementById('last-update');
    if (element && AppState.lastUpdate) {
        element.textContent = `Last update: ${formatTime(AppState.lastUpdate.toISOString())}`;
    }
}

// ============================================================================
// CONNECTION MONITORING
// ============================================================================

/**
 * Update connection status display
 */
function updateConnectionStatus() {
    const bar = document.getElementById('connection-bar');
    const text = bar?.querySelector('.connection-text');
    
    if (!bar || !text) return;
    
    if (AppState.connectionStatus === 'connected') {
        bar.style.background = 'var(--color-bg-tertiary)';
        text.textContent = 'Connected';
    } else {
        bar.style.background = 'rgba(239, 68, 68, 0.2)';
        text.textContent = 'Disconnected - Retrying...';
    }
}

/**
 * Monitor connection status
 */
function startConnectionMonitor() {
    window.addEventListener('online', () => {
        AppState.connectionStatus = 'connected';
        updateConnectionStatus();
        refreshAll();
    });
    
    window.addEventListener('offline', () => {
        AppState.connectionStatus = 'disconnected';
        updateConnectionStatus();
    });
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize dashboard with initial data
 */
function initializeDashboard() {
    console.log('[AstroWatch] Initializing dashboard...');
    
    // Load initial data from config (server-side rendered)
    const initialData = ASTROWATCH_CONFIG.initialData;
    
    if (initialData.weather) {
        updateWeatherPanel(initialData.weather);
    }
    
    if (initialData.alerts) {
        updateAlertsPanel({ alerts: initialData.alerts });
    }
    
    if (initialData.instruments) {
        updateInstrumentsPanel({ 
            system: { 
                averageHealth: 95, 
                totalInstruments: 5, 
                operational: 5,
                status: 'ok',
                readyForObserving: true
            },
            instruments: initialData.instruments 
        });
    }
    
    // Start polling timers
    startPolling();
    
    // Start countdown timers
    startTimerCountdown();
    
    // Monitor connection
    startConnectionMonitor();
    
    console.log('[AstroWatch] Dashboard initialized successfully');
}

/**
 * Start data polling intervals
 */
function startPolling() {
    // Clear existing timers
    Object.values(AppState.pollingTimers).forEach(timer => {
        if (timer) clearInterval(timer);
    });
    
    // Start weather polling
    AppState.pollingTimers.weather = setInterval(
        fetchWeather,
        ASTROWATCH_CONFIG.pollingIntervals.weather
    );
    
    // Start alerts polling
    AppState.pollingTimers.alerts = setInterval(
        fetchAlerts,
        ASTROWATCH_CONFIG.pollingIntervals.alerts
    );
    
    // Start instruments polling
    AppState.pollingTimers.instruments = setInterval(
        fetchInstruments,
        ASTROWATCH_CONFIG.pollingIntervals.instruments
    );
    
    console.log('[AstroWatch] Polling started');
}

/**
 * Toggle fullscreen mode
 */
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error(`[AstroWatch] Fullscreen error: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
}

// Make functions globally available
window.refreshAll = refreshAll;
window.toggleFullscreen = toggleFullscreen;

// ============================================================================
// DOM READY
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Wait for Chart.js to load
    if (typeof Chart === 'undefined') {
        console.error('[AstroWatch] Chart.js not loaded');
        return;
    }
    
    initializeDashboard();
});

// Handle page visibility changes (pause polling when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('[AstroWatch] Tab hidden, reducing polling frequency');
        // Could reduce polling frequency here if needed
    } else {
        console.log('[AstroWatch] Tab visible, refreshing data');
        refreshAll();
    }
});

// Graceful shutdown on page unload
window.addEventListener('beforeunload', () => {
    Object.values(AppState.pollingTimers).forEach(timer => {
        if (timer) clearInterval(timer);
    });
});
