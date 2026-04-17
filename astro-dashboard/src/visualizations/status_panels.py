"""
Status Panels - Creates status indicator cards for instruments and weather.

Generates HTML divs with traffic light indicators for monitoring.
"""

from typing import Dict, Any, List
import dash_bootstrap_components as dbc
from dash import html


def create_weather_panel(weather_data: Dict[str, Any]) -> dbc.Card:
    """
    Create weather conditions panel.
    
    Args:
        weather_data: Dictionary with weather measurements.
        
    Returns:
        Dash Bootstrap Card component.
    """
    if not weather_data:
        return dbc.Card([
            dbc.CardHeader("Weather Conditions"),
            dbc.CardBody(html.P("No data available", className="text-muted"))
        ], className="mb-3")
    
    # Status indicator function
    def get_status_indicator(status: str) -> str:
        indicators = {
            "good": "🟢",
            "ok": "🟢",
            "warning": "🟡",
            "alert": "🔴",
            "bad": "🔴"
        }
        return indicators.get(status, "⚪")
    
    seeing_indicator = get_status_indicator(weather_data.get("seeing_status", "unknown"))
    humidity_indicator = get_status_indicator(weather_data.get("humidity_status", "unknown"))
    wind_indicator = get_status_indicator(weather_data.get("wind_status", "unknown"))
    
    return dbc.Card([
        dbc.CardHeader([
            html.Span("🌤️ Weather Conditions", className="me-2"),
            html.Small(id="weather-timestamp", 
                      className="text-muted",
                      children=f"Updated: {weather_data.get('timestamp', 'N/A')[:19]}")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span(seeing_indicator, className="me-2"),
                        html.Strong("Seeing: "),
                        html.Span(f"{weather_data.get('seeing', 0):.2f}\"")
                    ], className="mb-2")
                ]),
                dbc.Col([
                    html.Div([
                        html.Span(humidity_indicator, className="me-2"),
                        html.Strong("Humidity: "),
                        html.Span(f"{weather_data.get('humidity', 0):.1f}%")
                    ], className="mb-2")
                ]),
                dbc.Col([
                    html.Div([
                        html.Span(wind_indicator, className="me-2"),
                        html.Strong("Wind: "),
                        html.Span(f"{weather_data.get('wind_speed', 0):.1f} km/h")
                    ], className="mb-2")
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Strong("Temperature: "),
                        html.Span(f"{weather_data.get('temperature', 0):.1f}°C")
                    ])
                ]),
                dbc.Col([
                    html.Div([
                        html.Strong("Cloud Cover: "),
                        html.Span(f"{weather_data.get('cloud_cover', 0):.1f}%")
                    ])
                ])
            ])
        ])
    ], className="mb-3")


def create_instrument_status_panel(instruments: Dict[str, Dict[str, Any]]) -> dbc.Card:
    """
    Create instrument status panel.
    
    Args:
        instruments: Dictionary mapping instrument names to status dicts.
        
    Returns:
        Dash Bootstrap Card component.
    """
    if not instruments:
        return dbc.Card([
            dbc.CardHeader("Instrument Status"),
            dbc.CardBody(html.P("No data available", className="text-muted"))
        ], className="mb-3")
    
    def get_health_indicator(health: str) -> str:
        indicators = {
            "good": "🟢",
            "warning": "🟡",
            "critical": "🔴"
        }
        return indicators.get(health, "⚪")
    
    # Build instrument cards
    instrument_cards = []
    for name, status in instruments.items():
        health_indicator = get_health_indicator(status.get("health", "unknown"))
        
        # Key metrics based on instrument type
        metrics = []
        inst_type = status.get("type", "")
        
        if inst_type == "CCD":
            metrics.append(f"CCD Temp: {status.get('ccd_temperature', 0):.1f}°C")
            metrics.append(f"Shutter: {status.get('shutter', 'N/A')}")
            metrics.append(f"Filter: {status.get('filter_wheel', 'N/A')}")
        elif inst_type == "GUIDER":
            metrics.append(f"Lock: {status.get('lock_status', 'N/A')}")
            metrics.append(f"RMS: {status.get('rms_error', 0):.2f}\"")
        elif inst_type == "SPECTROGRAPH":
            metrics.append(f"Grating: {status.get('grating', 'N/A')}")
            metrics.append(f"Slit: {status.get('slit_width', 'N/A')}")
        elif inst_type == "MOUNT":
            metrics.append(f"Tracking: {status.get('tracking_rate', 0):.3f}")
            if status.get("wind_shake"):
                metrics.append(html.Span(" ⚠️ Wind Shake", className="text-warning"))
        
        instrument_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Span(health_indicator, className="me-2"),
                            html.Strong(status.get("name", name)),
                            html.Small(f" ({inst_type})", className="text-muted ms-2")
                        ], className="mb-2"),
                        html.Div([
                            html.Small(m, className="d-block") for m in metrics
                        ])
                    ])
                ], className="mb-2")
            ], xs=6, md=4, lg=3)
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.Span("🔭 Instrument Status", className="me-2"),
            html.Small(id="instrument-timestamp", className="text-muted")
        ]),
        dbc.CardBody([
            dbc.Row(instrument_cards)
        ])
    ], className="mb-3")


