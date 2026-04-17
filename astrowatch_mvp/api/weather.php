<?php
/**
 * AstroWatch Dashboard - Weather API Endpoint
 * 
 * Returns observatory environmental conditions: seeing, humidity, wind, temperature.
 * Provides historical data for trend charts.
 * 
 * @package AstroWatch
 * @version 1.0.0
 */

declare(strict_types=1);

require_once __DIR__ . '/../config.php';

setJsonHeaders();

/**
 * Generate mock weather data with realistic patterns
 * Simulates observatory environmental monitoring station readings
 * 
 * @param int $historyPoints Number of historical data points to generate
 * @return array Weather data object
 */
function generateMockWeather(int $historyPoints = 24): array
{
    // Base values with diurnal variation simulation
    $hour = (int)date('H');
    $tempBase = 10 + 5 * sin(deg2rad($hour - 6) * 15); // Cooler at night
    
    seededRandom(0, 1, MOCK_DATA_SEED + $hour);
    
    // Current conditions
    $currentTemp = round($tempBase + seededRandom(-2, 2), 1);
    $currentHumidity = round(seededRandom(15, 45) + (10 - abs($tempBase - 10)), 1);
    $currentWind = round(seededRandom(5, 25) + seededRandom(-3, 3), 1);
    $currentSeeing = round(seededRandom(0.6, 2.0) + ($currentWind > 20 ? 0.3 : 0), 2);
    $currentPressure = round(750 + seededRandom(-5, 5), 1);
    $cloudCover = round(seededRandom(0, 30), 1);
    
    // Determine conditions status
    $conditions = 'Clear';
    if ($cloudCover > 50) {
        $conditions = 'Cloudy';
    } elseif ($cloudCover > 20) {
        $conditions = 'Partly Cloudy';
    } elseif ($currentHumidity > 70) {
        $conditions = 'Humid';
    }
    
    // Generate historical data for trends
    $history = [];
    for ($i = $historyPoints; $i >= 0; $i--) {
        $timestamp = time() - ($i * 3600);
        $histHour = (int)date('H', $timestamp);
        
        $histTempBase = 10 + 5 * sin(deg2rad($histHour - 6) * 15);
        $histVariation = seededRandom(-3, 3);
        
        $history[] = [
            'timestamp' => formatTimestamp($timestamp),
            'temperature' => round($histTempBase + $histVariation, 1),
            'humidity' => round(seededRandom(15, 50), 1),
            'windSpeed' => round(seededRandom(5, 30), 1),
            'seeing' => round(seededRandom(0.5, 2.5), 2),
            'pressure' => round(750 + seededRandom(-8, 8), 1),
        ];
    }
    
    // Calculate statistics
    $temperatures = array_column($history, 'temperature');
    $humidities = array_column($history, 'humidity');
    $windSpeeds = array_column($history, 'windSpeed');
    $seeings = array_column($history, 'seeing');
    
    $stats = [
        'temperature' => [
            'min' => min($temperatures),
            'max' => max($temperatures),
            'avg' => round(array_sum($temperatures) / count($temperatures), 1),
        ],
        'humidity' => [
            'min' => min($humidities),
            'max' => max($humidities),
            'avg' => round(array_sum($humidities) / count($humidities), 1),
        ],
        'windSpeed' => [
            'min' => min($windSpeeds),
            'max' => max($windSpeeds),
            'avg' => round(array_sum($windSpeeds) / count($windSpeeds), 1),
        ],
        'seeing' => [
            'min' => min($seeings),
            'max' => max($seeings),
            'avg' => round(array_sum($seeings) / count($seeings), 2),
        ],
    ];
    
    // Determine observing conditions quality
    $qualityScore = 100;
    $qualityFactors = [];
    
    if ($currentSeeing > MAX_SEEING) {
        $qualityScore -= 30;
        $qualityFactors[] = 'Poor seeing';
    } elseif ($currentSeeing > 1.5) {
        $qualityScore -= 15;
        $qualityFactors[] = 'Moderate seeing';
    }
    
    if ($currentWind > MAX_WIND_SPEED) {
        $qualityScore -= 40;
        $qualityFactors[] = 'High wind';
    } elseif ($currentWind > 30) {
        $qualityScore -= 15;
        $qualityFactors[] = 'Moderate wind';
    }
    
    if ($currentHumidity > MAX_HUMIDITY) {
        $qualityScore -= 35;
        $qualityFactors[] = 'High humidity';
    } elseif ($currentHumidity > 60) {
        $qualityScore -= 10;
        $qualityFactors[] = 'Elevated humidity';
    }
    
    if ($cloudCover > 50) {
        $qualityScore -= 50;
        $qualityFactors[] = 'Cloud cover';
    }
    
    $qualityScore = max(0, $qualityScore);
    
    $qualityLabel = 'Excellent';
    if ($qualityScore < 80) {
        $qualityLabel = 'Good';
    }
    if ($qualityScore < 60) {
        $qualityLabel = 'Fair';
    }
    if ($qualityScore < 40) {
        $qualityLabel = 'Poor';
    }
    if ($qualityScore < 20) {
        $qualityLabel = 'Unsuitable';
    }
    
    return [
        'current' => [
            'temperature' => $currentTemp,
            'humidity' => $currentHumidity,
            'windSpeed' => $currentWind,
            'windDirection' => random_int(0, 359),
            'seeing' => $currentSeeing,
            'pressure' => $currentPressure,
            'cloudCover' => $cloudCover,
            'dewPoint' => round($currentTemp - ((100 - $currentHumidity) / 5), 1),
            'conditions' => $conditions,
            'qualityScore' => $qualityScore,
            'qualityLabel' => $qualityLabel,
            'qualityFactors' => $qualityFactors,
        ],
        'history' => $history,
        'statistics' => $stats,
        'thresholds' => [
            'maxWindSpeed' => MAX_WIND_SPEED,
            'maxHumidity' => MAX_HUMIDITY,
            'minTemperature' => MIN_TEMPERATURE,
            'maxTemperature' => MAX_TEMPERATURE,
            'maxSeeing' => MAX_SEEING,
        ],
        'alerts' => generateWeatherAlerts($currentTemp, $currentHumidity, $currentWind, $currentSeeing, $cloudCover),
    ];
}

