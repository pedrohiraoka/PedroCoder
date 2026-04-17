"""
AstroWatch & Triage Dashboard - Main Application Entry Point.

A unified dashboard for real-time astronomical alert monitoring,
instrument status tracking, and interactive data quality triage.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

import config
from src.utils.logger import get_logger, setup_root_logger
from src.data_fetchers.voevent_fetcher import VOEventFetcher
from src.data_fetchers.weather_fetcher import WeatherFetcher
from src.data_fetchers.instrument_status import InstrumentStatus
from src.data_fetchers.fits_loader import FITSCatalogLoader
from src.processors.alert_parser import AlertParser
from src.processors.quality_metrics import QualityMetrics
from src.visualizations.alert_map import (
    create_alert_sky_map, 
    create_alert_type_pie_chart,
    create_magnitude_histogram,
    create_alert_time_series
)
from src.visualizations.status_panels import (
    create_weather_panel,
    create_instrument_status_panel,
    create_alert_summary_panel,
    create_observing_conditions_card
)
from src.visualizations.linked_views import (
    create_catalog_scatter,
    create_magnitude_redshift_plot,
    create_fwhm_ellipticity_plot,
    get_selected_data,
    calculate_selection_statistics,
    export_selected_targets
)

# Setup logging
setup_root_logger()
logger = get_logger(__name__)

# Initialize data fetchers
voevent_fetcher = VOEventFetcher(use_mock=True)
weather_fetcher = WeatherFetcher(use_mock=True)
instrument_fetcher = InstrumentStatus(use_mock=True)
fits_loader = FITSCatalogLoader(use_mock=True)
alert_parser = AlertParser()
quality_metrics = QualityMetrics()

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "AstroWatch & Triage Dashboard"
server = app.server

# Global state storage (in production, use Redis or similar)
global_state = {
    "events": [],
    "parsed_events": [],
    "weather": {},
    "instruments": {},
    "catalog_data": None,
    "selected_ids": set(),
    "last_update": None
}


def serve_layout():
    """Serve the main layout."""
    return html.Div([
        # Store components for state management
        dcc.Store(id='store-events', data=[]),
        dcc.Store(id='store-catalog', data=None),
        dcc.Store(id='store-selected-ids', data=[]),
        dcc.Store(id='store-filter-type', data='ALL'),
        
        # Header
        html.Header([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H1([
                            html.Span("🔭 ", className="me-2"),
                            "AstroWatch & Triage Dashboard"
                        ], className="text-primary mb-1"),
                        html.P([
                            "Real-time alert monitoring • Instrument status • Data quality triage | ",
                            html.Span(id="current-time", className="text-muted")
                        ], className="lead mb-0")
                    ])
                ])
            ], fluid=True)
        ], style={"background": "#0d1117", "padding": "20px 0", "border-bottom": "1px solid #30363d"}),
        
        # Main content
        dbc.Container([
            # Monitoring Section
            html.Section([
                html.H3("📊 Real-Time Monitoring", className="mt-4 mb-3"),
                
                # Top row: Observing conditions and alerts
                dbc.Row([
                    dbc.Col(create_observing_conditions_card({}, {}), md=4),
                    dbc.Col(create_alert_summary_panel({"count": 0}), md=8)
                ]),
                
                # Weather and instruments
                dbc.Row([
                    dbc.Col(create_weather_panel({}), md=6),
                    dbc.Col(create_instrument_status_panel({}), md=6)
                ]),
                
                # Alert maps and charts
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='alert-sky-map',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        )
                    ], md=8),
                    dbc.Col([
                        dcc.Graph(
                            id='alert-type-pie',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        ),
                        dcc.Graph(
                            id='magnitude-histogram',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        )
                    ], md=4)
                ]),
                
                # Alert time series
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='alert-time-series',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        )
                    ])
                ])
            ]),
            
            # Data Triage Section
            html.Section([
                html.H3("🔬 Data Quality Triage", className="mt-5 mb-3"),
                
                # Catalog info and controls
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Strong("Catalog: ", className="me-2"),
                            html.Span(id="catalog-info", className="text-muted")
                        ]),
                        html.Div([
                            html.Strong("Objects: ", className="me-2"),
                            html.Span(id="catalog-count", className="text-info")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.Div([
                            dbc.Button("🔄 Refresh Catalog", id="btn-refresh-catalog", 
                                     color="primary", size="sm", className="me-2"),
                            dbc.Button("📥 Export Selected", id="btn-export", 
                                     color="success", size="sm")
                        ])
                    ], md=6, className="text-end")
                ], className="mb-3"),
                
                # Linked views
                dbc.Row([
                    dbc.Col([
                        html.H5("Sky Distribution", className="mb-2"),
                        dcc.Graph(
                            id='catalog-sky-map',
                            figure=go.Figure().add_annotation(text="Loading catalog...", showarrow=False),
                            config={'responsive': True}
                        )
                    ], md=6),
                    dbc.Col([
                        html.H5("Magnitude vs Redshift", className="mb-2"),
                        dcc.Graph(
                            id='mag-redshift-plot',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        )
                    ], md=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H5("Image Quality: FWHM vs Ellipticity", className="mb-2"),
                        dcc.Graph(
                            id='fwhm-ellip-plot',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        )
                    ], md=6),
                    dbc.Col([
                        html.H5("Selection Statistics", className="mb-2"),
                        html.Div(id="selection-stats", className="bg-dark p-3 rounded")
                    ], md=6)
                ]),
                
                # Quality metrics summary
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(
                            id='quality-summary',
                            figure=go.Figure().add_annotation(text="Loading...", showarrow=False),
                            config={'responsive': True}
                        )
                    ])
                ])
            ]),
            
            # Event Log
            html.Section([
                html.H3("📝 Event Log", className="mt-5 mb-3"),
                html.Div(
                    id="event-log",
                    className="bg-dark p-3 rounded",
                    style={"maxHeight": "200px", "overflowY": "auto"}
                )
            ]),
            
            # Footer
            html.Footer([
                html.Hr(className="my-4"),
                dbc.Row([
                    dbc.Col([
                        html.Small([
                            "AstroWatch & Triage Dashboard v1.0 | ",
                            "Running on ", html.Code("127.0.0.1:8050"), " | ",
                            html.A("Documentation", href="#", className="text-muted")
                        ], className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Small([
                            "Last Update: ", html.Span(id="last-update-time", className="text-info")
                        ], className="text-muted text-end")
                    ], md=6)
                ])
            ], className="mt-5 pb-4")
        ], fluid=True),
        
        # Interval components for polling
        dcc.Interval(id='interval-voevent', interval=config.VOEVENT_POLL_INTERVAL * 1000, n_intervals=0),
        dcc.Interval(id='interval-weather', interval=config.WEATHER_POLL_INTERVAL * 1000, n_intervals=0),
        dcc.Interval(id='interval-instrument', interval=config.INSTRUMENT_POLL_INTERVAL * 1000, n_intervals=0),
        dcc.Interval(id='interval-time', interval=1000, n_intervals=0)  # Update clock every second
    ], className="dash-dark")


app.layout = serve_layout


# Callbacks for real-time updates
@app.callback(
    [Output('store-events', 'data'),
     Output('alert-sky-map', 'figure'),
     Output('alert-type-pie', 'figure'),
     Output('magnitude-histogram', 'figure'),
     Output('alert-time-series', 'figure'),
     Output('alert-summary-panel', 'children', allow_duplicate=True),
     Output('event-log', 'children', allow_duplicate=True)],
    Input('interval-voevent', 'n_intervals'),
    prevent_initial_call='initial_duplicate'
)
def update_alerts(n):
    """Update alert data and visualizations."""
    logger.info(f"Updating alerts (poll #{n})")
    
    # Fetch new events
    events = voevent_fetcher.fetch_events(max_events=50)
    parsed_events = alert_parser.parse_events(events)
    
    global_state["events"] = events
    global_state["parsed_events"] = parsed_events
    global_state["last_update"] = datetime.utcnow()
    
    # Create visualizations
    sky_map = create_alert_sky_map(parsed_events)
    pie_chart = create_alert_type_pie_chart(parsed_events)
    mag_hist = create_magnitude_histogram(parsed_events)
    time_series = create_alert_time_series(parsed_events)
    
    # Get statistics
    stats = voevent_fetcher.get_statistics(parsed_events)
    alert_panel = create_alert_summary_panel(stats)
    
    # Create log entries
    log_entries = []
    for event in parsed_events[:10]:  # Show last 10
        priority_color = {"1": "danger", "2": "warning", "3": "info"}.get(
            str(event["priority"]), "secondary")
        log_entries.append(
            dbc.Badge(
                f"[{event['type']}] {event['id']} - Mag: {event['magnitude']:.1f}",
                color=priority_color,
                className="me-1 mb-1"
            )
        )
    
    return (parsed_events, sky_map, pie_chart, mag_hist, time_series, 
            alert_panel, log_entries)


@app.callback(
    [Output('weather-panel', 'children', allow_duplicate=True),
     Output('observing-conditions', 'children', allow_duplicate=True)],
    Input('interval-weather', 'n_intervals'),
    prevent_initial_call='initial_duplicate'
)
def update_weather(n):
    """Update weather conditions."""
    logger.debug(f"Updating weather (poll #{n})")
    
    weather = weather_fetcher.fetch_conditions()
    global_state["weather"] = weather
    
    weather_panel = create_weather_panel(weather)
    conditions_card = create_observing_conditions_card(
        weather, global_state.get("instruments", {})
    )
    
    return weather_panel, conditions_card


@app.callback(
    [Output('instrument-panel', 'children', allow_duplicate=True),
     Output('observing-conditions', 'children', allow_duplicate=True)],
    Input('interval-instrument', 'n_intervals'),
    prevent_initial_call='initial_duplicate'
)
def update_instruments(n):
    """Update instrument status."""
    logger.debug(f"Updating instruments (poll #{n})")
    
    instruments = instrument_fetcher.fetch_all_status()
    global_state["instruments"] = instruments
    
    instrument_panel = create_instrument_status_panel(instruments)
    conditions_card = create_observing_conditions_card(
        global_state.get("weather", {}), instruments
    )
    
    return instrument_panel, conditions_card


@app.callback(
    Output('current-time', 'children'),
    Input('interval-time', 'n_intervals')
)
def update_clock(n):
    """Update current time display."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


