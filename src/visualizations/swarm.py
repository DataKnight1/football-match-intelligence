"""
Author: Tiago Monteiro
Date: 22-12-2025
Swarm and violin plot visualization for distribution analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import textwrap

def plot_swarm_violin(
    df: pd.DataFrame,
    y_metric: str,
    x_group: str,
    y_label: str = None,
    x_label: str = None,
    title: str = "Threat Distribution",
    highlight_p1_id: int = None,
    highlight_p2_id: int = None,
    p1_name: str = "Player 1",
    p2_name: str = "Player 2",
    figsize=(14, 7), 
    order: list = None
) -> plt.Figure:
    """
    Create a violin plot with a swarm overlay to show distribution of a metric.
    
    :param df: DataFrame containing data.
    :param y_metric: Check metric value (Y-axis).
    :param x_group: Grouping category (X-axis).
    :param y_label: Label for Y.
    :param x_label: Label for X.
    :param title: Plot title.
    :param highlight_p1_id: P1 ID to highlight.
    :param highlight_p2_id: P2 ID to highlight.
    :param figsize: Figure size.
    :param order: Explicit order for X-axis categories.
    :return: Matplotlib Figure.
    """
    if df.empty or y_metric not in df.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No Data for Swarm Plot", ha='center')
        ax.axis('off')
        return fig

    if not order:
        standard_order = [
            'GR', 'GK', 'Goalkeeper',
            'RB', 'RWB', 'RCB', 'CB', 'LCB', 'LWB', 'LB',
            'CDM', 'DM', 'RCM', 'CM', 'LCM', 'AM', 'CAM', 'RM', 'LM',
            'RW', 'RAM', 'LAM', 'LW', 'CF', 'ST', 'LS', 'RS', 'Striker', 'Forward'
        ]
        present_cats = df[x_group].unique()
        order = [o for o in standard_order if o in present_cats]
        for cat in present_cats:
            if cat not in order:
                order.append(cat)

    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=figsize)
    
    sns.violinplot(
        data=df,
        x=x_group,
        y=y_metric,
        order=order,
        inner=None,
        color='#f0f0f0',
        linewidth=0,
        width=0.8,
        ax=ax
    )
    
    sns.swarmplot(
        data=df,
        x=x_group,
        y=y_metric,
        order=order,
        color='#4A4A4A',
        alpha=0.4,
        size=4,
        ax=ax,
        zorder=1
    )
    
    def highlight_player(pid, name, color, offset=0):
        if pid is None: return
        p_data = df[df['player_id'] == pid]
        if not p_data.empty:
            p_cat = str(p_data[x_group].values[0])
            if p_cat in order:
                idx = order.index(p_cat)
                
                ax.scatter(
                    idx, p_data[y_metric], 
                    color=color, s=200, zorder=20, 
                    edgecolor='black', linewidth=1.5,
                    label=name
                )
                
                ax.text(
                    idx + offset, p_data[y_metric].values[0],
                    name,
                    ha='center', va='bottom',
                    fontweight='bold', fontsize=9,
                    color='black', zorder=21
                )

    highlight_player(highlight_p1_id, p1_name, '#32FF69', offset=0)
    highlight_player(highlight_p2_id, p2_name, '#3385FF', offset=0)

    ax.set_xticklabels([textwrap.fill(o, 10) for o in order], fontsize=10)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel(x_label if x_label else "Position", fontsize=12)
    ax.set_ylabel(y_label if y_label else y_metric, fontsize=12)
    
    sns.despine(left=True)
    
    return fig
