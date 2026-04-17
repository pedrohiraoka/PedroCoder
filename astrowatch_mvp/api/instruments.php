<?php
/**
 * AstroWatch Dashboard - Instruments API Endpoint
 * 
 * Returns status of observatory instruments: telescope, camera, spectrograph.
 * Provides operational state, health metrics, and configuration data.
 * 
 * @package AstroWatch
 * @version 1.0.0
 */

declare(strict_types=1);

require_once __DIR__ . '/../config.php';

setJsonHeaders();

/**
 * Generate mock instrument status data
 * Simulates real-time instrument monitoring system
 * 
 * @return array Instrument status objects
 */
function generateMockInstruments(): array
{
    $instruments = [];
    
    // Telescope status
    $telescopeStatus = STATUS_OK;
    $telescopeIssues = [];
    
    seededRandom(0, 1, MOCK_DATA_SEED + intval(time() / 60));
    $telescopeHealth = round(seededRandom(85, 100), 1);
    
    if ($telescopeHealth < 90) {
        $telescopeStatus = STATUS_WARNING;
        $telescopeIssues[] = 'Encoder calibration recommended';
    }
    
    $telescopeMode = ['Tracking', 'Slew', 'Parking', 'Calibration'][array_rand(range(0, 3))];
    $targetName = ['NGC 1234', 'M31', 'SN 2024abc', 'Sky Flat', 'Dark Frame'][array_rand(range(0, 4))];
    
    $instruments['telescope'] = [
        'id' => 'TEL_001',
        'name' => 'Main Telescope',
        'type' => 'Ritchey-Chrétien',
        'aperture' => '2.0m',
        'focalLength' => '20.0m',
        'status' => $telescopeStatus,
        'health' => $telescopeHealth,
        'mode' => $telescopeMode,
        'operational' => $telescopeStatus !== STATUS_ERROR && $telescopeStatus !== STATUS_OFFLINE,
        'coordinates' => [
            'ra' => round(seededRandom(0, 24), 4),
            'dec' => round(seededRandom(-90, 90), 4),
            'azimuth' => round(seededRandom(0, 360), 2),
            'altitude' => round(seededRandom(0, 90), 2),
        ],
        'tracking' => [
            'enabled' => $telescopeMode === 'Tracking',
            'rate' => 'Sidereal',
            'guiding' => seededRandom(0, 1) > 0.2,
            'rmsError' => round(seededRandom(0.05, 0.3), 3),
        ],
        'dome' => [
            'shutterOpen' => $telescopeMode !== 'Parking',
            'rotationEnabled' => true,
            'ventilationOpen' => true,
        ],
        'metrics' => [
            'uptime' => random_int(100, 500) . 'h',
            'observationsTonight' => random_int(5, 25),
            'lastMaintenance' => date('Y-m-d', strtotime('-' . random_int(5, 30) . ' days')),
            'nextMaintenance' => date('Y-m-d', strtotime('+' . random_int(10, 60) . ' days')),
        ],
        'issues' => $telescopeIssues,
        'lastUpdate' => formatTimestamp(),
    ];
    
    // Camera status
    $cameraStatus = STATUS_OK;
    $cameraIssues = [];
    
    $cameraHealth = round(seededRandom(88, 100), 1);
    $ccdTemp = round(seededRandom(-100, -80), 1); // CCD temperature in °C
    $ccdSetpoint = -90;
    
    if (abs($ccdTemp - $ccdSetpoint) > 5) {
        $cameraStatus = STATUS_WARNING;
        $cameraIssues[] = 'CCD temperature deviation';
    }
    
    $filterWheel = ['g', 'r', 'i', 'z', 'u', 'Clear'][array_rand(range(0, 5))];
    $shutterState = seededRandom(0, 1) > 0.3 ? 'Open' : 'Closed';
    
    $instruments['camera'] = [
        'id' => 'CAM_001',
        'name' => 'Wide-Field Camera',
        'type' => 'CCD',
        'sensor' => 'e2v CCD44-82',
        'resolution' => '10560 x 10560',
        'pixelSize' => '9μm',
        'fieldOfView' => '2.2° x 2.2°',
        'status' => $cameraStatus,
        'health' => $cameraHealth,
        'operational' => $cameraStatus !== STATUS_ERROR && $cameraStatus !== STATUS_OFFLINE,
        'temperature' => [
            'current' => $ccdTemp,
            'setpoint' => $ccdSetpoint,
            'stability' => round(seededRandom(0.01, 0.1), 2),
            'coolerPower' => round(seededRandom(30, 70), 1),
        ],
        'filter' => [
            'current' => $filterWheel,
            'wheelPosition' => array_search($filterWheel, ['g', 'r', 'i', 'z', 'u', 'Clear']) + 1,
            'totalFilters' => 6,
        ],
        'shutter' => [
            'state' => $shutterState,
            'cycles' => random_int(1000, 5000),
        ],
        'readout' => [
            'gain' => round(seededRandom(0.5, 2.0), 2),
            'readNoise' => round(seededRandom(3, 6), 1),
            'bitDepth' => 16,
        ],
        'metrics' => [
            'exposuresTonight' => random_int(20, 100),
            'totalExposures' => random_int(5000, 20000),
            'lastCalibration' => date('Y-m-d', strtotime('-' . random_int(1, 7) . ' days')),
        ],
        'issues' => $cameraIssues,
        'lastUpdate' => formatTimestamp(),
    ];
    
    // Spectrograph status
    $spectrographStatus = STATUS_OK;
    $spectrographIssues = [];
    
    $spectrographHealth = round(seededRandom(90, 100), 1);
    $vacuumPressure = round(seededRandom(0.001, 0.01), 4); // mbar
    
    if ($vacuumPressure > 0.005) {
        $spectrographStatus = STATUS_WARNING;
        $spectrographIssues[] = 'Vacuum pressure elevated';
    }
    
    $grating = ['300V', '600V', '1200V', 'Mirror'][array_rand(range(0, 3))];
    $slitWidth = ['0.5"', '1.0"', '2.0"', '5.0"'][array_rand(range(0, 3))];
    
    $instruments['spectrograph'] = [
        'id' => 'SPEC_001',
        'name' => 'Optical Spectrograph',
        'type' => 'Long-slit',
        'wavelengthRange' => '350-900 nm',
        'resolution' => 'R ~ 1000-5000',
        'status' => $spectrographStatus,
        'health' => $spectrographHealth,
        'operational' => $spectrographStatus !== STATUS_ERROR && $spectrographStatus !== STATUS_OFFLINE,
        'configuration' => [
            'grating' => $grating,
            'slitWidth' => $slitWidth,
            'centralWavelength' => round(seededRandom(500, 700), 0),
            'tiltAngle' => round(seededRandom(0, 45), 2),
        ],
        'detector' => [
            'type' => 'CCD',
            'temperature' => round(seededRandom(-110, -90), 1),
            'binning' => '1x1',
        ],
        'vacuum' => [
            'pressure' => $vacuumPressure,
            'threshold' => 0.01,
            'pumpRunning' => $vacuumPressure > 0.003,
        ],
        'calibration' => [
            'arcLampAvailable' => true,
            'flatFieldAvailable' => true,
            'lastArc' => date('Y-m-d H:i', strtotime('-' . random_int(1, 12) . ' hours')),
            'lastFlat' => date('Y-m-d H:i', strtotime('-' . random_int(1, 24) . ' hours')),
        ],
        'metrics' => [
            'spectraTonight' => random_int(5, 30),
            'totalSpectra' => random_int(2000, 10000),
            'lastMaintenance' => date('Y-m-d', strtotime('-' . random_int(10, 60) . ' days')),
        ],
        'issues' => $spectrographIssues,
        'lastUpdate' => formatTimestamp(),
    ];
    
    // Weather station (auxiliary instrument)
    $weatherStationStatus = STATUS_OK;
    
    $instruments['weather_station'] = [
        'id' => 'WX_001',
        'name' => 'Weather Station',
        'type' => 'Environmental Monitor',
        'status' => $weatherStationStatus,
        'health' => round(seededRandom(95, 100), 1),
        'operational' => true,
        'sensors' => [
            'anemometer' => ['status' => STATUS_OK, 'lastCheck' => date('Y-m-d')],
            'hygrometer' => ['status' => STATUS_OK, 'lastCheck' => date('Y-m-d')],
            'thermometer' => ['status' => STATUS_OK, 'lastCheck' => date('Y-m-d')],
            'cloudSensor' => ['status' => seededRandom(0, 1) > 0.1 ? STATUS_OK : STATUS_WARNING, 'lastCheck' => date('Y-m-d')],
            'seeingMonitor' => ['status' => STATUS_OK, 'lastCheck' => date('Y-m-d')],
        ],
        'lastUpdate' => formatTimestamp(),
    ];
    
    // Guide camera
    $guideCameraStatus = seededRandom(0, 1) > 0.05 ? STATUS_OK : STATUS_WARNING;
    
    $instruments['guide_camera'] = [
        'id' => 'GUIDE_001',
        'name' => 'Autoguider',
        'type' => 'Guide Camera',
        'status' => $guideCameraStatus,
        'health' => round(seededRandom(90, 100), 1),
        'operational' => $guideCameraStatus !== STATUS_ERROR && $guideCameraStatus !== STATUS_OFFLINE,
        'guiding' => [
            'locked' => seededRandom(0, 1) > 0.1,
            'starMagnitude' => round(seededRandom(8, 14), 1),
            'rmsX' => round(seededRandom(0.05, 0.3), 3),
            'rmsY' => round(seededRandom(0.05, 0.3), 3),
            'corrections' => random_int(100, 500),
        ],
        'lastUpdate' => formatTimestamp(),
    ];
    
    return $instruments;
}

