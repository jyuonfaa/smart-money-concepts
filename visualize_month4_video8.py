import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
sys.path.insert(0, r'd:\C.Slim\ict-intelligence')
from smartmoneyconcepts.smc import smc

CSV_PATH = r'd:\C.Slim\ict-intelligence\HISTDATA_COM_ASCII_AUDUSD_M12016\DAT_ASCII_AUDUSD_M1_2016.csv'
df_raw = pd.read_csv(CSV_PATH, sep=';', names=['date','open','high','low','close','volume'])
df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y%m%d %H%M%S')
df_raw.set_index('date', inplace=True)
df_15m = df_raw.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

swing_hl = smc.swing_highs_lows(df_15m, swing_length=5)
ob_df = smc.ob(df_15m, swing_hl)
pb_df = smc._propulsion_blocks(df_15m, ob_df)

pb_valid = pb_df[pb_df['PB'].notna()].copy()

def make_chart(df, pb_rows, title, out_png, out_html):
    """df: sliced OHLC. pb_rows: list of (ts, row) tuples for blocks that fall in this window."""
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=[t.isoformat() for t in df.index],
        open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Price', increasing_line_color='green', decreasing_line_color='red'
    ))

    for ts, row in pb_rows:
        direction = int(row['PB'])
        color = 'rgba(0,100,255,0.3)' if direction == 1 else 'rgba(255,50,50,0.3)'
        border_color = 'blue' if direction == 1 else 'red'
        label = 'BULL PB' if direction == 1 else 'BEAR PB'

        pb_top    = float(row['PBTop'])
        pb_bottom = float(row['PBBottom'])
        anchor_ts = row['AnchorOB_Index']
        mt_ts     = row['MeanThresholdViolated']
        inv_ts    = row['Invalidated']

        ts_str     = ts.isoformat()
        anchor_str = anchor_ts.isoformat() if pd.notna(anchor_ts) else None

        # Zone extends from anchor to end-of-window (or invalidation if within window)
        if pd.notna(inv_ts) and inv_ts in df.index:
            zone_end = inv_ts.isoformat()
        else:
            zone_end = df.index[-1].isoformat()

        zone_start = anchor_str if (anchor_str and anchor_ts >= df.index[0]) else df.index[0].isoformat()

        # PB zone rectangle
        fig.add_shape(type='rect',
            x0=zone_start, x1=zone_end,
            y0=pb_bottom, y1=pb_top,
            xref='x', yref='y',
            fillcolor=color, line=dict(color=border_color, width=1.5)
        )

        # PB label at timestamp
        fig.add_annotation(
            x=ts_str, y=pb_top,
            text=label, showarrow=False,
            font=dict(size=10, color=border_color),
            xref='x', yref='y', yshift=8
        )

        # Mean Threshold line
        mt_level = (pb_top + pb_bottom) / 2.0
        fig.add_shape(type='line',
            x0=zone_start, x1=zone_end,
            y0=mt_level, y1=mt_level,
            xref='x', yref='y',
            line=dict(color=border_color, width=1, dash='dot')
        )

        # MeanThresholdViolated marker
        if pd.notna(mt_ts) and mt_ts in df.index:
            fig.add_shape(type='line',
                x0=mt_ts.isoformat(), x1=mt_ts.isoformat(),
                y0=0, y1=1, xref='x', yref='paper',
                line=dict(color='orange', width=1.5, dash='dash')
            )
            fig.add_annotation(
                x=mt_ts.isoformat(), y=1, xref='x', yref='paper',
                text='MT', showarrow=False, font=dict(size=9, color='orange'), yshift=5
            )

        # Invalidated marker
        if pd.notna(inv_ts) and inv_ts in df.index:
            fig.add_shape(type='line',
                x0=inv_ts.isoformat(), x1=inv_ts.isoformat(),
                y0=0, y1=1, xref='x', yref='paper',
                line=dict(color='black', width=1.5, dash='dash')
            )
            fig.add_annotation(
                x=inv_ts.isoformat(), y=0.95, xref='x', yref='paper',
                text='INV', showarrow=False, font=dict(size=9, color='black'), yshift=5
            )

        # Phase 3: Retest marker
        retest_ts  = row.get('PBRetestIndex') if hasattr(row, 'get') else row['PBRetestIndex']
        retest_rej = row.get('PBRetestRejected') if hasattr(row, 'get') else row['PBRetestRejected']
        wick_extreme_level = float(row['PBBottom']) if direction == 1 else float(row['PBTop'])
        # For bullish: wick_extreme is below PBBottom (wick low); for bearish: above PBTop (wick high)
        # We stored wick_extreme in smc.py but not in pb_df columns, so approximate from known geometry:
        # (wick_extreme is not in the output DataFrame -- we draw the horizontal at the wick level by
        #  reading the actual OHLC low/high of the PB candle from df if available)
        if ts in df.index:
            wb_candle = df.loc[ts]
            wick_extreme_level = float(wb_candle['low']) if direction == 1 else float(wb_candle['high'])

        if pd.notna(retest_ts) and retest_ts in df.index:
            retest_str = retest_ts.isoformat()
            rej_label = 'RETEST✓' if retest_rej else 'RETEST✗'
            rej_color = 'green' if retest_rej else 'darkorange'
            # Vertical line at retest bar
            fig.add_shape(type='line',
                x0=retest_str, x1=retest_str,
                y0=0, y1=1, xref='x', yref='paper',
                line=dict(color=rej_color, width=1.5, dash='dashdot')
            )
            fig.add_annotation(
                x=retest_str, y=0.75, xref='x', yref='paper',
                text=rej_label, showarrow=False,
                font=dict(size=9, color=rej_color), yshift=5
            )
            # Horizontal wick_extreme level (dashed, full window width)
            fig.add_shape(type='line',
                x0=df.index[0].isoformat(), x1=df.index[-1].isoformat(),
                y0=wick_extreme_level, y1=wick_extreme_level,
                xref='x', yref='y',
                line=dict(color=rej_color, width=1, dash='dash')
            )
            fig.add_annotation(
                x=retest_str, y=wick_extreme_level,
                text='wick', showarrow=False,
                font=dict(size=8, color=rej_color),
                xref='x', yref='y', xshift=20
            )

        # Anchor vertical line
        if anchor_str and anchor_ts >= df.index[0]:
            fig.add_shape(type='line',
                x0=anchor_str, x1=anchor_str,
                y0=0, y1=1, xref='x', yref='paper',
                line=dict(color='purple', width=1, dash='dot')
            )
            fig.add_annotation(
                x=anchor_str, y=0.85, xref='x', yref='paper',
                text='Anchor', showarrow=False, font=dict(size=9, color='purple'), yshift=5
            )

    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=600, width=1200,
        plot_bgcolor='white',
        xaxis=dict(type='category', nticks=30, tickangle=-45)
    )

    fig.write_html(out_html)
    try:
        import kaleido
        fig.write_image(out_png)
        print(f'Saved PNG: {out_png}')
    except Exception as e:
        print(f'PNG failed ({e}), HTML saved: {out_html}')