@app.callback(
    Output('last-update-time', 'children'),
    Input('store-events', 'data')
)
def update_last_update(data):
    """Update last update timestamp."""
    if global_state["last_update"]:
        return global_state["last_update"].strftime("%Y-%m-%d %H:%M:%S")
    return "Never"


# Catalog loading and linked views callbacks
@app.callback(
    [Output('catalog-sky-map', 'figure'),
     Output('mag-redshift-plot', 'figure'),
     Output('fwhm-ellip-plot', 'figure'),
     Output('catalog-count', 'children'),
     Output('catalog-info', 'children'),
     Output('quality-summary', 'figure')],
    [Input('btn-refresh-catalog', 'n_clicks'),
     Input('store-selected-ids', 'data')],
    prevent_initial_call=False
)
def update_catalog_views(n_clicks, selected_ids):
    """Update catalog visualizations with linked brushing."""
    logger.info("Updating catalog views")
    
    # Load catalog data
    df = fits_loader.read_all(max_rows=config.MAX_OBJECTS_IN_MEMORY)
    global_state["catalog_data"] = df
    
    # Convert selected IDs from list to set
    selected_set = set(selected_ids) if selected_ids else set()
    global_state["selected_ids"] = selected_set
    
    # Create visualizations
    sky_fig = create_catalog_scatter(df, selected_ids=selected_set)
    mag_z_fig = create_magnitude_redshift_plot(df, selected_ids=selected_set)
    fwhm_ellip_fig = create_fwhm_ellipticity_plot(df, selected_ids=selected_set)
    
    # Catalog info
    info = fits_loader.get_catalog_info()
    count_text = f"{len(df):,} objects"
    info_text = f"{info['filename']} | {info['n_objects']:,} total"
    
    # Quality summary
    quality_stats = quality_metrics.analyze_catalog_quality(df)
    quality_fig = go.Figure()
    
    if quality_stats:
        quality_fig.add_trace(go.Bar(
            x=["FWHM", "Ellipticity", "SNR"],
            y=[
                quality_stats.get("fwhm", {}).get("median", 0),
                quality_stats.get("ellipticity", {}).get("median", 0),
                quality_stats.get("snr", {}).get("median", 0) / 10
            ],
            marker_color=config.DARK_THEME['accent']
        ))
        quality_fig.update_layout(
            title="Quality Metrics Summary",
            height=300,
            showlegend=False
        )
    
    return sky_fig, mag_z_fig, fwhm_ellip_fig, count_text, info_text, quality_fig