/**
 * Calculate overall system status
 * 
 * @param array $instruments All instrument data
 * @return array Overall status summary
 */
function calculateSystemStatus(array $instruments): array
{
    $totalHealth = 0;
    $count = 0;
    $criticalCount = 0;
    $warningCount = 0;
    $offlineCount = 0;
    
    foreach ($instruments as $instrument) {
        $count++;
        $totalHealth += $instrument['health'];
        
        switch ($instrument['status']) {
            case STATUS_ERROR:
                $criticalCount++;
                break;
            case STATUS_WARNING:
                $warningCount++;
                break;
            case STATUS_OFFLINE:
                $offlineCount++;
                break;
        }
    }
    
    $avgHealth = $count > 0 ? round($totalHealth / $count, 1) : 0;
    
    $overallStatus = STATUS_OK;
    if ($criticalCount > 0 || $offlineCount > 0) {
        $overallStatus = STATUS_ERROR;
    } elseif ($warningCount > 0) {
        $overallStatus = STATUS_WARNING;
    }
    
    $operationalCount = $count - $offlineCount - $criticalCount;
    $readyForObserving = $overallStatus === STATUS_OK && $avgHealth >= 90;
    
    return [
        'status' => $overallStatus,
        'averageHealth' => $avgHealth,
        'totalInstruments' => $count,
        'operational' => $operationalCount,
        'warnings' => $warningCount,
        'critical' => $criticalCount,
        'offline' => $offlineCount,
        'readyForObserving' => $readyForObserving,
        'summary' => generateStatusSummary($overallStatus, $avgHealth, $readyForObserving),
    ];
}

