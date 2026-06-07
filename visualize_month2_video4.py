"""
visualize_month2_video4.py
ICT Month 2 Video 4 — No Fear of Losing: Expectancy Matrix
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from risk_engine import calc_expectancy

def build_dashboard():
    scenarios = [
        {"Accuracy": 0.30, "Risk/Trade": 0.02, "R:R": 3.0},
        {"Accuracy": 0.30, "Risk/Trade": 0.02, "R:R": 5.0},
        {"Accuracy": 0.40, "Risk/Trade": 0.02, "R:R": 5.0},
        {"Accuracy": 0.50, "Risk/Trade": 0.02, "R:R": 5.0},
        {"Accuracy": 0.50, "Risk/Trade": 0.01, "R:R": 5.0},
        {"Accuracy": 0.50, "Risk/Trade": 0.005, "R:R": 5.0},
    ]
    
    account = 5000.0
    n_trades = 10
    
    # Process scenarios
    data = []
    for s in scenarios:
        res = calc_expectancy(s["Accuracy"], s["Risk/Trade"], s["R:R"], account, n_trades)
        data.append([
            f"{s['Accuracy']*100:.0f}%",
            f"{s['Risk/Trade']*100:.1f}%",
            f"{s['R:R']}:1",
            res['wins'],
            res['losses'],
            f"${res['subtotal_wins']:,.0f}",
            f"${res['subtotal_losses']:,.0f}",
            f"${res['net_profit']:,.0f}",
            res['monthly_pct']
        ])
        
    # Table columns
    headers = ["Accuracy", "Risk/Trade", "R:R", "Wins", "Losses", 
               "Subtotal Wins", "Subtotal Losses", "Net Profit", "Monthly %"]
               
    # Colors
    row_colors = ['#1e1e1e'] * 6
    row_colors[4] = '#0a3622'  # Highlight optimal scenario 5
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.1,
        specs=[[{"type": "table"}], [{"type": "bar"}]],
        row_heights=[0.4, 0.6]
    )
    
    # 1. Table
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
                fill_color=[row_colors]*9,
                align='center',
                font=dict(color='white', size=11)
            )
        ),
        row=1, col=1
    )
    
    # 2. Bar Chart
    monthly_pcts = [d[8] for d in data]
    labels = [f"Scenario {i+1}" for i in range(6)]
    bar_colors = ['#2ca02c'] * 6
    bar_colors[4] = '#1b5e20'  # Darker green for optimal
    
    fig.add_trace(
        go.Bar(
            x=labels,
            y=monthly_pcts,
            marker_color=bar_colors,
            text=[f"{p:.1f}%" for p in monthly_pcts],
            textposition='auto',
            name="Monthly % Return"
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="ICT Month 2 Video 4 — No Fear of Losing: Expectancy Matrix",
        template="plotly_dark",
        height=800,
        showlegend=False,
        annotations=[
            dict(
                x=0.5, y=-0.15,
                xref='paper', yref='paper',
                text="You don't need high accuracy. You need time and correct R:R framing.",
                showarrow=False,
                font=dict(size=16, color='#aaaaaa'),
                align='center'
            )
        ]
    )
    
    fig.update_yaxes(title_text="Monthly % Return", row=2, col=1)
    
    out_file = "ICT_MONTH2_VIDEO4_EXPECTANCY.html"
    fig.write_html(out_file)
    print(f"Generated dashboard: {out_file}")

if __name__ == "__main__":
    build_dashboard()