@app.callback(
    Output('store-selected-ids', 'data'),
    [Input('catalog-sky-map', 'selectedData'),
     Input('mag-redshift-plot', 'selectedData'),
     Input('fwhm-ellip-plot', 'selectedData')],
    [State('store-selected-ids', 'data')]
)
def update_selection(sky_selected, mag_z_selected, fwhm_selected, current_selected):
    """Handle linked brushing between plots."""
    triggered = ctx.triggered_id
    
    # Get points from the triggered plot
    selected_points = None
    if triggered == 'catalog-sky-map' and sky_selected:
        selected_points = sky_selected.get('points', [])
    elif triggered == 'mag-redshift-plot' and mag_z_selected:
        selected_points = mag_z_selected.get('points', [])
    elif triggered == 'fwhm-ellip-plot' and fwhm_selected:
        selected_points = fwhm_selected.get('points', [])
    
    if selected_points:
        # Extract IDs from selected points
        ids = []
        for point in selected_points:
            if 'text' in point:
                # Parse ID from hover text
                text = point['text']
                if 'ID:' in text:
                    id_str = text.split('ID:')[1].split('<br>')[0].strip()
                    try:
                        ids.append(int(id_str))
                    except ValueError:
                        pass
        
        if ids:
            logger.info(f"Selected {len(ids)} objects via {triggered}")
            return ids
    
    return current_selected or []