# --- Chart 1: Nov-10 BULL block — extended window to include retest at 2016-11-11 09:30 ---
# Block at 2016-11-10 21:00, anchor at 2016-11-10 04:45, retest at 2016-11-11 09:30
focus_ts1 = pd.Timestamp('2016-11-10 21:00')
anchor_ts1 = pd.Timestamp('2016-11-10 04:45')
win_start1 = anchor_ts1 - pd.Timedelta(hours=4)
win_end1   = pd.Timestamp('2016-11-11 11:00')   # Extended: covers retest at 09:30 + 1.5h buffer
df_win1 = df_15m.loc[win_start1:win_end1]
pb_rows1 = [(ts, row) for ts, row in pb_valid.iterrows()
            if ts >= win_start1 and ts <= win_end1]

make_chart(df_win1, pb_rows1,
    title='M4V8 BULL Propulsion Block — Nov 10 2016 (Retest at Nov 11 09:30)',
    out_png=r'd:\C.Slim\ict-intelligence\pb_bull_nov10.png',
    out_html=r'd:\C.Slim\ict-intelligence\pb_bull_nov10.html')


# --- Chart 2: Dec-16 BEAR block (live block) ---
focus_ts2 = pd.Timestamp('2016-12-16 06:00')
anchor_ts2 = pd.Timestamp('2016-12-15 22:15')
win_start2 = anchor_ts2 - pd.Timedelta(hours=4)
win_end2   = focus_ts2 + pd.Timedelta(hours=16)
df_win2 = df_15m.loc[win_start2:win_end2]
pb_rows2 = [(ts, row) for ts, row in pb_valid.iterrows()
            if ts >= win_start2 and ts <= win_end2]

make_chart(df_win2, pb_rows2,
    title='M4V8 BEAR Propulsion Block — Dec 16 2016 (Live Block)',
    out_png=r'd:\C.Slim\ict-intelligence\pb_bear_dec16.png',
    out_html=r'd:\C.Slim\ict-intelligence\pb_bear_dec16.html')

print('Done.')