/**
 * Generate weather alerts based on current conditions
 * 
 * @param float $temp Temperature in °C
 * @param float $humidity Humidity percentage
 * @param float $wind Wind speed in km/h
 * @param float $seeing Seeing in arcseconds
 * @param float $cloudCover Cloud cover percentage
 * @return array Array of active alerts
 */
function generateWeatherAlerts(float $temp, float $humidity, float $wind, float $seeing, float $cloudCover): array
{
    $alerts = [];
    
    if ($wind > MAX_WIND_SPEED) {
        $alerts[] = [
            'level' => 'critical',
            'type' => 'high_wind',
            'message' => "Wind speed ({$wind} km/h) exceeds safe limit (" . MAX_WIND_SPEED . " km/h)",
            'recommendation' => 'Close telescope dome immediately',
        ];
    } elseif ($wind > MAX_WIND_SPEED * 0.8) {
        $alerts[] = [
            'level' => 'warning',
            'type' => 'elevated_wind',
            'message' => "Wind speed approaching limit ({$wind} km/h)",
            'recommendation' => 'Monitor conditions closely',
        ];
    }
    
    if ($humidity > MAX_HUMIDITY) {
        $alerts[] = [
            'level' => 'critical',
            'type' => 'high_humidity',
            'message' => "Humidity ({$humidity}%) exceeds dew point threshold",
            'recommendation' => 'Activate mirror heating, consider closing dome',
        ];
    } elseif ($humidity > MAX_HUMIDITY * 0.9) {
        $alerts[] = [
            'level' => 'warning',
            'type' => 'elevated_humidity',
            'message' => "Humidity rising ({$humidity}%)",
            'recommendation' => 'Prepare dew prevention systems',
        ];
    }
    
    if ($temp < MIN_TEMPERATURE) {
        $alerts[] = [
            'level' => 'warning',
            'type' => 'low_temperature',
            'message' => "Temperature ({$temp}°C) below operating minimum",
            'recommendation' => 'Verify instrument thermal systems',
        ];
    }
    
    if ($temp > MAX_TEMPERATURE) {
        $alerts[] = [
            'level' => 'warning',
            'type' => 'high_temperature',
            'message' => "Temperature ({$temp}°C) above operating maximum",
            'recommendation' => 'Monitor cooling systems',
        ];
    }
    
    if ($seeing > MAX_SEEING) {
        $alerts[] = [
            'level' => 'info',
            'type' => 'poor_seeing',
            'message' => "Seeing ({$seeing}\") exceeds optimal threshold",
            'recommendation' => 'Consider postponing high-resolution observations',
        ];
    }
    
    if ($cloudCover > 70) {
        $alerts[] = [
            'level' => 'warning',
            'type' => 'cloud_cover',
            'message' => "Significant cloud cover ({$cloudCover}%)",
            'recommendation' => 'Monitor satellite imagery',
        ];
    }
    
    return $alerts;
}

/**
 * Attempt to fetch real weather data from external API (placeholder)
 * 
 * @return array|null Real weather data or null if unavailable
 */
function fetchRealWeather(): ?array
{
    if (!ENABLE_EXTERNAL_APIS || empty(WEATHER_API_URL)) {
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
        
        $response = file_get_contents(WEATHER_API_URL, false, $context);
        
        if ($response === false) {
            throw new Exception('Failed to fetch weather from external API');
        }
        
        return json_decode($response, true);
        
    } catch (Exception $e) {
        logError("Weather API error: " . $e->getMessage());
        return null;
    }
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

try {
    $weatherData = fetchRealWeather() ?? generateMockWeather(24);
    
    $response = [
        'success' => true,
        'timestamp' => formatTimestamp(),
        'observatory' => OBS_NAME,
        'location' => [
            'latitude' => OBS_LATITUDE,
            'longitude' => OBS_LONGITUDE,
            'altitude' => OBS_ALTITUDE,
        ],
        'data' => $weatherData,
        'metadata' => [
            'dataSource' => fetchRealWeather() !== null ? 'external_api' : 'mock_generator',
            'nextUpdate' => POLLING_WEATHER_INTERVAL / 1000,
            'units' => [
                'temperature' => '°C',
                'humidity' => '%',
                'windSpeed' => 'km/h',
                'seeing' => 'arcseconds',
                'pressure' => 'hPa',
                'cloudCover' => '%',
            ],
        ],
    ];
    
    jsonResponse($response);
    
} catch (Exception $e) {
    logError("Critical weather error: " . $e->getMessage());
    
    jsonResponse([
        'success' => false,
        'error' => 'Failed to retrieve weather data',
        'message' => 'Using fallback data',
        'timestamp' => formatTimestamp(),
        'data' => generateMockWeather(0),
    ], 500);
}
