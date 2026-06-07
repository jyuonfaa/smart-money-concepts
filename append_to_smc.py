code = """
    @classmethod
    def ny_midnight_open(cls, ohlc: pd.DataFrame) -> pd.Series:
        \"\"\"
        Month 3 Video 3: NY Midnight Power 3 Detector.
        Finds the exact opening price at 00:00:00 EST for each day, or the first
        available candle of that trading day (e.g., 17:00 EST for Sunday open).
        Forward-fills this value so every intraday candle knows its Midnight Open boundary.
        \"\"\"
        df = ohlc.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        idx_ny = df.index
        if idx_ny.tz is None:
            idx_ny = idx_ny.tz_localize('UTC').tz_convert('America/New_York')
        else:
            idx_ny = idx_ny.tz_convert('America/New_York')
            
        df['ny_time'] = idx_ny
        df['ny_date'] = df['ny_time'].dt.date
        
        # The first candle of the local NY date represents the opening price of that date.
        first_candles = df.groupby('ny_date').first()
        
        midnight_open_series = df['ny_date'].map(first_candles['open'])
        midnight_open_series.index = ohlc.index
        midnight_open_series.name = 'NY_Midnight_Open'
        
        return midnight_open_series

    @classmethod
    def session_order_blocks(cls, ob_df: pd.DataFrame, session_mask: pd.Series) -> pd.DataFrame:
        \"\"\"
        Month 3 Video 3: Session-Linked Recapitalization.
        Filters Order Blocks to only include those whose origin candle was formed 
        while session_mask was True (e.g., during London or NY killzones).
        \"\"\"
        result = ob_df.copy()
        
        # Identify rows where an OB was formed but the session mask is False
        invalid_mask = result['OB'].notna() & ~session_mask.astype(bool)
        
        result.loc[invalid_mask, 'OB'] = np.nan
        result.loc[invalid_mask, 'Top'] = np.nan
        result.loc[invalid_mask, 'Bottom'] = np.nan
        result.loc[invalid_mask, 'OBVolume'] = np.nan
        result.loc[invalid_mask, 'MitigatedIndex'] = np.nan
        
        if 'MeanThreshold' in result.columns:
            result.loc[invalid_mask, 'MeanThreshold'] = np.nan
            
        return result
"""

with open('smartmoneyconcepts/smc.py', 'a', encoding='utf-8') as f:
    f.write(code)
print("Successfully appended to smc.py")
