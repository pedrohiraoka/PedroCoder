<?php
/**
 * AstroWatch Dashboard - Alerts API Endpoint
 * 
 * Returns transient alerts (VOEvent-style) from simulated or real sources.
 * Provides celestial coordinates (RA/Dec) and alert metadata.
 * 
 * @package AstroWatch
 * @version 1.0.0
 */

declare(strict_types=1);

require_once __DIR__ . '/../config.php';

setJsonHeaders();

/**
 * Generate mock transient alerts
 * Simulates VOEvent network alerts for various astronomical transients
 * 
 * @return array Array of alert objects
 */
function generateMockAlerts(): array
{
    $alertTypes = [
        ['type' => 'GRB', 'name' => 'Gamma-Ray Burst', 'priority' => 'high'],
        ['type' => 'SN', 'name' => 'Supernova Candidate', 'priority' => 'medium'],
        ['type' => 'AGN', 'name' => 'AGN Flare', 'priority' => 'low'],
        ['type' => 'TDE', 'name' => 'Tidal Disruption Event', 'priority' => 'high'],
        ['type' => 'CV', 'name' => 'Cataclysmic Variable', 'priority' => 'low'],
        ['type' => 'ASTERIOD', 'name' => 'Near-Earth Asteroid', 'priority' => 'medium'],
        ['type' => 'COMET', 'name' => 'Comet Outburst', 'priority' => 'low'],
        ['type' => 'MICROLENS', 'name' => 'Microlensing Event', 'priority' => 'medium'],
    ];
    
    $alerts = [];
    $numAlerts = random_int(3, 8);
    
    seededRandom(0, 1, MOCK_DATA_SEED + intval(time() / 300)); // Change every 5 minutes
    
    for ($i = 0; $i < $numAlerts; $i++) {
        $alertType = $alertTypes[array_rand($alertTypes)];
        
        // Generate realistic RA (0-24h) and Dec (-90 to +90 deg)
        $ra = seededRandom(0, 24);
        $dec = seededRandom(-90, 90);
        
        // Generate magnitude (brighter objects have lower values)
        $magnitude = round(seededRandom(12, 22), 2);
        
        // Calculate significance (higher = more significant detection)
        $significance = round(seededRandom(3, 8), 1);
        
        // Generate alert ID
        $alertId = sprintf(
            'IVO_%s_%s',
            strtoupper($alertType['type']),
            date('YmdHis') . str_pad((string)$i, 3, '0', STR_PAD_LEFT)
        );
        
        $alerts[] = [
            'id' => $alertId,
            'type' => $alertType['type'],
            'typeName' => $alertType['name'],
            'priority' => $alertType['priority'],
            'coordinates' => [
                'ra' => round($ra, 4),
                'raFormatted' => sprintf('%02dh %02dm %.1fs', floor($ra), floor(($ra * 60) % 60), (($ra * 3600) % 60)),
                'dec' => round($dec, 4),
                'decFormatted' => sprintf('%+02d° %02d\' %.1f"', floor(abs($dec)), floor((abs($dec) * 60) % 60), ((abs($dec) * 3600) % 60)),
                'galactic_l' => round(seededRandom(0, 360), 2),
                'galactic_b' => round(seededRandom(-90, 90), 2),
            ],
            'photometry' => [
                'magnitude' => $magnitude,
                'band' => ['g', 'r', 'i', 'z'][array_rand(range(0, 3))],
                'error' => round(seededRandom(0.01, 0.15), 3),
            ],
            'significance' => $significance,
            'timestamp' => formatTimestamp(time() - random_int(0, 3600)),
            'source' => ['ZTF', 'ATLAS', 'Gaia', 'Swift', 'Fermi'][array_rand(range(0, 4))],
            'url' => 'https://example.org/alert/' . $alertId,
            'remarks' => generateAlertRemarks($alertType['type']),
        ];
    }
    
    // Sort by priority and significance
    usort($alerts, function($a, $b) {
        $priorityOrder = ['high' => 0, 'medium' => 1, 'low' => 2];
        if ($priorityOrder[$a['priority']] !== $priorityOrder[$b['priority']]) {
            return $priorityOrder[$a['priority']] - $priorityOrder[$b['priority']];
        }
        return $b['significance'] - $a['significance'];
    });
    
    return $alerts;
}

/**
 * Generate remarks based on alert type
 * 
 * @param string $type Alert type code
 * @return string Remark text
 */
function generateAlertRemarks(string $type): string
{
    $remarks = [
        'GRB' => 'Rapid follow-up recommended. High-energy counterpart detected.',
        'SN' => 'Spectroscopic confirmation pending. Rising light curve observed.',
        'AGN' => 'Unusual variability pattern. Multi-wavelength campaign suggested.',
        'TDE' => 'Candidate tidal disruption event. X-ray emission detected.',
        'CV' => 'Dwarf nova outburst in progress. Regular monitoring advised.',
        'ASTERIOD' => 'Moving object detected. Orbital parameters being calculated.',
        'COMET' => 'Cometary activity increase. Dust tail development observed.',
        'MICROLENS' => 'Peak magnification expected within 24 hours.',
    ];
    
    return $remarks[$type] ?? 'Further observations recommended.';
}

/**
 * Attempt to fetch real alerts from external API (placeholder)
 * Currently returns null to trigger mock data fallback
 * 
 * @return array|null Real alerts or null if unavailable
 */
function fetchRealAlerts(): ?array
{
    if (!ENABLE_EXTERNAL_APIS || empty(VOEVENT_API_URL)) {
        return null;
    }
    
    try {
        $context = stream_context_create([
            'http' => [
                'method' => 'GET',
                'timeout' => 5,
                'header' => "User-Agent: AstroWatch-Dashboard/1.0\r\n"
            ]
        ]);
        
        $response = file_get_contents(VOEVENT_API_URL, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to fetch alerts from external API');
        }
        
        // Parse real API response here (implementation depends on API format)
        // For now, return null to use mock data
        return null;
        
    } catch (Exception $e) {
        logError("Alerts API error: " . $e->getMessage());
        return null;
    }
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

try {
    // Try to get real alerts, fall back to mock data
    $alerts = fetchRealAlerts() ?? generateMockAlerts();
    
    $response = [
        'success' => true,
        'timestamp' => formatTimestamp(),
        'observatory' => OBS_NAME,
        'count' => count($alerts),
        'alerts' => $alerts,
        'metadata' => [
            'dataSource' => fetchRealAlerts() !== null ? 'external_api' : 'mock_generator',
            'nextUpdate' => POLLING_ALERTS_INTERVAL / 1000,
            'coordinateSystem' => 'J2000.0',
        ],
    ];
    
    jsonResponse($response);
    
} catch (Exception $e) {
    logError("Critical alerts error: " . $e->getMessage());
    
    jsonResponse([
        'success' => false,
        'error' => 'Failed to retrieve alerts',
        'message' => 'Using fallback data',
        'timestamp' => formatTimestamp(),
        'alerts' => [],
        'count' => 0,
    ], 500);
}