@app.callback(
    Output('selection-stats', 'children'),
    [Input('store-selected-ids', 'data'),
     Input('store-catalog', 'data')]
)
def update_selection_stats(selected_ids, catalog_data):
    """Update selection statistics."""
    if not selected_ids:
        return html.P("No objects selected. Click and drag on any plot to select.", 
                     className="text-muted")
    
    df = global_state.get("catalog_data")
    if df is None:
        return html.P("Loading catalog...", className="text-muted")
    
    selected_set = set(selected_ids)
    stats = calculate_selection_statistics(df, selected_set)
    
    stat_items = [
        html.H5(f"📊 {stats.get('count', 0)} Objects Selected", className="text-info mb-3")
    ]
    
    if stats.get('ra_range'):
        stat_items.append(html.Div([
            html.Strong("RA Range: "),
            f"{stats['ra_range'][0]:.2f}° - {stats['ra_range'][1]:.2f}°"
        ], className="mb-2"))
    
    if stats.get('dec_range'):
        stat_items.append(html.Div([
            html.Strong("Dec Range: "),
            f"{stats['dec_range'][0]:.2f}° - {stats['dec_range'][1]:.2f}°"
        ], className="mb-2"))
    
    if stats.get('magnitude_avg'):
        stat_items.append(html.Div([
            html.Strong("Avg Magnitude: "),
            f"{stats['magnitude_avg']:.2f} ± {stats['magnitude_std']:.2f}"
        ], className="mb-2"))
    
    if stats.get('redshift_median'):
        stat_items.append(html.Div([
            html.Strong("Median Redshift: "),
            f"{stats['redshift_median']:.3f}"
        ], className="mb-2"))
    
    if stats.get('class_distribution'):
        stat_items.append(html.Div([
            html.Strong("Class Distribution: "),
            html.Span(", ".join([f"{k}: {v}" for k, v in stats['class_distribution'].items()]))
        ], className="mb-2"))
    
    return stat_items


@app.callback(
    Output('btn-export', 'disabled'),
    Input('store-selected-ids', 'data')
)
def update_export_button(selected_ids):
    """Enable/disable export button based on selection."""
    return not selected_ids or len(selected_ids) == 0


@app.callback(
    Output('download-data', 'data'),
    Input('btn-export', 'n_clicks'),
    [State('store-selected-ids', 'data')],
    prevent_initial_call=True
)
def export_data(n_clicks, selected_ids):
    """Export selected targets."""
    if not selected_ids:
        return None
    
    df = global_state.get("catalog_data")
    if df is None:
        return None
    
    selected_set = set(selected_ids)
    csv_data = export_selected_targets(df, selected_set, format="CSV")
    
    return dict(content=csv_data, filename="selected_targets.csv")


# Add download component dynamically in layout
def serve_layout_with_download():
    """Serve layout with download component."""
    layout = serve_layout()
    # Append download component to the end
    layout.children.append(dcc.Download(id='download-data'))
    return layout

app.layout = serve_layout_with_download


if __name__ == '__main__':
    logger.info("Starting AstroWatch & Triage Dashboard...")
    logger.info(f"Configuration: Mock data={config.MOCK_WEATHER_DATA}, Observatory={config.OBSERVATORY_NAME}")
    
    # Run the server
    app.run(
        host='127.0.0.1',
        port=8050,
        debug=True,
        dev_tools_hot_reload=True
    )
