"""
Linked Views - Implements cross-filtering and linked brushing between visualizations.

Enables glue-like interactive filtering across multiple plots in Dash.
"""

from typing import List, Dict, Any, Optional, Set
import plotly.graph_objects as go
import pandas as pd
import numpy as np

import config


def create_catalog_scatter(df: pd.DataFrame,
                          x_col: str = "ra",
                          y_col: str = "dec",
                          color_col: Optional[str] = None,
                          size_col: Optional[str] = None,
                          selected_ids: Optional[Set[int]] = None,
                          dark_theme: bool = True) -> go.Figure:
    """
    Create scatter plot with optional highlighting of selected points.
    
    Args:
        df: DataFrame with catalog data.
        x_col: Column for x-axis.
        y_col: Column for y-axis.
        color_col: Column for coloring points.
        size_col: Column for sizing points.
        selected_ids: Set of IDs to highlight.
        dark_theme: Use dark theme.
        
    Returns:
        Plotly Figure object.
    """
    if df.empty:
        return _create_empty_figure("No data", dark_theme)
    
    # Prepare trace data
    if selected_ids and len(selected_ids) > 0:
        # Split into selected and unselected
        mask_selected = df["id"].isin(selected_ids)
        df_selected = df[mask_selected]
        df_unselected = df[~mask_selected]
        
        fig = go.Figure()
        
        # Unselected points
        if not df_unselected.empty:
            fig.add_trace(go.Scattergl(
                x=df_unselected[x_col],
                y=df_unselected[y_col],
                mode='markers',
                marker=dict(
                    size=6 if size_col is None else df_unselected[size_col] / 5,
                    color='#888888',
                    opacity=0.3
                ),
                name='Unselected',
                hoverinfo='skip'
            ))
        
        # Selected points (highlighted)
        if not df_selected.empty:
            fig.add_trace(go.Scattergl(
                x=df_selected[x_col],
                y=df_selected[y_col],
                mode='markers',
                marker=dict(
                    size=10 if size_col is None else df_selected[size_col] / 3,
                    color=config.DARK_THEME['accent'],
                    opacity=0.9,
                    line=dict(width=1, color='white')
                ),
                name='Selected',
                text=df_selected.apply(lambda row: f"ID: {row['id']}<br>{x_col}: {row[x_col]:.2f}<br>{y_col}: {row[y_col]:.2f}", axis=1),
                hoverinfo='text'
            ))
    else:
        # All points without selection
        colors = None
        if color_col and color_col in df.columns:
            if df[color_col].dtype == 'object':
                # Categorical coloring
                categories = df[color_col].unique()
                color_map = {cat: config.PRIORITY_COLORS.get(cat, '#888888') for cat in categories}
                colors = [color_map.get(val, '#888888') for val in df[color_col]]
            else:
                colors = df[color_col]
        
        sizes = 6
        if size_col and size_col in df.columns:
            sizes = df[size_col] / 5
        
        fig = go.Figure(data=[go.Scattergl(
            x=df[x_col],
            y=df[y_col],
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors if colors is not None else config.DARK_THEME['accent'],
                opacity=0.6,
                colorscale='Viridis' if isinstance(colors, (list, np.ndarray)) else None
            ),
            text=df.apply(lambda row: f"ID: {row['id']}<br>{x_col}: {row[x_col]:.2f}<br>{y_col}: {row[y_col]:.2f}", axis=1),
            hoverinfo='text',
            name='Objects'
        )])
    
    # Update layout
    fig.update_layout(
        height=500,
        xaxis_title=x_col.upper(),
        yaxis_title=y_col.upper(),
        plot_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        showlegend=selected_ids is not None and len(selected_ids) > 0,
        margin=dict(l=60, r=20, t=40, b=60),
        hovermode='closest'
    )
    
    return fig


