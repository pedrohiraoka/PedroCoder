<?php
/**
 * AstroWatch Dashboard - Main Entry Point
 * 
 * Primary dashboard interface with real-time astronomical data monitoring.
 * Loads initial data and provides structure for JavaScript polling.
 * 
 * @package AstroWatch
 * @version 1.0.0
 */

declare(strict_types=1);

require_once __DIR__ . '/config.php';

// Get initial data for server-side rendering
$initialAlerts = [];
$initialWeather = null;
$initialInstruments = null;

try {
    $alertsData = json_decode(file_get_contents(__DIR__ . '/api/alerts.php'), true);
    $initialAlerts = $alertsData['alerts'] ?? [];
} catch (Exception $e) {
    logError("Failed to load initial alerts: " . $e->getMessage());
}

try {
    $weatherData = json_decode(file_get_contents(__DIR__ . '/api/weather.php'), true);
    $initialWeather = $weatherData['data'] ?? null;
} catch (Exception $e) {
    logError("Failed to load initial weather: " . $e->getMessage());
}

try {
    $instrumentsData = json_decode(file_get_contents(__DIR__ . '/api/instruments.php'), true);
    $initialInstruments = $instrumentsData['instruments'] ?? null;
} catch (Exception $e) {
    logError("Failed to load initial instruments: " . $e->getMessage());
}

