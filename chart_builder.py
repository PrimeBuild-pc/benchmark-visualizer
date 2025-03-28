import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def build_bar_chart(df, x_column, y_column, theme):
    """Build a horizontal bar chart"""
    # Choose colors based on theme
    if theme == 'dark':
        bg_color = '#121212'
        text_color = 'white'
        plot_bg_color = '#1E1E1E'
        grid_color = '#333333'
        main_color = '#ff7514'
        secondary_color = '#ffa35c'
    else:
        bg_color = 'white'
        text_color = '#333333'
        plot_bg_color = '#f5f5f5'
        grid_color = '#dddddd'
        main_color = '#ff7514'
        secondary_color = '#ff8c38'

    # Create horizontal bar chart
    fig = px.bar(
        df, 
        y=x_column, 
        x=y_column,
        orientation='h',
        color_discrete_sequence=[main_color],
        text=y_column,
        height=max(400, len(df) * 40)  # Increase spacing slightly
    )

    # Round bar corners using marker.line and border radius simulation
    fig.update_traces(
        texttemplate='%{x:.1f}',
        textposition='inside',
        insidetextanchor='middle',
        hovertemplate='<b>%{y}</b><br>%{x:.1f}',
        marker_line_width=1,
        marker_line_color=main_color,
        marker=dict(line=dict(width=0), opacity=0.9, color=main_color),
    )

    fig.update_layout(
        plot_bgcolor=plot_bg_color,
        paper_bgcolor=bg_color,
        font_color=text_color,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title=y_column,
        yaxis_title=None,
        xaxis=dict(showgrid=True, gridcolor=grid_color, zeroline=False),
        yaxis=dict(showgrid=False, categoryorder='total ascending'),
        hoverlabel=dict(bgcolor=plot_bg_color, font_color=text_color, font_size=14, bordercolor=main_color),
        bargap=0.1  # Reduce gap between bars
    )

    st.session_state.current_figure = fig
    return fig

def build_line_chart(df, x_column, y_column, theme):
    """Build a line chart"""
    # Choose colors based on theme
    if theme == 'dark':
        bg_color = '#121212'
        text_color = 'white'
        plot_bg_color = '#1E1E1E'
        grid_color = '#333333'
    else:
        bg_color = 'white'
        text_color = '#333333'
        plot_bg_color = '#f5f5f5'
        grid_color = '#dddddd'
    
    # Create sorted data
    df_sorted = df.sort_values(by=y_column, ascending=False)
    
    # Create line chart
    fig = go.Figure()
    
    # Add line
    fig.add_trace(go.Scatter(
        x=df_sorted[x_column], 
        y=df_sorted[y_column],
        mode='lines+markers',
        name=y_column,
        line=dict(color='#ff7514', width=3),
        marker=dict(size=10, color='#ff7514', line=dict(width=2, color='white')),
        hovertemplate='<b>%{x}</b><br>%{y:.1f}',
    ))
    
    # Update layout
    fig.update_layout(
        plot_bgcolor=plot_bg_color,
        paper_bgcolor=bg_color,
        font_color=text_color,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title=None,
        yaxis_title=y_column,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickangle=45,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
        ),
        hoverlabel=dict(
            bgcolor=plot_bg_color,
            font_color=text_color,
            font_size=14,
            bordercolor='#ff7514',
        ),
        hovermode='closest',
        height=500,
    )
    
    # Add animation on hover
    fig.update_traces(
        hoverinfo='all',
    )
    
    # Store the figure in session state for potential export
    st.session_state.current_figure = fig
    
    return fig

def build_stacked_bar_chart(df, x_column, y_columns, theme):
    """Build a stacked bar chart"""
    if theme == 'dark':
        bg_color = '#121212'
        text_color = 'white'
        plot_bg_color = '#1E1E1E'
        grid_color = '#333333'
    else:
        bg_color = 'white'
        text_color = '#333333'
        plot_bg_color = '#f5f5f5'
        grid_color = '#dddddd'

    color_sequence = ['#ff7514', '#ffa35c', '#ffba80', '#ffd1a4']

    df['total'] = df[y_columns].sum(axis=1)
    df_sorted = df.sort_values(by='total', ascending=False)

    fig = go.Figure()
    for i, y_column in enumerate(y_columns):
        fig.add_trace(go.Bar(
            y=df_sorted[x_column],
            x=df_sorted[y_column],
            name=y_column,
            orientation='h',
            marker_color=color_sequence[i % len(color_sequence)],
            text=df_sorted[y_column],
            textposition='inside',
            insidetextanchor='middle',
            hovertemplate='<b>%{y}</b><br>%{x:.1f}',
            opacity=0.95
        ))

    fig.update_layout(
        barmode='stack',
        plot_bgcolor=plot_bg_color,
        paper_bgcolor=bg_color,
        font_color=text_color,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title='Valori',
        yaxis_title=None,
        legend=dict(orientation='h', yanchor='top', y=1.05, xanchor='center', x=0.5, font=dict(size=10)),
        xaxis=dict(showgrid=True, gridcolor=grid_color, zeroline=False),
        yaxis=dict(showgrid=False, categoryorder='array', categoryarray=df_sorted[x_column].tolist()),
        hoverlabel=dict(bgcolor=plot_bg_color, font_color=text_color, font_size=14),
        height=max(400, len(df) * 40)
    )

    st.session_state.current_figure = fig
    return fig

def highlight_best_performance(fig, df, x_column, y_column):
    """Highlight the best performing test in green"""
    # Get the best performance (highest value)
    max_value = df[y_column].max()
    best_test = df.loc[df[y_column] == max_value, x_column].values[0]
    
    # Find the index of the best test in the plot
    idx = None
    for i, y_val in enumerate(fig.data[0].y):
        if y_val == best_test:
            idx = i
            break
    
    if idx is not None:
        # Make a copy of the marker colors
        colors = ['#ff7514'] * len(fig.data[0].y)
        # Change the color of the best test
        colors[idx] = '#2ecc71'  # Green color for best performance
        
        # Update the marker colors
        fig.data[0].marker.color = colors