/**
 * Generate human-readable status summary
 * 
 * @param string $status Overall status
 * @param float $health Average health percentage
 * @param bool $ready Ready for observing
 * @return string Summary text
 */
function generateStatusSummary(string $status, float $health, bool $ready): string
{
    if (!$ready) {
        if ($status === STATUS_ERROR) {
            return 'System requires attention. Critical issues detected.';
        }
        if ($status === STATUS_WARNING) {
            return 'System operational with warnings. Review recommended.';
        }
        return 'System not ready for observations.';
    }
    
    if ($health >= 98) {
        return 'All systems nominal. Excellent conditions for observing.';
    }
    if ($health >= 95) {
        return 'Systems healthy. Ready for observations.';
    }
    return 'Systems operational. Minor issues present.';
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

try {
    $instruments = generateMockInstruments();
    $systemStatus = calculateSystemStatus($instruments);
    
    $response = [
        'success' => true,
        'timestamp' => formatTimestamp(),
        'observatory' => OBS_NAME,
        'system' => $systemStatus,
        'instruments' => $instruments,
        'metadata' => [
            'dataSource' => 'mock_generator',
            'nextUpdate' => POLLING_INSTRUMENTS_INTERVAL / 1000,
            'statusColors' => [
                STATUS_OK => '#10b981',
                STATUS_WARNING => '#f59e0b',
                STATUS_ERROR => '#ef4444',
                STATUS_OFFLINE => '#6b7280',
            ],
        ],
    ];
    
    jsonResponse($response);
    
} catch (Exception $e) {
    logError("Critical instruments error: " . $e->getMessage());
    
    jsonResponse([
        'success' => false,
        'error' => 'Failed to retrieve instrument status',
        'message' => $e->getMessage(),
        'timestamp' => formatTimestamp(),
        'system' => [
            'status' => STATUS_ERROR,
            'averageHealth' => 0,
        ],
        'instruments' => [],
    ], 500);
}