$currentDateTime = new DateTime();
$currentDateTime->setTimezone(new DateTimeZone(OBS_TIMEZONE));
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="description" content="Real-time astronomical observatory monitoring dashboard">
    <meta name="theme-color" content="#0f172a">
    
    <title>AstroWatch Dashboard - <?= htmlspecialchars(OBS_NAME) ?></title>
    
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js" integrity="sha384-v7MkD0pP1hIwgGLJKJHbJ5v9dCZOLJvpjLNKQzYVPEfnqWnLvDLfFCL1fT6rUuKT" crossorigin="anonymous"></script>
    
    <!-- Custom Styles -->
    <link rel="stylesheet" href="assets/css/style.css">
    
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔭</text></svg>">
</head>
<body>
    <!-- Header -->
    <header class="dashboard-header">
        <div class="header-content">
            <div class="logo-section">
                <span class="logo-icon">🔭</span>
                <div class="logo-text">
                    <h1>AstroWatch Dashboard</h1>
                    <p class="observatory-name"><?= htmlspecialchars(OBS_NAME) ?></p>
                </div>
            </div>
            
            <div class="header-info">
                <div class="datetime-display">
                    <span id="current-date"><?= $currentDateTime->format('l, F j, Y') ?></span>
                    <span id="current-time" class="time-large"><?= $currentDateTime->format('H:i:s') ?></span>
                    <span class="timezone-label"><?= OBS_TIMEZONE ?></span>
                </div>
                
                <div class="system-status-indicator" id="system-status" data-status="ok">
                    <span class="status-dot"></span>
                    <span class="status-text">System Nominal</span>
                </div>
            </div>
        </div>
        
        <!-- Connection Status Bar -->
        <div class="connection-bar" id="connection-bar">
            <span class="connection-icon">📡</span>
            <span class="connection-text">Connected</span>
            <span class="last-update" id="last-update">Last update: --:--:--</span>
        </div>
    </header>
    
    <!-- Main Dashboard Grid -->
    <main class="dashboard-grid">
        
        <!-- Weather & Conditions Panel -->
        <section class="panel weather-panel" id="weather-panel">
            <div class="panel-header">
                <h2>
                    <span class="panel-icon">🌤️</span>
                    Observatory Conditions
                </h2>
                <span class="update-timer" id="weather-timer">30s</span>
            </div>
            
            <div class="panel-content">
                <!-- Quality Indicator -->
                <div class="quality-indicator" id="quality-indicator">
                    <div class="quality-ring">
                        <svg viewBox="0 0 36 36" class="circular-chart">
                            <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <path class="circle" id="quality-circle" stroke-dasharray="100, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        </svg>
                        <div class="quality-value" id="quality-value">--</div>
                    </div>
                    <div class="quality-label" id="quality-label">Loading...</div>
                </div>
                
                <!-- Current Conditions Grid -->
                <div class="conditions-grid">
                    <div class="condition-card">
                        <span class="condition-icon">🌡️</span>
                        <div class="condition-info">
                            <span class="condition-label">Temperature</span>
                            <span class="condition-value" id="temp-value">--°C</span>
                        </div>
                    </div>
                    
                    <div class="condition-card">
                        <span class="condition-icon">💧</span>
                        <div class="condition-info">
                            <span class="condition-label">Humidity</span>
                            <span class="condition-value" id="humidity-value">--%</span>
                        </div>
                    </div>
                    
                    <div class="condition-card">
                        <span class="condition-icon">💨</span>
                        <div class="condition-info">
                            <span class="condition-label">Wind</span>
                            <span class="condition-value" id="wind-value">-- km/h</span>
                        </div>
                    </div>
                    
                    <div class="condition-card">
                        <span class="condition-icon">✨</span>
                        <div class="condition-info">
                            <span class="condition-label">Seeing</span>
                            <span class="condition-value" id="seeing-value">--"</span>
                        </div>
                    </div>
                </div>
                
                <!-- Weather Alerts -->
                <div class="weather-alerts" id="weather-alerts">
                    <!-- Alerts populated by JS -->
                </div>
                
                <!-- Trend Charts -->
                <div class="charts-container">
                    <div class="chart-wrapper">
                        <canvas id="weatherChart"></canvas>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Transient Alerts Panel -->
        <section class="panel alerts-panel" id="alerts-panel">
            <div class="panel-header">
                <h2>
                    <span class="panel-icon">⚡</span>
                    Transient Alerts
                </h2>
                <span class="update-timer" id="alerts-timer">60s</span>
            </div>
            
            <div class="panel-content">
                <!-- Alert Summary -->
                <div class="alert-summary">
                    <div class="summary-stat">
                        <span class="stat-count" id="alert-count">0</span>
                        <span class="stat-label">Active Alerts</span>
                    </div>
                    <div class="summary-stat high-priority">
                        <span class="stat-count" id="high-priority-count">0</span>
                        <span class="stat-label">High Priority</span>
                    </div>
                </div>
                
                <!-- Sky Map Placeholder -->
                <div class="sky-map" id="sky-map">
                    <div class="map-overlay">
                        <span class="map-label">Celestial Coordinates</span>
                        <div class="coordinate-grid" id="coordinate-grid">
                            <!-- RA/Dec markers populated by JS -->
                        </div>
                    </div>
                </div>
                
                <!-- Alerts Table -->
                <div class="alerts-table-container">
                    <table class="alerts-table" id="alerts-table">
                        <thead>
                            <tr>
                                <th>Priority</th>
                                <th>Type</th>
                                <th>RA (J2000)</th>
                                <th>Dec (J2000)</th>
                                <th>Mag</th>
                                <th>Significance</th>
                                <th>Source</th>
                                <th>Age</th>
                            </tr>
                        </thead>
                        <tbody id="alerts-tbody">
                            <!-- Alerts populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
        
        <!-- Instruments Status Panel -->
        <section class="panel instruments-panel" id="instruments-panel">
            <div class="panel-header">
                <h2>
                    <span class="panel-icon">⚙️</span>
                    Instrument Status
                </h2>
                <span class="update-timer" id="instruments-timer">15s</span>
            </div>
            
            <div class="panel-content">
                <!-- System Overview -->
                <div class="system-overview" id="system-overview">
                    <div class="overview-stat">
                        <span class="stat-icon">📊</span>
                        <span class="stat-value" id="system-health">--%</span>
                        <span class="stat-label">System Health</span>
                    </div>
                    <div class="overview-stat">
                        <span class="stat-icon">✅</span>
                        <span class="stat-value" id="operational-count">--/--</span>
                        <span class="stat-label">Operational</span>
                    </div>
                    <div class="overview-stat ready-status">
                        <span class="stat-icon" id="ready-icon">⏳</span>
                        <span class="stat-value" id="ready-status">--</span>
                        <span class="stat-label">Ready for Observing</span>
                    </div>
                </div>
                
                <!-- Instrument Cards -->
                <div class="instruments-grid" id="instruments-grid">
                    <!-- Telescope Card -->
                    <div class="instrument-card" id="card-telescope" data-status="loading">
                        <div class="card-header">
                            <span class="card-icon">🔭</span>
                            <span class="card-title">Telescope</span>
                            <span class="status-badge" data-status="loading">Loading</span>
                        </div>
                        <div class="card-body">
                            <div class="health-bar">
                                <div class="health-fill" id="telescope-health"></div>
                            </div>
                            <div class="card-details">
                                <span class="detail-item">Mode: <strong id="telescope-mode">--</strong></span>
                                <span class="detail-item">Health: <strong id="telescope-health-text">--%</strong></span>
                            </div>
                        </div>
                        <div class="card-tooltip" id="tooltip-telescope">
                            <!-- Tooltip content populated by JS -->
                        </div>
                    </div>
                    
                    <!-- Camera Card -->
                    <div class="instrument-card" id="card-camera" data-status="loading">
                        <div class="card-header">
                            <span class="card-icon">📷</span>
                            <span class="card-title">Camera</span>
                            <span class="status-badge" data-status="loading">Loading</span>
                        </div>
                        <div class="card-body">
                            <div class="health-bar">
                                <div class="health-fill" id="camera-health"></div>
                            </div>
                            <div class="card-details">
                                <span class="detail-item">Filter: <strong id="camera-filter">--</strong></span>
                                <span class="detail-item">CCD Temp: <strong id="camera-temp">--°C</strong></span>
                            </div>
                        </div>
                        <div class="card-tooltip" id="tooltip-camera">
                            <!-- Tooltip content populated by JS -->
                        </div>
                    </div>
                    
                    <!-- Spectrograph Card -->
                    <div class="instrument-card" id="card-spectrograph" data-status="loading">
                        <div class="card-header">
                            <span class="card-icon">🌈</span>
                            <span class="card-title">Spectrograph</span>
                            <span class="status-badge" data-status="loading">Loading</span>
                        </div>
                        <div class="card-body">
                            <div class="health-bar">
                                <div class="health-fill" id="spectrograph-health"></div>
                            </div>
                            <div class="card-details">
                                <span class="detail-item">Grating: <strong id="spectrograph-grating">--</strong></span>
                                <span class="detail-item">Vacuum: <strong id="spectrograph-vacuum">--</strong></span>
                            </div>
                        </div>
                        <div class="card-tooltip" id="tooltip-spectrograph">
                            <!-- Tooltip content populated by JS -->
                        </div>
                    </div>
                    
                    <!-- Guide Camera Card -->
                    <div class="instrument-card" id="card-guide_camera" data-status="loading">
                        <div class="card-header">
                            <span class="card-icon">🎯</span>
                            <span class="card-title">Autoguider</span>
                            <span class="status-badge" data-status="loading">Loading</span>
                        </div>
                        <div class="card-body">
                            <div class="health-bar">
                                <div class="health-fill" id="guide_camera-health"></div>
                            </div>
                            <div class="card-details">
                                <span class="detail-item">Locked: <strong id="guide-locked">--</strong></span>
                                <span class="detail-item">RMS: <strong id="guide-rms">--"</strong></span>
                            </div>
                        </div>
                        <div class="card-tooltip" id="tooltip-guide_camera">
                            <!-- Tooltip content populated by JS -->
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
    </main>
    
    <!-- Footer -->
    <footer class="dashboard-footer">
        <div class="footer-content">
            <div class="footer-info">
                <span>AstroWatch Dashboard v1.0.0</span>
                <span class="separator">•</span>
                <span>Location: <?= OBS_LATITUDE ?>°, <?= OBS_LONGITUDE ?>° (Alt: <?= OBS_ALTITUDE ?>m)</span>
            </div>
            <div class="footer-links">
                <a href="#" onclick="refreshAll(); return false;">↻ Refresh Now</a>
                <span class="separator">•</span>
                <a href="#" onclick="toggleFullscreen(); return false;">⛶ Fullscreen</a>
            </div>
        </div>
    </footer>
    
    <!-- Configuration Data for JavaScript -->
    <script>
        window.ASTROWATCH_CONFIG = {
            endpoints: {
                alerts: 'api/alerts.php',
                weather: 'api/weather.php',
                instruments: 'api/instruments.php'
            },
            pollingIntervals: {
                alerts: <?= POLLING_ALERTS_INTERVAL ?>,
                weather: <?= POLLING_WEATHER_INTERVAL ?>,
                instruments: <?= POLLING_INSTRUMENTS_INTERVAL ?>
            },
            observatory: {
                name: '<?= addslashes(OBS_NAME) ?>',
                latitude: <?= OBS_LATITUDE ?>,
                longitude: <?= OBS_LONGITUDE ?>,
                altitude: <?= OBS_ALTITUDE ?>,
                timezone: '<?= OBS_TIMEZONE ?>'
            },
            thresholds: {
                maxWindSpeed: <?= MAX_WIND_SPEED ?>,
                maxHumidity: <?= MAX_HUMIDITY ?>,
                minTemperature: <?= MIN_TEMPERATURE ?>,
                maxTemperature: <?= MAX_TEMPERATURE ?>,
                maxSeeing: <?= MAX_SEEING ?>
            },
            statusColors: {
                ok: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444',
                offline: '#6b7280'
            },
            initialData: {
                alerts: <?= json_encode($initialAlerts, JSON_UNESCAPED_UNICODE) ?>,
                weather: <?= json_encode($initialWeather, JSON_UNESCAPED_UNICODE) ?>,
                instruments: <?= json_encode($initialInstruments, JSON_UNESCAPED_UNICODE) ?>
            }
        };
    </script>
    
    <!-- Dashboard JavaScript -->
    <script src="assets/js/dashboard.js"></script>
</body>
</html>
