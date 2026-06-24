
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st

def get_summary_statistics(df):
    """Returns basic descriptive statistics for the dataframe."""
    return df.describe()

def visualize_numerical_distributions(df):
    """Plots histograms and box plots for numerical columns."""
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    charts = {}

    for col in numerical_cols:
        if col in ['order_id']: continue # Skip ID columns
        
        # Histogram
        fig_hist = px.histogram(df, x=col, title=f"Distribution of {col}", template="plotly_dark", color_discrete_sequence=['#00CC96'])
        
        # Box Plot
        fig_box = px.box(df, y=col, title=f"Box Plot of {col}", template="plotly_dark", color_discrete_sequence=['#EF553B'])

        charts[col] = {"histogram": fig_hist, "boxplot": fig_box}
    
    return charts

def visualize_categorical_counts(df):
    """Plots bar charts for categorical columns."""
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns
    charts = {}

    for col in categorical_cols:
        if df[col].nunique() > 20: continue # Skip high cardinality columns for clarity
        
        # Bar Chart
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, 'count']
        fig = px.bar(counts, x=col, y='count', title=f"Count of {col}", template="plotly_dark", color='count', color_continuous_scale='Viridis')
        
        charts[col] = fig
    
    return charts

def visualize_time_series(df, date_col):
    """Plots time series trends if a date column exists."""
    if date_col not in df.columns:
        return None
    
    # Resample by day or month depending on range
    df = df.sort_values(by=date_col)
    
    # Check if we have numeric columns to plot over time
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Remove potential ID columns
    if 'order_id' in numeric_cols: numeric_cols.remove('order_id')

    if not numeric_cols: return None

    charts = {}
    for col in numeric_cols:
        daily_agg = df.groupby(date_col)[col].sum().reset_index()
        fig = px.line(daily_agg, x=date_col, y=col, title=f"{col} Over Time", template="plotly_dark", markers=True)
        charts[col] = fig
            
    return charts

def visualize_correlation_heatmap(df):
    """Plots a correlation heatmap for numerical columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Remove ID columns if present
    if 'order_id' in numeric_df.columns:
        numeric_df = numeric_df.drop(columns=['order_id'])
        
    if numeric_df.shape[1] < 2:
        return None

    corr = numeric_df.corr()
    
    fig = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        title="Correlation Heatmap",
        template="plotly_dark",
        color_continuous_scale='RdBu_r'
    )
    return fig