def create_alert_summary_panel(event_stats: Dict[str, Any]) -> dbc.Card:
    """
    Create alert summary statistics panel.
    
    Args:
        event_stats: Dictionary with alert statistics.
        
    Returns:
        Dash Bootstrap Card component.
    """
    if not event_stats or event_stats.get("count", 0) == 0:
        return dbc.Card([
            dbc.CardHeader("Alert Summary"),
            dbc.CardBody(html.P("No alerts", className="text-muted"))
        ], className="mb-3")
    
    by_type = event_stats.get("by_type", {})
    
    # Create type badges
    type_badges = []
    for t, count in by_type.items():
        badge_color = {
            "GRB": "danger",
            "SN": "warning",
            "Asteroid": "info",
            "Unknown": "secondary"
        }.get(t, "primary")
        
        type_badges.append(
            dbc.Badge(f"{t}: {count}", color=badge_color, className="me-1 mb-1")
        )
    
    return dbc.Card([
        dbc.CardHeader("🚨 Alert Summary"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H3(str(event_stats.get("count", 0)), className="text-primary"),
                    html.Small("Total Alerts", className="text-muted")
                ], width=3),
                dbc.Col([
                    html.H3(f"{event_stats.get('avg_magnitude', 0):.1f}", className="text-info"),
                    html.Small("Avg Magnitude", className="text-muted")
                ], width=3),
                dbc.Col([
                    html.H3(f"{event_stats.get('avg_age_hours', 0):.1f}h", className="text-warning"),
                    html.Small("Avg Age", className="text-muted")
                ], width=3),
                dbc.Col([
                    html.H3(f"{event_stats.get('newest_event_hours', 0):.1f}h", className="text-success"),
                    html.Small("Newest Event", className="text-muted")
                ], width=3)
            ], className="mb-3"),
            html.Div(type_badges)
        ])
    ], className="mb-3")


def create_observing_conditions_card(weather: Dict[str, Any], 
                                     instruments: Dict[str, Dict[str, Any]]) -> dbc.Card:
    """
    Create overall observing conditions card.
    
    Args:
        weather: Weather data dictionary.
        instruments: Instrument status dictionary.
        
    Returns:
        Dash Bootstrap Card component with go/no-go recommendation.
    """
    # Determine overall status
    can_observe = True
    reasons = []
    
    # Check weather
    if weather:
        if weather.get("humidity_status") == "alert":
            can_observe = False
            reasons.append("High humidity")
        if weather.get("wind_status") == "alert":
            can_observe = False
            reasons.append("High wind")
        if weather.get("cloud_cover", 0) > 80:
            can_observe = False
            reasons.append("Heavy cloud cover")
        if weather.get("seeing_status") == "bad":
            reasons.append("Poor seeing")
    
    # Check instruments
    if instruments:
        for name, status in instruments.items():
            if status.get("health") == "critical":
                can_observe = False
                reasons.append(f"{status.get('name', name)} critical")
            elif status.get("health") == "warning":
                reasons.append(f"{status.get('name', name)} warning")
    
    # Set status indicator
    if can_observe and not any("poor" in r or "warning" in r for r in reasons):
        status_color = "success"
        status_text = "GOOD TO OBSERVE"
        status_icon = "✅"
    elif can_observe:
        status_color = "warning"
        status_text = "CAUTION"
        status_icon = "⚠️"
    else:
        status_color = "danger"
        status_text = "NOT RECOMMENDED"
        status_icon = "❌"
    
    return dbc.Card([
        dbc.CardHeader("📋 Observing Conditions"),
        dbc.CardBody([
            html.Div([
                html.Span(status_icon, className="me-2"),
                html.H4(status_text, className=f"text-{status_color}", style={"display": "inline"}),
            ], className="mb-3"),
            html.Ul([
                html.Li(r, className="text-muted") for r in reasons
            ]) if reasons else html.P("All systems nominal", className="text-success")
        ])
    ], className="mb-3")