def create_magnitude_redshift_plot(df: pd.DataFrame,
                                   selected_ids: Optional[Set[int]] = None,
                                   dark_theme: bool = True) -> go.Figure:
    """
    Create magnitude vs redshift plot.
    
    Args:
        df: DataFrame with catalog data.
        selected_ids: Set of IDs to highlight.
        dark_theme: Use dark theme.
        
    Returns:
        Plotly Figure object.
    """
    if df.empty or "magnitude" not in df.columns or "redshift" not in df.columns:
        return _create_empty_figure("No data", dark_theme)
    
    # Filter to valid data
    df_valid = df.dropna(subset=["magnitude", "redshift"])
    
    if df_valid.empty:
        return _create_empty_figure("No valid data", dark_theme)
    
    if selected_ids and len(selected_ids) > 0:
        mask_selected = df_valid["id"].isin(selected_ids)
        df_selected = df_valid[mask_selected]
        df_unselected = df_valid[~mask_selected]
        
        fig = go.Figure()
        
        if not df_unselected.empty:
            fig.add_trace(go.Scattergl(
                x=df_unselected["redshift"],
                y=df_unselected["magnitude"],
                mode='markers',
                marker=dict(size=6, color='#888888', opacity=0.3),
                name='Unselected',
                hoverinfo='skip'
            ))
        
        if not df_selected.empty:
            fig.add_trace(go.Scattergl(
                x=df_selected["redshift"],
                y=df_selected["magnitude"],
                mode='markers',
                marker=dict(size=10, color=config.DARK_THEME['accent'], opacity=0.9),
                name='Selected',
                text=df_selected.apply(lambda row: f"ID: {row['id']}<br>z: {row['redshift']:.3f}<br>mag: {row['magnitude']:.2f}", axis=1),
                hoverinfo='text'
            ))
    else:
        fig = go.Figure(data=[go.Scattergl(
            x=df_valid["redshift"],
            y=df_valid["magnitude"],
            mode='markers',
            marker=dict(size=6, color=config.DARK_THEME['accent'], opacity=0.6),
            text=df_valid.apply(lambda row: f"ID: {row['id']}<br>z: {row['redshift']:.3f}<br>mag: {row['magnitude']:.2f}", axis=1),
            hoverinfo='text',
            name='Objects'
        )])
    
    # Invert y-axis (brighter at top)
    fig.update_layout(
        height=400,
        title="Magnitude vs Redshift",
        xaxis_title="Redshift (z)",
        yaxis_title="Magnitude",
        yaxis_autorange="reversed",
        plot_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        margin=dict(l=60, r=20, t=40, b=60)
    )
    
    return fig


