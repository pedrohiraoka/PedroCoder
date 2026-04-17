<?php
/**
 * AstroWatch Dashboard - Configuration File
 * 
 * Central configuration for coordinates, intervals, limits and operational parameters.
 * 
 * @package AstroWatch
 * @version 1.0.0
 */

declare(strict_types=1);

// Prevent direct access
if (!defined('ASTROWATCH_CONFIG')) {
    define('ASTROWATCH_CONFIG', true);
}

// ============================================================================
// OBSERVATORY CONFIGURATION
// ============================================================================

/**
 * Observatory coordinates (example: Cerro Paranal)
 */
define('OBS_LATITUDE', -24.6275);      // Decimal degrees
define('OBS_LONGITUDE', -70.4042);     // Decimal degrees
define('OBS_ALTITUDE', 2635);          // Meters above sea level
define('OBS_NAME', 'Cerro Paranal Observatory');
define('OBS_TIMEZONE', 'America/Santiago');

// ============================================================================
// POLLING INTERVALS (milliseconds)
// ============================================================================

define('POLLING_ALERTS_INTERVAL', 60000);        // 60 seconds
define('POLLING_WEATHER_INTERVAL', 30000);       // 30 seconds
define('POLLING_INSTRUMENTS_INTERVAL', 15000);   // 15 seconds

// ============================================================================
// OPERATIONAL LIMITS
// ============================================================================

/**
 * Weather thresholds for safe operations
 */
define('MAX_WIND_SPEED', 60);           // km/h - Maximum safe wind speed
define('MAX_HUMIDITY', 85);             // % - Maximum humidity before dew risk
define('MIN_TEMPERATURE', -10);         // °C - Minimum operating temperature
define('MAX_TEMPERATURE', 40);          // °C - Maximum operating temperature
define('MAX_SEEING', 2.5);              // arcseconds - Poor seeing threshold

/**
 * Instrument status levels
 */
define('STATUS_OK', 'ok');
define('STATUS_WARNING', 'warning');
define('STATUS_ERROR', 'error');
define('STATUS_OFFLINE', 'offline');

// ============================================================================
// API CONFIGURATION
// ============================================================================

/**
 * External API endpoints (optional - mock data used if unavailable)
 */
define('VOEVENT_API_URL', 'https://voevent.net/');
define('WEATHER_API_URL', '');          // Leave empty to use mock data
define('ENABLE_EXTERNAL_APIS', false);  // Set true to attempt real API calls

// ============================================================================
// CACHE & PERFORMANCE
// ============================================================================

define('CACHE_CONTROL_MAX_AGE', 30);    // Seconds for Cache-Control header
define('JSON_PRETTY_PRINT', true);      // Pretty print JSON responses

// ============================================================================
// MOCK DATA GENERATION
// ============================================================================

/**
 * Seed for reproducible mock data (change for different random sequences)
 */
define('MOCK_DATA_SEED', 42);

// ============================================================================
// ERROR HANDLING
// ============================================================================

error_reporting(E_ALL);
ini_set('display_errors', '0');         // Don't display errors in production
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/error.log');

// Timezone configuration
date_default_timezone_set(OBS_TIMEZONE);

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Set JSON response headers with cache control
 * 
 * @param int $maxAge Cache max age in seconds
 * @return void
 */
function setJsonHeaders(int $maxAge = CACHE_CONTROL_MAX_AGE): void
{
    header('Content-Type: application/json; charset=utf-8');
    header("Cache-Control: public, max-age={$maxAge}");
    header('X-Content-Type-Options: nosniff');
    header('Access-Control-Allow-Origin: *');
}

/**
 * Output JSON response with error handling
 * 
 * @param array $data Response data
 * @param int $statusCode HTTP status code
 * @return void
 */
function jsonResponse(array $data, int $statusCode = 200): void
{
    http_response_code($statusCode);
    
    $options = JSON_PRETTY_PRINT ? JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE : JSON_UNESCAPED_UNICODE;
    echo json_encode($data, $options);
    exit;
}

/**
 * Generate seeded random number for consistent mock data
 * 
 * @param float $min Minimum value
 * @param float $max Maximum value
 * @param int|null $seed Optional seed
 * @return float
 */
function seededRandom(float $min, float $max, ?int $seed = null): float
{
    static $state = null;
    
    if ($seed !== null) {
        $state = $seed;
    }
    
    if ($state === null) {
        $state = time();
    }
    
    $state = ($state * 1103515245 + 12345) & 0x7fffffff;
    $normalized = $state / 0x7fffffff;
    
    return $min + ($normalized * ($max - $min));
}

/**
 * Format timestamp for API responses
 * 
 * @param int|null $timestamp Unix timestamp
 * @return string ISO 8601 formatted datetime
 */
function formatTimestamp(?int $timestamp = null): string
{
    return date('c', $timestamp ?? time());
}

/**
 * Log error message
 * 
 * @param string $message Error message
 * @param string $level Error level
 * @return void
 */
function logError(string $message, string $level = 'ERROR'): void
{
    error_log("[{$level}] " . date('Y-m-d H:i:s') . " - {$message}");
}
