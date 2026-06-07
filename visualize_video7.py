import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from smartmoneyconcepts import smc
from smartmoneyconcepts.state_machine import PriceDeliveryStateMachine

def run_visualization():
    print("Step 5: Visualizing AUDUSD Sept 2016 (Pure Projection)")
    
    # 1. Load Data
    path = 'HISTDATA_COM_ASCII_AUDUSD_M12016/DAT_ASCII_AUDUSD_M1_2016.csv'
    df_raw = pd.read_csv(path, sep=';', names=['date', 'open', 'high', 'low', 'close', 'volume'], index_col=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S').dt.tz_localize(None)
    df_raw.set_index('date', inplace=True)
    
    df_15m_full = df_raw.loc['2016-08-01':'2016-10-31'].resample('15min').agg({
        'open':'first','high':'max','low':'min','close':'last'
    }).dropna()
    df_15m_full.index = df_15m_full.index.tz_localize(None)

    # 2. Run Scanners
    swings = smc.swing_highs_lows_v4(df_15m_full)
    if 'type' in swings.columns:
        swings['HighLow'] = swings['type'].map({'HIGH': 1, 'LOW': -1})
        swings['Level'] = swings['p']

    fvgs = smc.fvg(df_15m_full)
    if isinstance(fvgs.index, pd.RangeIndex): fvgs.index = df_15m_full.index
    else: fvgs.index = fvgs.index.tz_localize(None)
    
    liq = smc.liquidity(df_15m_full, swings)
    if isinstance(liq.index, pd.RangeIndex): liq.index = df_15m_full.index
    else: liq.index = liq.index.tz_localize(None)
    
    cons = smc.consolidation(df_15m_full, prd=10, conslen=5)

    # 3. Filter for target range
    df_15m = df_15m_full.loc['2016-09-01':'2016-09-30']
    exp = fvgs.reindex(df_15m.index)
    if 'FVG' in exp.columns: exp.rename(columns={'FVG': 'Expansion'}, inplace=True)
    cons_a = cons.reindex(df_15m.index)
    swings_a = swings[swings['ts'] <= df_15m.index[-1]]
    liq_a = liq.reindex(df_15m.index)
    
    # 4. Run State Machine
    sm = PriceDeliveryStateMachine()
    audit = sm.process(
        ohlc=df_15m,
        consolidation=cons_a,
        expansion=exp,
        liquidity=liq_a,
        swing_hl=swings_a
    )
    
    # 5. Build Visualization
    fig = make_subplots(rows=1, cols=1, subplot_titles=("AUDUSD 15M (Sept 2016) - LRR/HRR Environment",))
    fig.add_trace(go.Candlestick(
        x=df_15m.index, open=df_15m['open'], high=df_15m['high'], low=df_15m['low'], close=df_15m['close'], name="15M"
    ), row=1, col=1)

    # Issue 2: Draw on Liquidity Lines
    upper_targets = audit['Target'].where(audit['Target'] > df_15m['close'])
    lower_targets = audit['Target'].where(audit['Target'] < df_15m['close'])

    fig.add_trace(go.Scatter(
        x=df_15m.index, y=upper_targets,
        mode='lines', name='Draw on Liquidity (High)',
        line=dict(color='#4caf50', width=2, dash='dash')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df_15m.index, y=lower_targets,
        mode='lines', name='Draw on Liquidity (Low)',
        line=dict(color='#f44336', width=2, dash='dash')
    ), row=1, col=1)

    # Add Environment Backgrounds
    blocks = []
    current_env_start = df_15m.index[0]
    current_env = audit['SovereignEnv'].iloc[0]
    
    for i in range(1, len(audit)):
        env = audit['SovereignEnv'].iloc[i]
        
        # When environment changes or we hit the end, store the block
        if env != current_env or i == len(audit) - 1:
            end_idx = df_15m.index[i]
            blocks.append({
                'env': current_env,
                'start': current_env_start,
                'end': end_idx,
                'duration': (end_idx - current_env_start).total_seconds()
            })
            current_env_start = end_idx
            current_env = env

    # Enforce Rule of 3 for SOVEREIGN labels: Top 3 widest LRR blocks
    lrr_blocks = [b for b in blocks if b['env'] == 'LRR']
    lrr_blocks.sort(key=lambda x: x['duration'], reverse=True)
    top_3_lrr = lrr_blocks[:3]

    sovereign_y_positions = [0.15, 0.09, 0.03]  # bottom of chart, staggered down
    sovereign_count = 0
    
    for i, b in enumerate(blocks):
        color = "rgba(38,166,154,0.15)" if b['env'] == "LRR" else "rgba(239,83,80,0.15)"
        
        fig.add_vrect(
            x0=b['start'], x1=b['end'],
            fillcolor=color, opacity=1.0, layer="below", line_width=0,
            row=1, col=1
        )
        
        if b in top_3_lrr:
            mid_idx = b['start'] + (b['end'] - b['start']) / 2
            label_y = sovereign_y_positions[sovereign_count % 3]
            
            fig.add_annotation(
                x=mid_idx, y=label_y,
                xref='x', yref='paper',
                text="SOVEREIGN",
                showarrow=False,
                font=dict(color="#FFD700", size=14, family="Arial Black")
            )
            sovereign_count += 1
            
    # User's exact loop for TRANSITION labels
    prev_env = None
    transition_count = 0
    label_ay_positions = [-40, -80, -120, -160]  # 4-slot wider pixel offsets
    
    # Join ohlc with audit to get the 'high' values for placing the labels
    audit_with_price = audit.copy()
    audit_with_price['high'] = df_15m['high']
    
    for ts, row in audit_with_price.iterrows():
        env = row['SovereignEnv']
        if env != prev_env and prev_env is not None:
            # draw exactly one label here at ts
            label_color = "#26a69a" if env == "LRR" else "#ef5350"
            y_val = row['high'] + 0.0010
            
            # Alternate label ay-position to prevent stacking text
            ay_val = label_ay_positions[transition_count % 4]
            transition_count += 1
            
            fig.add_annotation(
                x=ts, y=y_val,
                text=f"TRANSITION: {env}",
                showarrow=True, arrowhead=2, ay=ay_val,
                font=dict(color=label_color, size=10, family="Arial Black"),
                row=1, col=1
            )
        prev_env = env

    fig.update_layout(
        height=900, template="plotly_dark", 
        title="ICT VIDEO 7: Sovereign Liquidity Engine (AUDUSD Sept 2016)",
        xaxis_rangeslider_visible=False
    )
    
    output_file = "visualize_video7.html"
    fig.write_html(output_file)
    print(f"\n[DONE] Saved visualization to {output_file}")

if __name__ == "__main__":
    run_visualization()