def create_fwhm_ellipticity_plot(df: pd.DataFrame,
                                 selected_ids: Optional[Set[int]] = None,
                                 dark_theme: bool = True) -> go.Figure:
    """
    Create FWHM vs ellipticity quality plot.
    
    Args:
        df: DataFrame with catalog data.
        selected_ids: Set of IDs to highlight.
        dark_theme: Use dark theme.
        
    Returns:
        Plotly Figure object.
    """
    if df.empty or "fwhm" not in df.columns or "ellipticity" not in df.columns:
        return _create_empty_figure("No data", dark_theme)
    
    df_valid = df.dropna(subset=["fwhm", "ellipticity"])
    
    if df_valid.empty:
        return _create_empty_figure("No valid data", dark_theme)
    
    # Color by quality
    snr_available = "snr" in df_valid.columns
    
    if selected_ids and len(selected_ids) > 0:
        mask_selected = df_valid["id"].isin(selected_ids)
        df_selected = df_valid[mask_selected]
        df_unselected = df_valid[~mask_selected]
        
        fig = go.Figure()
        
        if not df_unselected.empty:
            fig.add_trace(go.Scattergl(
                x=df_unselected["fwhm"],
                y=df_unselected["ellipticity"],
                mode='markers',
                marker=dict(size=6, color='#888888', opacity=0.3),
                name='Unselected',
                hoverinfo='skip'
            ))
        
        if not df_selected.empty:
            colors = df_selected["snr"] if snr_available else config.DARK_THEME['accent']
            fig.add_trace(go.Scattergl(
                x=df_selected["fwhm"],
                y=df_selected["ellipticity"],
                mode='markers',
                marker=dict(
                    size=10,
                    color=colors,
                    colorscale='Viridis' if snr_available else None,
                    opacity=0.9
                ),
                name='Selected',
                text=df_selected.apply(lambda row: f"ID: {row['id']}<br>FWHM: {row['fwhm']:.2f}\"<br>Ellip: {row['ellipticity']:.3f}", axis=1),
                hoverinfo='text'
            ))
    else:
        colors = df_valid["snr"] if snr_available else config.DARK_THEME['accent']
        
        fig = go.Figure(data=[go.Scattergl(
            x=df_valid["fwhm"],
            y=df_valid["ellipticity"],
            mode='markers',
            marker=dict(
                size=6,
                color=colors,
                colorscale='Viridis' if snr_available else None,
                opacity=0.6
            ),
            text=df_valid.apply(lambda row: f"ID: {row['id']}<br>FWHM: {row['fwhm']:.2f}\"<br>Ellip: {row['ellipticity']:.3f}", axis=1),
            hoverinfo='text',
            name='Objects'
        )])
    
    fig.update_layout(
        height=400,
        title="Image Quality: FWHM vs Ellipticity",
        xaxis_title="FWHM (arcseconds)",
        yaxis_title="Ellipticity",
        plot_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['card_bg'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        margin=dict(l=60, r=20, t=40, b=60)
    )
    
    return fig


def _create_empty_figure(message: str, dark_theme: bool) -> go.Figure:
    """Create empty figure placeholder."""
    fig = go.Figure()
    
    fig.update_layout(
        height=400,
        plot_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        paper_bgcolor=config.DARK_THEME['background'] if dark_theme else 'white',
        font=dict(color=config.DARK_THEME['text'] if dark_theme else 'black'),
        annotations=[dict(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )]
    )
    
    return fig


def get_selected_data(df: pd.DataFrame, selected_ids: Set[int]) -> pd.DataFrame:
    """
    Get subset of data for selected IDs.
    
    Args:
        df: Full DataFrame.
        selected_ids: Set of selected IDs.
        
    Returns:
        Filtered DataFrame.
    """
    if not selected_ids:
        return df.head(0)  # Empty DataFrame with same columns
    return df[df["id"].isin(selected_ids)]


def calculate_selection_statistics(df: pd.DataFrame, 
                                   selected_ids: Set[int]) -> Dict[str, Any]:
    """
    Calculate statistics for selected objects.
    
    Args:
        df: Full DataFrame.
        selected_ids: Set of selected IDs.
        
    Returns:
        Dictionary with statistics.
    """
    if not selected_ids:
        return {"count": 0}
    
    selected = df[df["id"].isin(selected_ids)]
    
    stats = {
        "count": len(selected),
        "ra_range": (selected["ra"].min(), selected["ra"].max()) if "ra" in selected.columns else None,
        "dec_range": (selected["dec"].min(), selected["dec"].max()) if "dec" in selected.columns else None,
    }
    
    if "magnitude" in selected.columns:
        stats["magnitude_avg"] = round(selected["magnitude"].mean(), 2)
        stats["magnitude_std"] = round(selected["magnitude"].std(), 2)
    
    if "redshift" in selected.columns:
        stats["redshift_avg"] = round(selected["redshift"].mean(), 3)
        stats["redshift_median"] = round(selected["redshift"].median(), 3)
    
    if "class" in selected.columns:
        stats["class_distribution"] = selected["class"].value_counts().to_dict()
    
    return stats


def export_selected_targets(df: pd.DataFrame, 
                           selected_ids: Set[int],
                           format: str = "CSV") -> str:
    """
    Export selected targets to string format.
    
    Args:
        df: Full DataFrame.
        selected_ids: Set of selected IDs.
        format: Export format ("CSV", "JSON", "VOTable").
        
    Returns:
        String representation of exported data.
    """
    if not selected_ids:
        return ""
    
    selected = df[df["id"].isin(selected_ids)]
    
    if format == "CSV":
        return selected.to_csv(index=False)
    elif format == "JSON":
        return selected.to_json(orient='records', indent=2)
    elif format == "VOTable":
        # Simple VOTable format
        from astropy.table import Table
        table = Table.from_pandas(selected)
        return table.to_xml(format='votable')
    else:
        return selected.to_csv(index=False)
