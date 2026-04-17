"""
Alert Map - Interactive celestial map for astronomical events.

Creates Plotly scatter plots on sky coordinates with filtering and hover info.
"""

from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

import config


def create_alert_sky_map(events: List[Dict[str, Any]], 
                         event_type_filter: str = "ALL",
                         height: int = 600,
                         dark_theme: bool = True) -> go.Figure:
    """
    Create interactive sky map showing alert positions.
    
    Args:
        events: List of event dictionaries with ra, dec, type, magnitude.
        event_type_filter: Filter by event type ("ALL" for no filter).
        height: Figure height in pixels.
        dark_theme: Use dark theme for astronomy.
        
    Returns:
        Plotly Figure object.
    """
    # Filter events
    if event_type_filter != "ALL":
        events = [e for e in events if e["type"] == event_type_filter]
    
    if not events:
        return _create_empty_map(height, dark_theme)
    
    # Extract coordinates and properties
    ras = [e["ra"] for e in events]
    decs = [e["dec"] for e in events]
    magnitudes = [e["magnitude"] for e in events]
    types = [e["type"] for e in events]
    priorities = [e.get("priority", 3) for e in events]
    
    # Create hover text
    hover_texts = []
    for e in events:
        hover = (
            f"ID: {e['id']}<br>"
            f"Type: {e['type']}<br>"
            f"RA: {e['ra']:.4f}°<br>"
            f"Dec: {e['dec']:+.4f}°<br>"
            f"Magnitude: {e['magnitude']:.2f}<br>"
            f"Priority: {e.get('priority', 'N/A')}<br>"
            f"Time: {e.get('timestamp', 'N/A')[:19]}"
        )
        hover_texts.append(hover)
    
    # Map priority to marker size
    sizes = [(6 - p) * 5 + 5 for p in priorities]  # Priority 1 = size 30, 5 = size 10
    
    # Get colors for each event type
    colors = [config.PRIORITY_COLORS.get(t, "#888888") for t in types]
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter trace
    fig.add_trace(go.Scattergl(
        x=ras,
        y=decs,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.7,
            line=dict(width=1, color='white'),
            symbol='circle'
        ),
        text=hover_texts,
        hoverinfo='text',
        name='Alerts'
    ))
    
    # Update layout
    fig.update_layout(
        height=height,
        xaxis_title="Right Ascension (degrees)",
        yaxis_title="Declination (degrees)",
        xaxis=dict(
            range=[0, 360],
            tickmode='linear',
            tick0=0,
            dtick=45,
            showgrid=True,
            gridcolor='#30363d' if dark_theme else '#cccccc'
        ),
        yaxis=dict(
            range=[-90, 90],
            tickmode='linear',
            tick0=-90,
            dtick=30,
            showgrid=True,
            gridcolor='#30363d' if dark_theme else '#cccccc'
        ),
        plot_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        showlegend=False,
        margin=dict(l=60, r=20, t=40, b=60),
        hovermode='closest'
    )
    
    # Add grid lines for RA hours
    for ra_hour in range(0, 24, 3):
        ra_deg = ra_hour * 15
        fig.add_vline(x=ra_deg, line_dash="dash", line_color="#444444", opacity=0.3)
    
    # Add celestial equator
    fig.add_hline(y=0, line_dash="solid", line_color="#666666", opacity=0.5)
    
    return fig


def _create_empty_map(height: int, dark_theme: bool) -> go.Figure:
    """Create empty map placeholder."""
    fig = go.Figure()
    
    fig.update_layout(
        height=height,
        xaxis_title="Right Ascension (degrees)",
        yaxis_title="Declination (degrees)",
        xaxis=dict(range=[0, 360]),
        yaxis=dict(range=[-90, 90]),
        plot_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        annotations=[dict(
            text="No alerts to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )]
    )
    
    return fig


def create_alert_type_pie_chart(events: List[Dict[str, Any]], 
                                dark_theme: bool = True) -> go.Figure:
    """
    Create pie chart showing distribution of alert types.
    
    Args:
        events: List of event dictionaries.
        dark_theme: Use dark theme.
        
    Returns:
        Plotly Figure object.
    """
    # Count by type
    type_counts = {}
    for e in events:
        t = e["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    if not type_counts:
        return go.Figure().add_annotation(text="No data", showarrow=False)
    
    labels = list(type_counts.keys())
    values = list(type_counts.values())
    colors = [config.PRIORITY_COLORS.get(t, "#888888") for t in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.3,
        textinfo='label+percent',
        hoverinfo='label+value'
    )])
    
    fig.update_layout(
        height=400,
        title="Alert Distribution by Type",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def create_magnitude_histogram(events: List[Dict[str, Any]], 
                               dark_theme: bool = True) -> go.Figure:
    """
    Create histogram of alert magnitudes.
    
    Args:
        events: List of event dictionaries.
        dark_theme: Use dark theme.
        
    Returns:
        Plotly Figure object.
    """
    if not events:
        return go.Figure().add_annotation(text="No data", showarrow=False)
    
    magnitudes = [e["magnitude"] for e in events]
    
    fig = go.Figure(data=[go.Histogram(
        x=magnitudes,
        nbinsx=30,
        marker_color=config.DARK_THEME['accent'],
        opacity=0.7
    )])
    
    fig.update_layout(
        height=300,
        title="Magnitude Distribution",
        xaxis_title="Magnitude",
        yaxis_title="Count",
        plot_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        margin=dict(l=60, r=20, t=40, b=60),
        showlegend=False
    )
    
    return fig


def create_alert_time_series(events: List[Dict[str, Any]], 
                            hours: int = 24,
                            dark_theme: bool = True) -> go.Figure:
    """
    Create time series of alert rate.
    
    Args:
        events: List of event dictionaries.
        hours: Time window in hours.
        dark_theme: Use dark theme.
        
    Returns:
        Plotly Figure object.
    """
    from datetime import datetime, timedelta
    
    if not events:
        return go.Figure().add_annotation(text="No data", showarrow=False)
    
    # Parse timestamps and bin by hour
    now = datetime.utcnow()
    bins = [0] * hours
    
    for e in events:
        try:
            ts = datetime.fromisoformat(e["timestamp"].replace('Z', '+00:00'))
            if ts.tzinfo is None:
                age_hours = (now - ts).total_seconds() / 3600
            else:
                age_hours = (now - ts.replace(tzinfo=None)).total_seconds() / 3600
            
            if 0 <= age_hours < hours:
                bin_idx = int(age_hours)
                bins[hours - 1 - bin_idx] += 1
        except Exception:
            continue
    
    # Create time labels
    time_labels = []
    for h in range(hours - 1, -1, -1):
        time_point = now - timedelta(hours=h)
        time_labels.append(time_point.strftime("%H:%M"))
    
    fig = go.Figure(data=[go.Bar(
        x=time_labels,
        y=bins,
        marker_color=config.DARK_THEME['accent'],
        opacity=0.8
    )])
    
    fig.update_layout(
        height=300,
        title=f"Alert Rate (Last {hours} Hours)",
        xaxis_title="Time (UTC)",
        yaxis_title="Alerts per Hour",
        plot_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black', size=10),
        margin=dict(l=60, r=20, t=40, b=80),
        showlegend=False,
        xaxis_tickangle=-45
    )
    
    return fig
