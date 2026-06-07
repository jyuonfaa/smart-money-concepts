"""
visualize_month2_video5.py
ICT Month 2 Video 5 — Loss Mitigation
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def build_dashboard():
    # Simulated Equity Curve (Mitigating a 2% loss with 1% risk)
    # Trade 1: Initial trade, hits stop, -2%
    # Trade 2: Re-entry trade, risking 1%. We plot equity as it moves to 1R, 2R, 3R.
    
    r_multiples = [0, 1, 2, 3]
    equity_curve = [-2.0, -1.0, 0.0, 1.0] # 2% loss -> 1% loss at 1R -> breakeven at 2R -> +1% at 3R
    
    # Doubling down curve (Dangerous, just for contrast)
    # If a trader kept 2% risk, 1R gives +2% (breakeven), but another loss drops them to -4%.
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.1,
        specs=[[{"type": "table"}], [{"type": "scatter"}]],
        row_heights=[0.3, 0.7]
    )
    
    # 1. Table
    headers = ["Scenario", "Initial Risk", "Re-entry Risk", "R Required to Breakeven", "Status"]
    data = [
        ["ICT Mitigation (Halved Risk)", "2.0%", "1.0%", "2.0R", "SAFE (Preserves Equity)"],
        ["Aggressive (Same Risk)", "2.0%", "2.0%", "1.0R", "DANGEROUS (Risk of Ruin)"],
        ["Revenge Trading (Double Down)", "2.0%", "4.0%", "0.5R", "TOXIC (Fear-based)"]
    ]
    
    row_colors = ['#0a3622', '#362a0a', '#360a0a']
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=headers,
                fill_color='#2c2c2c',
                align='center',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=list(zip(*data)),
                fill_color=[row_colors]*5,
                align='center',
                font=dict(color='white', size=11)
            )
        ),
        row=1, col=1
    )
    
    # 2. Scatter Plot (Mitigation Curve)
    fig.add_trace(
        go.Scatter(
            x=r_multiples,
            y=equity_curve,
            mode='lines+markers+text',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=10),
            text=["Initial Loss (-2%)", "1R (+1%)", "2R (Breakeven)", "3R (+1% Profit)"],
            textposition="top left",
            name="ICT Mitigation Strategy"
        ),
        row=2, col=1
    )
    
    # Baseline (Breakeven)
    fig.add_trace(
        go.Scatter(
            x=[0, 3], y=[0.0, 0.0],
            mode='lines',
            line=dict(color='white', width=1, dash='dash'),
            name='Breakeven'
        ),
        row=2, col=1
    )    
    fig.update_layout(
        title="ICT Month 2 Video 5 — How To Mitigate Losing Trades Effectively",
        template="plotly_dark",
        height=800,
        showlegend=False,
        annotations=[
            dict(
                x=0.5, y=-0.1,
                xref='paper', yref='paper',
                text="Why would any trader think like a fool and not dial back their leverage if they take a losing trade?",
                showarrow=False,
                font=dict(size=14, color='#aaaaaa'),
                align='center'
            )
        ]
    )
    
    fig.update_xaxes(title_text="R-Multiple on Re-entry", row=2, col=1)
    fig.update_yaxes(title_text="Equity Change (%)", row=2, col=1)
    
    out_file = "ICT_MONTH2_VIDEO5_MITIGATION.html"
    fig.write_html(out_file)
    print(f"Generated dashboard: {out_file}")

if __name__ == "__main__":
    build_dashboard()
