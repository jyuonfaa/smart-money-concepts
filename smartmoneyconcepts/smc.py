from functools import wraps
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from datetime import datetime

def inputvalidator(input_="ohlc"):
    def dfcheck(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            args = list(args)
            i = 0 if isinstance(args[0], pd.DataFrame) else 1

            args[i] = args[i].rename(columns={c: c.lower() for c in args[i].columns})

            inputs = {
                "o": "open",
                "h": "high",
                "l": "low",
                "c": kwargs.get("column", "close").lower(),
                "v": "volume",
            }

            if inputs["c"] != "close":
                kwargs["column"] = inputs["c"]

            for l in input_:
                if inputs[l] not in args[i].columns:
                    raise LookupError(
                        'Must have a dataframe column named "{0}"'.format(inputs[l])
                    )

            return func(*args, **kwargs)

        return wrap

    return dfcheck


def apply(decorator):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))

        return cls

    return decorate


@apply(inputvalidator(input_="ohlc"))
class smc:
    __version__ = "0.0.27"

    @classmethod
    def fvg(cls, ohlc: DataFrame, join_consecutive=False) -> Series:
        """
        FVG - Fair Value Gap
        A fair value gap is when the previous high is lower than the next low if the current candle is bullish.
        Or when the previous low is higher than the next high if the current candle is bearish.

        parameters:
        join_consecutive: bool - if there are multiple FVG in a row then they will be merged into one using the highest top and the lowest bottom

        returns:
        FVG = 1 if bullish fair value gap, -1 if bearish fair value gap
        Top = the top of the fair value gap
        Bottom = the bottom of the fair value gap
        MitigatedIndex = the index of the candle that mitigated the fair value gap
        """

        fvg = np.where(
            (
                (ohlc["high"].shift(1) < ohlc["low"].shift(-1))
                & (ohlc["close"] > ohlc["open"])
            )
            | (
                (ohlc["low"].shift(1) > ohlc["high"].shift(-1))
                & (ohlc["close"] < ohlc["open"])
            ),
            np.where(ohlc["close"] > ohlc["open"], 1, -1),
            np.nan,
        )

        top = np.where(
            ~np.isnan(fvg),
            np.where(
                ohlc["close"] > ohlc["open"],
                ohlc["low"].shift(-1),
                ohlc["low"].shift(1),
            ),
            np.nan,
        )

        bottom = np.where(
            ~np.isnan(fvg),
            np.where(
                ohlc["close"] > ohlc["open"],
                ohlc["high"].shift(1),
                ohlc["high"].shift(-1),
            ),
            np.nan,
        )

        # if there are multiple consecutive fvg then join them together using the highest top and lowest bottom and the last index
        if join_consecutive:
            for i in range(len(fvg) - 1):
                if fvg[i] == fvg[i + 1]:
                    top[i + 1] = max(top[i], top[i + 1])
                    bottom[i + 1] = min(bottom[i], bottom[i + 1])
                    fvg[i] = top[i] = bottom[i] = np.nan

        mitigated_index = np.zeros(len(ohlc), dtype=np.int32)
        for i in np.where(~np.isnan(fvg))[0]:
            mask = np.zeros(len(ohlc), dtype=np.bool_)
            if fvg[i] == 1:
                mask = ohlc["low"][i + 2 :] <= top[i]
            elif fvg[i] == -1:
                mask = ohlc["high"][i + 2 :] >= bottom[i]
            if np.any(mask):
                j = np.argmax(mask) + i + 2
                mitigated_index[i] = j

        mitigated_index = np.where(np.isnan(fvg), np.nan, mitigated_index)

        return pd.concat(
            [
                pd.Series(fvg, name="FVG"),
                pd.Series(top, name="Top"),
                pd.Series(bottom, name="Bottom"),
                pd.Series(mitigated_index, name="MitigatedIndex"),
            ],
            axis=1,
        )

    @classmethod
    def swing_highs_lows(cls, ohlc: DataFrame, swing_length: int = 50) -> Series:
        """
        Swing Highs and Lows
        A swing high is when the current high is the highest high out of the swing_length amount of candles before and after.
        A swing low is when the current low is the lowest low out of the swing_length amount of candles before and after.

        parameters:
        swing_length: int - the amount of candles to look back and forward to determine the swing high or low

        returns:
        HighLow = 1 if swing high, -1 if swing low
        Level = the level of the swing high or low
        """

        swing_length *= 2
        # set the highs to 1 if the current high is the highest high in the last 5 candles and next 5 candles
        swing_highs_lows = np.where(
            ohlc["high"]
            == ohlc["high"].shift(-(swing_length // 2)).rolling(swing_length).max(),
            1,
            np.where(
                ohlc["low"]
                == ohlc["low"].shift(-(swing_length // 2)).rolling(swing_length).min(),
                -1,
                np.nan,
            ),
        )

        while True:
            positions = np.where(~np.isnan(swing_highs_lows))[0]

            if len(positions) < 2:
                break

            current = swing_highs_lows[positions[:-1]]
            next = swing_highs_lows[positions[1:]]

            highs = ohlc["high"].iloc[positions[:-1]].values
            lows = ohlc["low"].iloc[positions[:-1]].values

            next_highs = ohlc["high"].iloc[positions[1:]].values
            next_lows = ohlc["low"].iloc[positions[1:]].values

            index_to_remove = np.zeros(len(positions), dtype=bool)

            consecutive_highs = (current == 1) & (next == 1)
            index_to_remove[:-1] |= consecutive_highs & (highs < next_highs)
            index_to_remove[1:] |= consecutive_highs & (highs >= next_highs)

            consecutive_lows = (current == -1) & (next == -1)
            index_to_remove[:-1] |= consecutive_lows & (lows > next_lows)
            index_to_remove[1:] |= consecutive_lows & (lows <= next_lows)

            if not index_to_remove.any():
                break

            swing_highs_lows[positions[index_to_remove]] = np.nan

        positions = np.where(~np.isnan(swing_highs_lows))[0]

        if len(positions) > 0:
            if swing_highs_lows[positions[0]] == 1:
                swing_highs_lows[0] = -1
            if swing_highs_lows[positions[0]] == -1:
                swing_highs_lows[0] = 1
            if swing_highs_lows[positions[-1]] == -1:
                swing_highs_lows[-1] = 1
            if swing_highs_lows[positions[-1]] == 1:
                swing_highs_lows[-1] = -1

        level = np.where(
            ~np.isnan(swing_highs_lows),
            np.where(swing_highs_lows == 1, ohlc["high"], ohlc["low"]),
            np.nan,
        )

        return pd.concat(
            [
                pd.Series(swing_highs_lows, name="HighLow"),
                pd.Series(level, name="Level"),
            ],
            axis=1,
        )

    @classmethod
    def bos_choch(
        cls, ohlc: DataFrame, swing_highs_lows: DataFrame, close_break: bool = True
    ) -> Series:
        """
        BOS - Break of Structure
        CHoCH - Change of Character
        these are both indications of market structure changing

        parameters:
        swing_highs_lows: DataFrame - provide the dataframe from the swing_highs_lows function
        close_break: bool - if True then the break of structure will be mitigated based on the close of the candle otherwise it will be the high/low.

        returns:
        BOS = 1 if bullish break of structure, -1 if bearish break of structure
        CHOCH = 1 if bullish change of character, -1 if bearish change of character
        Level = the level of the break of structure or change of character
        BrokenIndex = the index of the candle that broke the level
        """

        swing_highs_lows = swing_highs_lows.copy()

        level_order = []
        highs_lows_order = []

        bos = np.zeros(len(ohlc), dtype=np.int32)
        choch = np.zeros(len(ohlc), dtype=np.int32)
        level = np.zeros(len(ohlc), dtype=np.float32)

        last_positions = []

        for i in range(len(swing_highs_lows["HighLow"])):
            if not np.isnan(swing_highs_lows["HighLow"][i]):
                level_order.append(swing_highs_lows["Level"][i])
                highs_lows_order.append(swing_highs_lows["HighLow"][i])
                if len(level_order) >= 4:
                    # bullish bos
                    bos[last_positions[-2]] = (
                        1
                        if (
                            np.all(highs_lows_order[-4:] == [-1, 1, -1, 1])
                            and np.all(
                                level_order[-4]
                                < level_order[-2]
                                < level_order[-3]
                                < level_order[-1]
                            )
                        )
                        else 0
                    )
                    level[last_positions[-2]] = (
                        level_order[-3] if bos[last_positions[-2]] != 0 else 0
                    )

                    # bearish bos
                    bos[last_positions[-2]] = (
                        -1
                        if (
                            np.all(highs_lows_order[-4:] == [1, -1, 1, -1])
                            and np.all(
                                level_order[-4]
                                > level_order[-2]
                                > level_order[-3]
                                > level_order[-1]
                            )
                        )
                        else bos[last_positions[-2]]
                    )
                    level[last_positions[-2]] = (
                        level_order[-3] if bos[last_positions[-2]] != 0 else 0
                    )

                    # bullish choch
                    choch[last_positions[-2]] = (
                        1
                        if (
                            np.all(highs_lows_order[-4:] == [-1, 1, -1, 1])
                            and np.all(
                                level_order[-1]
                                > level_order[-3]
                                > level_order[-4]
                                > level_order[-2]
                            )
                        )
                        else 0
                    )
                    level[last_positions[-2]] = (
                        level_order[-3]
                        if choch[last_positions[-2]] != 0
                        else level[last_positions[-2]]
                    )

                    # bearish choch
                    choch[last_positions[-2]] = (
                        -1
                        if (
                            np.all(highs_lows_order[-4:] == [1, -1, 1, -1])
                            and np.all(
                                level_order[-1]
                                < level_order[-3]
                                < level_order[-4]
                                < level_order[-2]
                            )
                        )
                        else choch[last_positions[-2]]
                    )
                    level[last_positions[-2]] = (
                        level_order[-3]
                        if choch[last_positions[-2]] != 0
                        else level[last_positions[-2]]
                    )

                last_positions.append(i)

        broken = np.zeros(len(ohlc), dtype=np.int32)
        for i in np.where(np.logical_or(bos != 0, choch != 0))[0]:
            mask = np.zeros(len(ohlc), dtype=np.bool_)
            # if the bos is 1 then check if the candles high has gone above the level
            if bos[i] == 1 or choch[i] == 1:
                mask = ohlc["close" if close_break else "high"][i + 2 :] > level[i]
            # if the bos is -1 then check if the candles low has gone below the level
            elif bos[i] == -1 or choch[i] == -1:
                mask = ohlc["close" if close_break else "low"][i + 2 :] < level[i]
            if np.any(mask):
                j = np.argmax(mask) + i + 2
                broken[i] = j
                # if there are any unbroken bos or choch that started before this one and ended after this one then remove them
                for k in np.where(np.logical_or(bos != 0, choch != 0))[0]:
                    if k < i and broken[k] >= j:
                        bos[k] = 0
                        choch[k] = 0
                        level[k] = 0

        # remove the ones that aren't broken
        for i in np.where(
            np.logical_and(np.logical_or(bos != 0, choch != 0), broken == 0)
        )[0]:
            bos[i] = 0
            choch[i] = 0
            level[i] = 0

        # replace all the 0s with np.nan
        bos = np.where(bos != 0, bos, np.nan)
        choch = np.where(choch != 0, choch, np.nan)
        level = np.where(level != 0, level, np.nan)
        broken = np.where(broken != 0, broken, np.nan)

        bos = pd.Series(bos, name="BOS")
        choch = pd.Series(choch, name="CHOCH")
        level = pd.Series(level, name="Level")
        broken = pd.Series(broken, name="BrokenIndex")

        return pd.concat([bos, choch, level, broken], axis=1)

    @classmethod
    def ob(
        cls,
        ohlc: DataFrame,
        swing_highs_lows: DataFrame,
        close_mitigation: bool = False,
    ) -> Series:
        """
        OB - Order Blocks
        This method detects order blocks when there is a high amount of market orders exist on a price range.

        parameters:
        swing_highs_lows: DataFrame - provide the dataframe from the swing_highs_lows function
        close_mitigation: bool - if True then the order block will be mitigated based on the close of the candle otherwise it will be the high/low.

        returns:
        OB = 1 if bullish order block, -1 if bearish order block
        Top = top of the order block
        Bottom = bottom of the order block
        OBVolume = volume + 2 last volumes amounts
        Percentage = strength of order block (min(highVolume, lowVolume)/max(highVolume, lowVolume))
        """

        ohlc_len = len(ohlc)
        _open = ohlc["open"].values
        _high = ohlc["high"].values
        _low = ohlc["low"].values
        _close = ohlc["close"].values
        _volume = ohlc["volume"].values
        swing_hl = swing_highs_lows["HighLow"].values

        # Pre-allocate arrays
        crossed = np.full(ohlc_len, False, dtype=bool)
        ob = np.zeros(ohlc_len, dtype=np.int32)
        top_arr = np.zeros(ohlc_len, dtype=np.float32)
        bottom_arr = np.zeros(ohlc_len, dtype=np.float32)
        obVolume = np.zeros(ohlc_len, dtype=np.float32)
        lowVolume = np.zeros(ohlc_len, dtype=np.float32)
        highVolume = np.zeros(ohlc_len, dtype=np.float32)
        percentage = np.zeros(ohlc_len, dtype=np.float32)
        mitigated_index = np.zeros(ohlc_len, dtype=np.int32)
        breaker = np.full(ohlc_len, False, dtype=bool)

        # Precompute swing indices (assumed sorted)
        swing_high_indices = np.flatnonzero(swing_hl == 1)
        swing_low_indices = np.flatnonzero(swing_hl == -1)

        # List to track active bullish order blocks
        active_bullish = []
        for i in range(ohlc_len):
            close_index = i
            # Update existing bullish OB
            for idx in active_bullish.copy():
                if breaker[idx]:
                    if _high[close_index] > top_arr[idx]:
                        # Reset this OB
                        ob[idx] = 0
                        top_arr[idx] = 0.0
                        bottom_arr[idx] = 0.0
                        obVolume[idx] = 0.0
                        lowVolume[idx] = 0.0
                        highVolume[idx] = 0.0
                        mitigated_index[idx] = 0
                        percentage[idx] = 0.0
                        active_bullish.remove(idx)
                else:
                    if ((not close_mitigation and _low[close_index] < bottom_arr[idx])
                        or (close_mitigation and min(_open[close_index], _close[close_index]) < bottom_arr[idx])):
                        breaker[idx] = True
                        mitigated_index[idx] = close_index - 1

            # Find last swing high index less than current candle (using binary search)
            pos = np.searchsorted(swing_high_indices, close_index)
            last_top_index = swing_high_indices[pos - 1] if pos > 0 else None

            if last_top_index is not None:
                if _close[close_index] > _high[last_top_index] and not crossed[last_top_index]:
                    crossed[last_top_index] = True
                    # Initialise with default values from previous candle
                    default_index = close_index - 1
                    obBtm = _high[default_index]
                    obTop = _low[default_index]
                    obIndex = default_index
                    # Look for a lower low between last_top_index and current candle
                    if close_index - last_top_index > 1:
                        start = last_top_index + 1
                        end = close_index  # up to but not including close_index
                        if end > start:
                            segment = _low[start:end]
                            min_val = segment.min()
                            # In case of ties, take the last occurrence
                            candidates = np.nonzero(segment == min_val)[0]
                            if candidates.size:
                                candidate_index = start + candidates[-1]
                                obBtm = _low[candidate_index]
                                obTop = _high[candidate_index]
                                obIndex = candidate_index
                    # Set bullish OB values
                    ob[obIndex] = 1
                    top_arr[obIndex] = obTop
                    bottom_arr[obIndex] = obBtm
                    vol_cur = _volume[close_index]
                    vol_prev1 = _volume[close_index - 1] if close_index >= 1 else 0.0
                    vol_prev2 = _volume[close_index - 2] if close_index >= 2 else 0.0
                    obVolume[obIndex] = vol_cur + vol_prev1 + vol_prev2
                    lowVolume[obIndex] = vol_prev2
                    highVolume[obIndex] = vol_cur + vol_prev1
                    max_vol = max(highVolume[obIndex], lowVolume[obIndex])
                    percentage[obIndex] = (min(highVolume[obIndex], lowVolume[obIndex]) / max_vol * 100.0) if max_vol != 0 else 100.0
                    active_bullish.append(obIndex)

        # List to track active bearish order blocks
        active_bearish = []
        for i in range(ohlc_len):
            close_index = i
            # Update existing bearish OB
            for idx in active_bearish.copy():
                if breaker[idx]:
                    if _low[close_index] < bottom_arr[idx]:
                        ob[idx] = 0
                        top_arr[idx] = 0.0
                        bottom_arr[idx] = 0.0
                        obVolume[idx] = 0.0
                        lowVolume[idx] = 0.0
                        highVolume[idx] = 0.0
                        mitigated_index[idx] = 0
                        percentage[idx] = 0.0
                        active_bearish.remove(idx)
                else:
                    if ((not close_mitigation and _high[close_index] > top_arr[idx])
                        or (close_mitigation and max(_open[close_index], _close[close_index]) > top_arr[idx])):
                        breaker[idx] = True
                        mitigated_index[idx] = close_index

            # Find last swing low index less than current candle
            pos = np.searchsorted(swing_low_indices, close_index)
            last_btm_index = swing_low_indices[pos - 1] if pos > 0 else None

            if last_btm_index is not None:
                if _close[close_index] < _low[last_btm_index] and not crossed[last_btm_index]:
                    crossed[last_btm_index] = True
                    default_index = close_index - 1
                    obTop = _high[default_index]
                    obBtm = _low[default_index]
                    obIndex = default_index
                    if close_index - last_btm_index > 1:
                        start = last_btm_index + 1
                        end = close_index
                        if end > start:
                            segment = _high[start:end]
                            max_val = segment.max()
                            candidates = np.nonzero(segment == max_val)[0]
                            if candidates.size:
                                candidate_index = start + candidates[-1]
                                obTop = _high[candidate_index]
                                obBtm = _low[candidate_index]
                                obIndex = candidate_index
                    ob[obIndex] = -1
                    top_arr[obIndex] = obTop
                    bottom_arr[obIndex] = obBtm
                    vol_cur = _volume[close_index]
                    vol_prev1 = _volume[close_index - 1] if close_index >= 1 else 0.0
                    vol_prev2 = _volume[close_index - 2] if close_index >= 2 else 0.0
                    obVolume[obIndex] = vol_cur + vol_prev1 + vol_prev2
                    lowVolume[obIndex] = vol_cur + vol_prev1
                    highVolume[obIndex] = vol_prev2
                    max_vol = max(highVolume[obIndex], lowVolume[obIndex])
                    percentage[obIndex] = (min(highVolume[obIndex], lowVolume[obIndex]) / max_vol * 100.0) if max_vol != 0 else 100.0
                    active_bearish.append(obIndex)

        # Convert zeros to NaN where OB was not set
        ob = np.where(ob != 0, ob, np.nan)
        top_arr = np.where(~np.isnan(ob), top_arr, np.nan)
        bottom_arr = np.where(~np.isnan(ob), bottom_arr, np.nan)
        obVolume = np.where(~np.isnan(ob), obVolume, np.nan)
        mitigated_index = np.where(~np.isnan(ob), mitigated_index, np.nan)
        percentage = np.where(~np.isnan(ob), percentage, np.nan)

        ob_series = pd.Series(ob, name="OB")
        top_series = pd.Series(top_arr, name="Top")
        bottom_series = pd.Series(bottom_arr, name="Bottom")
        obVolume_series = pd.Series(obVolume, name="OBVolume")
        mitigated_index_series = pd.Series(mitigated_index, name="MitigatedIndex")
        percentage_series = pd.Series(percentage, name="Percentage")

        return pd.concat(
            [
                ob_series,
                top_series,
                bottom_series,
                obVolume_series,
                mitigated_index_series,
                percentage_series,
            ],
            axis=1,
        )

    @classmethod
    def liquidity(cls, ohlc: DataFrame, swing_highs_lows: DataFrame, range_percent: float = 0.01) -> Series:
        """
        Liquidity
        Liquidity is when there are multiple highs within a small range of each other,
        or multiple lows within a small range of each other.

        parameters:
        swing_highs_lows: DataFrame - provide the dataframe from the swing_highs_lows function
        range_percent: float - the percentage of the range to determine liquidity

        returns:
        Liquidity = 1 if bullish liquidity, -1 if bearish liquidity
        Level = the level of the liquidity
        End = the index of the last liquidity level
        Swept = the index of the candle that swept the liquidity
        """

        # Work on a copy so the original is not modified.
        shl = swing_highs_lows.copy()
        n = len(ohlc)
        
        # Calculate the pip range based on the overall high-low range.
        pip_range = (ohlc["high"].max() - ohlc["low"].min()) * range_percent

        # Preconvert required columns to numpy arrays.
        ohlc_high = ohlc["high"].values
        ohlc_low = ohlc["low"].values
        # Make a copy to allow in-place marking of used candidates.
        shl_HL = shl["HighLow"].values.copy()
        shl_Level = shl["Level"].values.copy()

        # Initialise output arrays with NaN (to match later replacement of zeros).
        liquidity = np.full(n, np.nan, dtype=np.float32)
        liquidity_level = np.full(n, np.nan, dtype=np.float32)
        liquidity_end = np.full(n, np.nan, dtype=np.float32)
        liquidity_swept = np.full(n, np.nan, dtype=np.float32)
        is_too_clean = np.full(n, 0, dtype=np.int32)

        # Process bullish liquidity (HighLow == 1)
        bull_indices = np.nonzero(shl_HL == 1)[0]
        for i in bull_indices:
            # Skip if this candidate has already been used.
            if shl_HL[i] != 1:
                continue
            high_level = shl_Level[i]
            range_low = high_level - pip_range
            range_high = high_level + pip_range
            group_levels = [high_level]
            group_end = i

            # Determine the swept index:
            # Find the first candle after i where the high reaches or exceeds range_high.
            c_start = i + 1
            if c_start < n:
                cond = ohlc_high[c_start:] >= range_high
                if np.any(cond):
                    swept = c_start + int(np.argmax(cond))
                else:
                    swept = 0
            else:
                swept = 0

            # Iterate only over candidate indices greater than i.
            for j in bull_indices:
                if j <= i:
                    continue
                # Emulate the inner loop break: if we've reached or passed the swept index, stop.
                if swept and j >= swept:
                    break
                # If candidate j is within the liquidity range, add it and mark it as used.
                if shl_HL[j] == 1 and (range_low <= shl_Level[j] <= range_high):
                    group_levels.append(shl_Level[j])
                    group_end = j
                    shl_HL[j] = 0  # mark candidate as used
            # Only record liquidity if more than one candidate is grouped.
            if len(group_levels) > 1:
                liquidity[i] = 1
                liquidity_level[i] = sum(group_levels) / len(group_levels)
                liquidity_end[i] = group_end
                liquidity_swept[i] = swept
                # Video 3: Too Clean (Equal Highs) - Loosened threshold
                if np.std(group_levels) < (pip_range * 0.5):
                    is_too_clean[i] = 1
                    # Store zone range
                    liquidity_level[i] = min(group_levels) # Bot of zone
                    liquidity_end[i] = max(group_levels)   # Top of zone

        # Process bearish liquidity (HighLow == -1)
        bear_indices = np.nonzero(shl_HL == -1)[0]
        for i in bear_indices:
            if shl_HL[i] != -1:
                continue
            low_level = shl_Level[i]
            range_low = low_level - pip_range
            range_high = low_level + pip_range
            group_levels = [low_level]
            group_end = i

            # Find the first candle after i where the low reaches or goes below range_low.
            c_start = i + 1
            if c_start < n:
                cond = ohlc_low[c_start:] <= range_low
                if np.any(cond):
                    swept = c_start + int(np.argmax(cond))
                else:
                    swept = 0
            else:
                swept = 0

            for j in bear_indices:
                if j <= i:
                    continue
                if swept and j >= swept:
                    break
                if shl_HL[j] == -1 and (range_low <= shl_Level[j] <= range_high):
                    group_levels.append(shl_Level[j])
                    group_end = j
                    shl_HL[j] = 0
            if len(group_levels) > 1:
                liquidity[i] = -1
                liquidity_level[i] = sum(group_levels) / len(group_levels)
                liquidity_end[i] = group_end
                liquidity_swept[i] = swept
                # Video 3: Too Clean (Equal Lows) - Loosened threshold
                if np.std(group_levels) < (pip_range * 0.5):
                    is_too_clean[i] = 1
                    # Store the zone range in level and end columns for the visualizer
                    liquidity_level[i] = min(group_levels) # Bot of zone
                    liquidity_end[i] = max(group_levels)   # Top of zone

        # Convert arrays to Series with the proper names.
        liq_series = pd.Series(liquidity, name="Liquidity")
        level_series = pd.Series(liquidity_level, name="Level") # Zone Bottom for Clean
        end_series = pd.Series(liquidity_end, name="End")       # Zone Top for Clean
        swept_series = pd.Series(liquidity_swept, name="Swept")
        clean_series = pd.Series(is_too_clean, name="IsTooClean")

        return pd.concat([liq_series, level_series, end_series, swept_series, clean_series], axis=1)

    @classmethod
    def previous_high_low(cls, ohlc: DataFrame, time_frame: str = "1D") -> DataFrame:
        """
        Previous High Low
        This method returns the previous high and low of the given time frame.

        parameters:
        time_frame: str - the time frame to get the previous high and low 15m, 1H, 4H, 1D, 1W, 1M

        returns:
        PreviousHigh = the previous high
        PreviousLow = the previous low
        BrokenHigh = 1 once price has broken the previous high of the timeframe, 0 otherwise
        BrokenLow = 1 once price has broken the previous low of the timeframe, 0 otherwise
        """
        ohlc = ohlc.copy()
        ohlc.index = pd.to_datetime(ohlc.index)
        n = len(ohlc)

        # Resample to target timeframe
        resampled = ohlc.resample(time_frame).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()

        # Edge case: not enough resampled periods
        if len(resampled) < 2:
            return pd.concat([
                pd.Series(np.full(n, np.nan, dtype=np.float32), name="PreviousHigh"),
                pd.Series(np.full(n, np.nan, dtype=np.float32), name="PreviousLow"),
                pd.Series(np.zeros(n, dtype=np.int32), name="BrokenHigh"),
                pd.Series(np.zeros(n, dtype=np.int32), name="BrokenLow"),
            ], axis=1)

        resampled_times = resampled.index.values
        resampled_highs = resampled["high"].values
        resampled_lows = resampled["low"].values
        candle_times = ohlc.index.values

        # For each candle, find how many resampled periods have start time < candle time
        # This is equivalent to: len(np.where(resampled_times < candle_time)[0])
        periods_before = np.searchsorted(resampled_times, candle_times, side='left')

        # Original takes second-to-last: indices[-2] = periods_before - 2
        prev_period_idx = periods_before - 2

        # Valid only if more than 1 period before (original: len > 1, i.e., >= 2 periods)
        valid_mask = periods_before > 1

        # Initialize output arrays
        previous_high = np.full(n, np.nan, dtype=np.float32)
        previous_low = np.full(n, np.nan, dtype=np.float32)

        # Fill valid entries
        valid_indices = np.where(valid_mask)[0]
        if len(valid_indices) > 0:
            lookup_indices = prev_period_idx[valid_indices]
            previous_high[valid_indices] = resampled_highs[lookup_indices]
            previous_low[valid_indices] = resampled_lows[lookup_indices]

        # Group candles by their reference period for cumulative broken tracking
        # Original resets broken flags when the reference period changes
        group_changes = np.concatenate([[True], prev_period_idx[1:] != prev_period_idx[:-1]])
        group_id = np.cumsum(group_changes)

        ohlc_high = ohlc["high"].values
        ohlc_low = ohlc["low"].values

        # Compute cumulative max/min within each group
        df_temp = pd.DataFrame({
            'group': group_id,
            'high': ohlc_high,
            'low': ohlc_low,
        })

        cummax_high = df_temp.groupby('group')['high'].cummax().values
        cummin_low = df_temp.groupby('group')['low'].cummin().values

        # Broken = 1 if cumulative high > previous_high (or cummin < previous_low)
        broken_high = np.where(valid_mask & (cummax_high > previous_high), 1, 0).astype(np.int32)
        broken_low = np.where(valid_mask & (cummin_low < previous_low), 1, 0).astype(np.int32)

        return pd.concat([
            pd.Series(previous_high, name="PreviousHigh"),
            pd.Series(previous_low, name="PreviousLow"),
            pd.Series(broken_high, name="BrokenHigh"),
            pd.Series(broken_low, name="BrokenLow"),
        ], axis=1)
    
    @classmethod
    def sessions(
        cls,
        ohlc: DataFrame,
        session: str,
        start_time: str = "",
        end_time: str = "",
        time_zone: str = "UTC",
    ) -> Series:
        """
        Sessions
        This method returns wwhich candles are within the session specified

        parameters:
        session: str - the session you want to check (Sydney, Tokyo, London, New York, Asian kill zone, London open kill zone, New York kill zone, london close kill zone, Custom)
        start_time: str - the start time of the session in the format "HH:MM" only required for custom session.
        end_time: str - the end time of the session in the format "HH:MM" only required for custom session.
        time_zone: str - the time zone of the candles can be in the format "UTC+0" or "GMT+0"

        returns:
        Active = 1 if the candle is within the session, 0 if not
        High = the highest point of the session
        Low = the lowest point of the session
        """

        if session == "Custom" and (start_time == "" or end_time == ""):
            raise ValueError("Custom session requires a start and end time")

        default_sessions = {
            "Sydney": {
                "start": "21:00",
                "end": "06:00",
            },
            "Tokyo": {
                "start": "00:00",
                "end": "09:00",
            },
            "London": {
                "start": "07:00",
                "end": "16:00",
            },
            "New York": {
                "start": "13:00",
                "end": "22:00",
            },
            "Asian kill zone": {
                "start": "00:00",
                "end": "04:00",
            },
            "London open kill zone": {
                "start": "6:00",
                "end": "9:00",
            },
            "New York kill zone": {
                "start": "11:00",
                "end": "14:00",
            },
            "london close kill zone": {
                "start": "14:00",
                "end": "16:00",
            },
            "Custom": {
                "start": start_time,
                "end": end_time,
            },
        }

        ohlc.index = pd.to_datetime(ohlc.index)
        if time_zone != "UTC":
            time_zone = time_zone.replace("GMT", "Etc/GMT")
            time_zone = time_zone.replace("UTC", "Etc/GMT")
            ohlc.index = ohlc.index.tz_localize(time_zone).tz_convert("UTC")

        start_time = datetime.strptime(
            default_sessions[session]["start"], "%H:%M"
        ).strftime("%H:%M")
        start_time = datetime.strptime(start_time, "%H:%M")
        end_time = datetime.strptime(
            default_sessions[session]["end"], "%H:%M"
        ).strftime("%H:%M")
        end_time = datetime.strptime(end_time, "%H:%M")

        # if the candles are between the start and end time then it is an active session
        active = np.zeros(len(ohlc), dtype=np.int32)
        high = np.zeros(len(ohlc), dtype=np.float32)
        low = np.zeros(len(ohlc), dtype=np.float32)

        for i in range(len(ohlc)):
            current_time = ohlc.index[i].strftime("%H:%M")
            # convert current time to the second of the day
            current_time = datetime.strptime(current_time, "%H:%M")
            if (start_time < end_time and start_time <= current_time <= end_time) or (
                start_time >= end_time
                and (start_time <= current_time or current_time <= end_time)
            ):
                active[i] = 1
                high[i] = max(ohlc["high"].iloc[i], high[i - 1] if i > 0 else 0)
                low[i] = min(
                    ohlc["low"].iloc[i],
                    low[i - 1] if i > 0 and low[i - 1] != 0 else float("inf"),
                )

        active = pd.Series(active, name="Active")
        high = pd.Series(high, name="High")
        low = pd.Series(low, name="Low")

        return pd.concat([active, high, low], axis=1)

    @classmethod
    def retracements(cls, ohlc: DataFrame, swing_highs_lows: DataFrame) -> Series:
        """
        Retracement
        This method returns the percentage of a retracement from the swing high or low

        parameters:
        swing_highs_lows: DataFrame - provide the dataframe from the swing_highs_lows function

        returns:
        Direction = 1 if bullish retracement, -1 if bearish retracement
        CurrentRetracement% = the current retracement percentage from the swing high or low
        DeepestRetracement% = the deepest retracement percentage from the swing high or low
        """

        swing_highs_lows = swing_highs_lows.copy()

        direction = np.zeros(len(ohlc), dtype=np.int32)
        current_retracement = np.zeros(len(ohlc), dtype=np.float64)
        deepest_retracement = np.zeros(len(ohlc), dtype=np.float64)

        top = 0
        bottom = 0
        for i in range(len(ohlc)):
            if swing_highs_lows["HighLow"][i] == 1:
                direction[i] = 1
                top = swing_highs_lows["Level"][i]
                # deepest_retracement[i] = 0
            elif swing_highs_lows["HighLow"][i] == -1:
                direction[i] = -1
                bottom = swing_highs_lows["Level"][i]
                # deepest_retracement[i] = 0
            else:
                direction[i] = direction[i - 1] if i > 0 else 0

            if direction[i - 1] == 1:
                divisor = top - bottom
                current_retracement[i] = round(
                    100 - (((ohlc["low"].iloc[i] - bottom) / divisor) * 100) if divisor != 0 else 0, 1
                )
                deepest_retracement[i] = max(
                    (
                        deepest_retracement[i - 1]
                        if i > 0 and direction[i - 1] == 1
                        else 0
                    ),
                    current_retracement[i],
                )
            if direction[i] == -1:
                divisor = bottom - top
                current_retracement[i] = round(
                    100 - ((ohlc["high"].iloc[i] - top) / divisor) * 100 if divisor != 0 else 0, 1
                )
                deepest_retracement[i] = max(
                    (
                        deepest_retracement[i - 1]
                        if i > 0 and direction[i - 1] == -1
                        else 0
                    ),
                    current_retracement[i],
                )

        # shift the arrays by 1
        current_retracement = np.roll(current_retracement, 1)
        deepest_retracement = np.roll(deepest_retracement, 1)
        direction = np.roll(direction, 1)

        # remove the first 3 retracements as they get calculated incorrectly due to not enough data
        remove_first_count = 0
        for i in range(len(direction)):
            if i + 1 == len(direction):
                break
            if direction[i] != direction[i + 1]:
                remove_first_count += 1
            direction[i] = 0
            current_retracement[i] = 0
            deepest_retracement[i] = 0
            if remove_first_count == 3:
                direction[i + 1] = 0
                current_retracement[i + 1] = 0
                deepest_retracement[i + 1] = 0
                break

        direction = pd.Series(direction, name="Direction")
        current_retracement = pd.Series(current_retracement, name="CurrentRetracement%")
        deepest_retracement = pd.Series(deepest_retracement, name="DeepestRetracement%")
        
    @classmethod
    def consolidation(
        cls,
        ohlc: pd.DataFrame,
        prd: int = 10,
        conslen: int = 5,
    ) -> pd.DataFrame:
        """
        Consolidation Zones - Live
        Direct Python translation of LonesomeTheBlue's Pine Script.
        Uses ZigZag pivot counting — NOT ATR or rolling window.

        How it works:
        1. Find significant pivot highs/lows using lookback period (prd)
        2. Track the most extreme pivot in the current direction (pp)
        3. Every bar, increment conscnt
        4. When pp changes AND moves OUTSIDE the range → RESET (breakout)
        5. When pp changes AND stays INSIDE the range → keep counting
        6. When conscnt >= conslen → consolidation confirmed, draw the box
        7. Box boundaries expand dynamically as new highs/lows form inside
        """
        ohlc = ohlc.copy()
        n    = len(ohlc)
        high = ohlc["high"].values
        low  = ohlc["low"].values
        # Video 3: Consolidation defined by bodies, not wicks
        body_high = np.maximum(ohlc["open"].values, ohlc["close"].values)
        body_low  = np.minimum(ohlc["open"].values, ohlc["close"].values)

        # ── Step 1: Find pivot highs and lows ──────────────────────────
        # Pine: highestbars(prd) == 0  →  current bar is highest in last prd bars
        # Pine: lowestbars(prd)  == 0  →  current bar is lowest  in last prd bars
        hb_ = np.full(n, np.nan)
        lb_ = np.full(n, np.nan)

        for i in range(prd, n):
            window_high = high[i - prd: i + 1]
            window_low  = low[i  - prd: i + 1]
            if high[i] >= np.max(window_high):
                hb_[i] = high[i]
            if low[i]  <= np.min(window_low):
                lb_[i] = low[i]

        # ── Step 2: Direction + ZigZag ─────────────────────────────────
        # Pine: dir := iff(hb_ and na(lb_), 1, iff(lb_ and na(hb_), -1, dir))
        direction = np.zeros(n, dtype=int)
        zz        = np.full(n, np.nan)
        dir_val   = 0

        for i in range(n):
            has_hb = not np.isnan(hb_[i])
            has_lb = not np.isnan(lb_[i])

            if   has_hb and not has_lb: dir_val = 1
            elif has_lb and not has_hb: dir_val = -1

            if has_hb and has_lb:
                zz[i] = hb_[i] if dir_val == 1 else lb_[i]
            elif has_hb: zz[i] = hb_[i]
            elif has_lb: zz[i] = lb_[i]

            direction[i] = dir_val

        # ── Step 3: Track pp (most extreme pivot in current direction) ─
        # Pine loops back 1000 bars to find the highest/lowest zz in same dir
        pp = np.full(n, np.nan)

        for i in range(n):
            pp_val = np.nan
            for x in range(min(i + 1, 1001)):
                idx = i - x
                if direction[idx] != direction[i]:
                    break
                if not np.isnan(zz[idx]):
                    if np.isnan(pp_val):
                        pp_val = zz[idx]
                    elif direction[i] == 1  and zz[idx] > pp_val:
                        pp_val = zz[idx]
                    elif direction[i] == -1 and zz[idx] < pp_val:
                        pp_val = zz[idx]
            pp[i] = pp_val

        # ── Step 4: Consolidation counting ─────────────────────────────
        # Pine: change(pp) → pp changed from previous bar
        conscnt  = 0
        condhigh = np.nan
        condlow  = np.nan

        cons_out      = np.full(n, np.nan)
        top_out       = np.full(n, np.nan)
        bot_out       = np.full(n, np.nan)
        eq_out        = np.full(n, np.nan)
        ote_h_out     = np.full(n, np.nan)
        ote_l_out     = np.full(n, np.nan)
        break_up_out  = np.full(n, np.nan)
        break_dn_out  = np.full(n, np.nan)

        for i in range(1, n):
            # H_ = highest body high of last conslen bars
            # L_ = lowest  body low  of last conslen bars
            start = max(0, i - conslen + 1)
            H_    = np.max(body_high[start: i + 1])
            L_    = np.min(body_low[start:  i + 1])

            pp_changed = pp[i] != pp[i - 1] and not (
                np.isnan(pp[i]) and np.isnan(pp[i - 1])
            )

            if pp_changed:
                # Check for breakout BEFORE updating count
                if conscnt > conslen:
                    if not np.isnan(pp[i]):
                        if pp[i] > condhigh:
                            break_up_out[i] = 1.0
                        if pp[i] < condlow:
                            break_dn_out[i] = -1.0

                # Stay in range → keep counting | break range → reset
                if (conscnt > 0
                        and not np.isnan(condhigh)
                        and not np.isnan(pp[i])
                        and pp[i] <= condhigh
                        and pp[i] >= condlow):
                    conscnt += 1
                else:
                    conscnt = 0
            else:
                conscnt += 1  # pp unchanged → just count the bar

            # Draw / expand the box
            if conscnt >= conslen:
                if conscnt == conslen:          # first bar — initialise
                    condhigh = H_
                    condlow  = L_
                else:                           # expand to include new body extremes
                    condhigh = max(condhigh, body_high[i])
                    condlow  = min(condlow,  body_low[i])

                if conscnt > conslen:
                    rng = condhigh - condlow
                    cons_out[i]  = 1.0
                    top_out[i]   = condhigh
                    bot_out[i]   = condlow
                    eq_out[i]    = condhigh - rng * 0.50
                    ote_h_out[i] = condhigh - rng * 0.62
                    ote_l_out[i] = condhigh - rng * 0.79

        return pd.DataFrame({
            "Consolidation": cons_out,
            "Top":           top_out,
            "Bottom":        bot_out,
            "Equilibrium":   eq_out,
            "OTE_High":      ote_h_out,
            "OTE_Low":       ote_l_out,
            "BreakLong":     break_up_out,
            "BreakShort":    break_dn_out,
        }, index=ohlc.index)

    @classmethod
    def expansion(
        cls,
        ohlc: pd.DataFrame,
        consolidation: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        ICT Expansion detector.
        Detects when price body closes beyond the consolidation boundary.
        Identifies the direction and the source Order Block.
        """
        ohlc = ohlc.copy()
        
        # Expansion occurs when a candle closes outside the previous candle's consolidation box
        # We use .shift(1) because we are looking at the breakout of a *previously confirmed* range
        prev_top = consolidation["Top"].shift(1)
        prev_bottom = consolidation["Bottom"].shift(1)
        was_consolidating = consolidation["Consolidation"].shift(1).notna()
        
        bullish_break = (ohlc["close"] > prev_top) & was_consolidating
        bearish_break = (ohlc["close"] < prev_bottom) & was_consolidating
        
        # Filter to only show the FIRST candle that breaks out
        # (Wait, ICT might want to keep the state as expansion until it retraces. 
        # But for detection of the SIGNAL, we want the first break.)
        # The briefing pseudologic: expansion_bullish = body_close_above_top & consolidation["Consolidation"].shift().notna()
        # This will stay true for multiple candles if they all close above the *original* top?
        # No, usually consolidation["Top"] becomes NaN after expansion confirms.
        
        expansion_result = np.where(bullish_break, 1.0, np.where(bearish_break, -1.0, np.nan))
        
        # Identify Order Block: The last opposing candle inside the range
        # For bullish expansion, find the last bearish candle body inside the range [Bottom, Top] 
        # before the expansion candle index.
        ob_top = np.full(len(ohlc), np.nan)
        ob_bottom = np.full(len(ohlc), np.nan)
        
        for i in np.where(~np.isnan(expansion_result))[0]:
            # Look backwards from expansion candle i
            top_val = prev_top.iloc[i]
            btm_val = prev_bottom.iloc[i]
            eq_val = consolidation["Equilibrium"].iloc[i] # The 50% level
            
            if np.isnan(eq_val): continue
            
            # Find the last opposing candle
            found_ob = False
            for j in range(i - 1, max(0, i - 50), -1):
                is_bullish_candle = ohlc["close"].iloc[j] > ohlc["open"].iloc[j]
                is_bearish_candle = ohlc["close"].iloc[j] < ohlc["open"].iloc[j]
                
                # Was it inside the range? (Using bodies)
                body_h = max(ohlc["open"].iloc[j], ohlc["close"].iloc[j])
                body_l = min(ohlc["open"].iloc[j], ohlc["close"].iloc[j])
                
                if expansion_result[i] == 1.0: # Bullish expansion
                    if is_bearish_candle: # Looking for last bearish candle
                        # ICT Equilibrium Filter: Bullish OB must be in DISCOUNT (below 50%)
                        if ohlc["high"].iloc[j] <= eq_val:
                            ob_top[i] = ohlc["high"].iloc[j]
                            ob_bottom[i] = ohlc["low"].iloc[j]
                            found_ob = True
                            break
                else: # Bearish expansion
                    if is_bullish_candle: # Looking for last bullish candle
                        # ICT Equilibrium Filter: Bearish OB must be in PREMIUM (above 50%)
                        if ohlc["low"].iloc[j] >= eq_val:
                            ob_top[i] = ohlc["high"].iloc[j]
                            ob_bottom[i] = ohlc["low"].iloc[j]
                            found_ob = True
                            break
                        
                # If we exit the range without finding an opposing candle (rare), stop
                if body_h > top_val or body_l < btm_val:
                    break
                    
        return pd.DataFrame({
            "Expansion": expansion_result,
            "OB_Top":    ob_top,
            "OB_Top":    ob_top,
            "OB_Bottom": ob_bottom,
        }, index=ohlc.index)

    @classmethod
    def displacement(
        cls,
        ohlc: pd.DataFrame,
        lookback: int = 50, # Reduced lookback for local volatility sensitivity
        range_p: float = 90.0, # Top 10% of size
        body_p: float = 75.0, # Top 25% of body ratio
    ) -> pd.DataFrame:
        """
        ICT Displacement (Speed) Detector.
        Uses statistical percentiles to identify "Real Big Candles" relative to environment.
        
        Logic: 
        1. Range > range_p percentile of recent ranges.
        2. Body-to-Range ratio > body_p percentile of recent ratios.
        """
        ohlc = ohlc.copy()
        n = len(ohlc)
        
        candle_range = (ohlc["high"] - ohlc["low"]).values
        body_size = (ohlc["close"] - ohlc["open"]).abs().values
        body_ratio = np.divide(body_size, candle_range, out=np.zeros_like(body_size), where=candle_range!=0)
        
        displacement = np.zeros(n, dtype=np.float32)
        
        for i in range(lookback, n):
            # Calculate percentiles for the local window
            window_ranges = candle_range[i-lookback:i]
            window_ratios = body_ratio[i-lookback:i]
            
            range_threshold = np.percentile(window_ranges, range_p)
            ratio_threshold = np.percentile(window_ratios, body_p)
            
            is_big = candle_range[i] > range_threshold
            is_strong = body_ratio[i] > ratio_threshold
            
            if is_big and is_strong:
                # Direction of displacement
                displacement[i] = 1.0 if ohlc["close"].iloc[i] > ohlc["open"].iloc[i] else -1.0
                
        return pd.DataFrame({
            "Displacement": displacement,
            "Range_90p": pd.Series(candle_range).rolling(lookback).apply(lambda x: np.percentile(x, range_p)),
            "BodyRatio_80p": pd.Series(body_ratio).rolling(lookback).apply(lambda x: np.percentile(x, body_p))
        }, index=ohlc.index)









    @classmethod
    def swing_highs_lows_v4(cls, ohlc):
        """
        ICT Video 4: Religious 4-Candle confirmation with Strict Alternation.
        Ensures H -> L -> H sequence only. Discards duplicates.
        """
        import pandas as pd
        df = ohlc.copy()
        is_sunday = df.index.dayofweek == 6
        df_v = df[~is_sunday].copy()
        h, l, c = df_v['high'].values, df_v['low'].values, df_v['close'].values
        idx = df_v.index
        
        final = []
        last_confirmed_type = None
        raw_count = 0
        
        for i in range(2, len(df_v) - 2):
            # 1. Check for High Confirmation (i+2 rule)
            if h[i] > h[i-1] and h[i] > h[i+1]:
                if c[i+2] < c[i+1]:
                    raw_count += 1
                    if last_confirmed_type != "HIGH":
                        final.append({'ts': idx[i], 'conf_ts': idx[i+2], 'type': 'HIGH', 'p': h[i], 'label': 'High Down Move Confirmed'})
                        last_confirmed_type = "HIGH"

            # 2. Check for Low Confirmation (i+2 rule)
            if l[i] < l[i-1] and l[i] < l[i+1]:
                if c[i+2] > c[i+1]:
                    raw_count += 1
                    if last_confirmed_type != "LOW":
                        final.append({'ts': idx[i], 'conf_ts': idx[i+2], 'type': 'LOW', 'p': l[i], 'label': 'Low Up Move Confirmed'})
                        last_confirmed_type = "LOW"
        
        # --- VERIFICATION (Fix 3) ---
        final_count = len(final)
        signal_sequence = [f"{s['type'][0]}" for s in final]
        print(f"VERIFICATION: DEDUPLICATION [{ohlc.index.name or 'Asset'}]")
        print(f"Total raw signals before dedup: {raw_count}")
        print(f"Total signals after strict alternation: {final_count}")
        print(f"Signals discarded: {raw_count - final_count}")
        print(f"Signal sequence: {signal_sequence}")
        
        return pd.DataFrame(final)

    @classmethod
    def identify_order_block(cls, ohlc, confirmed_swings):
        import pandas as pd
        if confirmed_swings.empty: return pd.DataFrame()
        obs = []
        for i in range(1, len(confirmed_swings)):
            curr = confirmed_swings.iloc[i]
            prev = confirmed_swings.iloc[i-1]
            if curr['type'] == 'HIGH' and prev['type'] == 'LOW':
                sub = ohlc.loc[prev['ts']:curr['ts']]
                down_candles = sub[sub['close'] < sub['open']]
                if not down_candles.empty:
                    ob_row = down_candles.iloc[0]
                    obs.append({'ts': ob_row.name, 'type': 'BULLISH_OB', 'high': ob_row['high'], 'low': ob_row['low']})
        return pd.DataFrame(obs)


# ================================================================
# SMT DIVERGENCE — module-level functions (bypass @apply decorator)
# ICT Month 3, Video 5 — Institutional Market Structure, pp.216–226
#
# CRITICAL: These are intentionally at MODULE LEVEL (zero indent),
# OUTSIDE the smc class. Monkey-patched onto smc at the bottom.
# Do NOT move inside the class — @apply(inputvalidator) would wrap
# them and break the calling convention on Python 3.11+.
# ================================================================


def _smt_divergence(
    ohlc,
    benchmark_ohlc,
    asset_swings,
    correlation="inverse",
    lookaround_bars=5,
    fvg_df=None,
    liquidity_df=None,
):
    """
    ICT Month 3, Video 5 — Institutional Market Structure (SMT Divergence).

    Detects all four non-symmetrical divergence scenarios between a primary
    asset and its correlated/inversely-correlated benchmark, plus symmetrical
    trend-confirmation conditions.

    Gap 1 (p.222): FVG void on benchmark confirmed as closed-in.
    Gap 2 (p.226): Use smt_apply_bias_filter() to gate ob()/ny_midnight_open().

    Parameters
    ----------
    ohlc            : OHLC of the primary asset (e.g. AUDUSD)
    benchmark_ohlc  : OHLC of the benchmark (DXY for inverse correlation)
    asset_swings    : output of smc.swing_highs_lows_v4() on ohlc
                      Required columns: 'type' ('HIGH'/'LOW'), 'ts', 'p'
    correlation     : "inverse" (DXY) | "positive" (e.g. GBPUSD vs EURUSD)
    lookaround_bars : bars either side of a swing to search for extremes
    fvg_df          : optional pre-computed FVG df (backward-compat)
    liquidity_df    : optional Liquidity df for sweep-gate confirmation

    Returns
    -------
    pd.DataFrame indexed like ohlc. Columns:
        smt_bias, smt_bullish_div, smt_bearish_div,
        smt_bullish_div_bm, smt_bearish_div_bm,
        smt_trend_confirmed, smt_trend_direction,
        smt_swept_high, smt_swept_low,
        smt_confirmed, smt_at_liquidity, smt_bias_event
    """
    asset_ohlc = ohlc

    df = pd.DataFrame(index=asset_ohlc.index)
    df['smt_bias']            = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
    df['smt_bullish_div']     = False
    df['smt_bearish_div']     = False
    df['smt_bullish_div_bm']  = False
    df['smt_bearish_div_bm']  = False
    df['smt_trend_confirmed'] = False
    df['smt_trend_direction'] = pd.Series('NEUTRAL', index=asset_ohlc.index, dtype='object')
    df['smt_swept_high']      = np.nan
    df['smt_swept_low']       = np.nan
    df['smt_confirmed']       = False
    df['smt_at_liquidity']    = False
    df['smt_bias_event']      = pd.Series(np.nan, index=asset_ohlc.index, dtype='object')

    if len(asset_swings) < 2 or benchmark_ohlc is None or len(benchmark_ohlc) == 0:
        return df

    bm = benchmark_ohlc

    # ── Price window helpers (tolerate index mismatches via nearest lookup) ──
    def _win_max(target, ts):
        try:
            i = (target.index.get_loc(ts) if ts in target.index
                 else target.index.get_indexer([ts], method='nearest')[0])
            return target.iloc[max(0, i - lookaround_bars):i + lookaround_bars + 1]['high'].max()
        except Exception:
            return np.nan

    def _win_min(target, ts):
        try:
            i = (target.index.get_loc(ts) if ts in target.index
                 else target.index.get_indexer([ts], method='nearest')[0])
            return target.iloc[max(0, i - lookaround_bars):i + lookaround_bars + 1]['low'].min()
        except Exception:
            return np.nan

    def _bh(ts): return _win_max(bm, ts)
    def _bl(ts): return _win_min(bm, ts)
    def _ah(ts): return _win_max(asset_ohlc, ts)
    def _al(ts): return _win_min(asset_ohlc, ts)

    # ── Safe write helper ────────────────────────────────────────────────────
    # BM-led scenarios (C, D, Symmetrical) use DXY timestamps. If that date
    # is missing from the AUDUSD index, df.loc[dxy_ts] creates a spurious row.
    # This helper maps any timestamp to the nearest existing df row instead.
    def _set(ts, col, val):
        if ts in df.index:
            df.loc[ts, col] = val
        else:
            i = df.index.get_indexer([ts], method='nearest')[0]
            df.iloc[i, df.columns.get_loc(col)] = val

    asset_highs = asset_swings[asset_swings['type'] == 'HIGH']
    asset_lows  = asset_swings[asset_swings['type'] == 'LOW']

    bm_swings = smc.swing_highs_lows_v4(bm)
    bm_highs  = bm_swings[bm_swings['type'] == 'HIGH']
    bm_lows   = bm_swings[bm_swings['type'] == 'LOW']

    # ── Divergence detection ─────────────────────────────────────────────────
    if correlation == "inverse":

        # A — Asset LL + BM fails HH → BULLISH
        for i in range(1, len(asset_lows)):
            t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
            p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
            if p1 < p0:
                h0, h1 = _bh(t0), _bh(t1)
                if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                    _set(t1, 'smt_bullish_div', True)
                    _set(t1, 'smt_swept_low',   float(p1))
                    _set(t1, 'smt_bias_event',  'BULLISH')

        # B — Asset HH + BM fails LL → BEARISH
        for i in range(1, len(asset_highs)):
            t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
            p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
            if p1 > p0:
                l0, l1 = _bl(t0), _bl(t1)
                if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                    _set(t1, 'smt_bearish_div', True)
                    _set(t1, 'smt_swept_high',  float(p1))
                    _set(t1, 'smt_bias_event',  'BEARISH')

        # C — BM LL + Asset fails HH → BEARISH
        for i in range(1, len(bm_lows)):
            t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
            bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
            if bp1 < bp0:
                ah0, ah1 = _ah(t0), _ah(t1)
                if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                    _set(t1, 'smt_bearish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BEARISH')

        # D — BM HH + Asset fails LL → BULLISH
        for i in range(1, len(bm_highs)):
            t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
            bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
            if bp1 > bp0:
                al0, al1 = _al(t0), _al(t1)
                if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                    _set(t1, 'smt_bullish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BULLISH')

        # Symmetrical Bullish — DXY LL + Asset HH → trend up continues
        for i in range(1, len(bm_lows)):
            t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
            bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
            if bp1 < bp0:
                ah0, ah1 = _ah(t0), _ah(t1)
                if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 > ah0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BULLISH')
                    _set(t1, 'smt_bias_event',      'BULLISH')

        # Symmetrical Bearish — DXY HH + Asset LL → trend down continues
        for i in range(1, len(bm_highs)):
            t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
            bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
            if bp1 > bp0:
                al0, al1 = _al(t0), _al(t1)
                if not (pd.isna(al0) or pd.isna(al1)) and al1 < al0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BEARISH')
                    _set(t1, 'smt_bias_event',      'BEARISH')

    elif correlation == "positive":

        # A — Asset HH + BM fails HH → BEARISH
        for i in range(1, len(asset_highs)):
            t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
            p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
            if p1 > p0:
                h0, h1 = _bh(t0), _bh(t1)
                if not (pd.isna(h0) or pd.isna(h1)) and h1 < h0:
                    _set(t1, 'smt_bearish_div', True)
                    _set(t1, 'smt_bias_event',  'BEARISH')

        # B — Asset LL + BM fails LL → BULLISH
        for i in range(1, len(asset_lows)):
            t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
            p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
            if p1 < p0:
                l0, l1 = _bl(t0), _bl(t1)
                if not (pd.isna(l0) or pd.isna(l1)) and l1 > l0:
                    _set(t1, 'smt_bullish_div', True)
                    _set(t1, 'smt_bias_event',  'BULLISH')

        # C — BM HH + Asset fails HH → BEARISH
        for i in range(1, len(bm_highs)):
            t0, t1 = bm_highs.iloc[i-1]['ts'], bm_highs.iloc[i]['ts']
            bp0, bp1 = bm_highs.iloc[i-1]['p'], bm_highs.iloc[i]['p']
            if bp1 > bp0:
                ah0, ah1 = _ah(t0), _ah(t1)
                if not (pd.isna(ah0) or pd.isna(ah1)) and ah1 < ah0:
                    _set(t1, 'smt_bearish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BEARISH')

        # D — BM LL + Asset fails LL → BULLISH
        for i in range(1, len(bm_lows)):
            t0, t1 = bm_lows.iloc[i-1]['ts'], bm_lows.iloc[i]['ts']
            bp0, bp1 = bm_lows.iloc[i-1]['p'], bm_lows.iloc[i]['p']
            if bp1 < bp0:
                al0, al1 = _al(t0), _al(t1)
                if not (pd.isna(al0) or pd.isna(al1)) and al1 > al0:
                    _set(t1, 'smt_bullish_div_bm', True)
                    _set(t1, 'smt_bias_event',     'BULLISH')

        # Symmetrical Bullish — Asset HH + BM HH
        for i in range(1, len(asset_highs)):
            t0, t1 = asset_highs.iloc[i-1]['ts'], asset_highs.iloc[i]['ts']
            p0, p1 = asset_highs.iloc[i-1]['p'],  asset_highs.iloc[i]['p']
            if p1 > p0:
                h0, h1 = _bh(t0), _bh(t1)
                if not (pd.isna(h0) or pd.isna(h1)) and h1 > h0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BULLISH')
                    _set(t1, 'smt_bias_event',      'BULLISH')

        # Symmetrical Bearish — Asset LL + BM LL
        for i in range(1, len(asset_lows)):
            t0, t1 = asset_lows.iloc[i-1]['ts'], asset_lows.iloc[i]['ts']
            p0, p1 = asset_lows.iloc[i-1]['p'],  asset_lows.iloc[i]['p']
            if p1 < p0:
                l0, l1 = _bl(t0), _bl(t1)
                if not (pd.isna(l0) or pd.isna(l1)) and l1 < l0:
                    _set(t1, 'smt_trend_confirmed', True)
                    _set(t1, 'smt_trend_direction', 'BEARISH')
                    _set(t1, 'smt_bias_event',      'BEARISH')

    # Forward-fill bias from event markers (persists until next signal)
    df['smt_bias'] = df['smt_bias_event'].ffill().fillna('NEUTRAL')

    # ── GAP 1: FVG void "closed in" confirmation (ICT p.222) ─────────────────
    # ICT: "Once the void right after that down candle is closed in,
    #       we know there is underlying strength."
    # Sequence: (1) find last opposing-direction candle on benchmark near signal,
    #           (2) detect the FVG gap formed with surrounding candles,
    #           (3) confirm price later trades back into that gap zone.
    def _ob_fvg_closed_in(bm_df, ts, direction):
        center_i = (bm_df.index.get_loc(ts) if ts in bm_df.index
                    else bm_df.index.get_indexer([ts], method='nearest')[0])
        start_i = max(1, center_i - lookaround_bars)
        window  = bm_df.iloc[start_i:center_i + 1]

        if direction == 'BEARISH':
            ob_mask = window['close'] < window['open']   # down candle = OB candidate
        else:
            ob_mask = window['close'] > window['open']   # up candle = OB candidate

        ob_candles = window[ob_mask]
        if ob_candles.empty:
            return False

        ob_loc = bm_df.index.get_loc(ob_candles.index[-1])
        # Defensive: get_loc may return slice/array on non-unique index
        if isinstance(ob_loc, slice):
            ob_loc = ob_loc.start
        elif not isinstance(ob_loc, (int, np.integer)):
            ob_loc = int(np.where(ob_loc)[0][0])

        if ob_loc < 1 or ob_loc + 2 >= len(bm_df):
            return False

        prev_c = bm_df.iloc[ob_loc - 1]
        next_c = bm_df.iloc[ob_loc + 1]

        if direction == 'BEARISH':
            fvg_top, fvg_bot = float(prev_c['low']), float(next_c['high'])
        else:
            fvg_top, fvg_bot = float(next_c['low']), float(prev_c['high'])

        if fvg_bot >= fvg_top:
            return False   # no genuine gap

        future = bm_df.iloc[ob_loc + 2:]
        if future.empty:
            return False
        return bool(((future['high'] >= fvg_bot) & (future['low'] <= fvg_top)).any())

    if fvg_df is not None and not fvg_df.empty and 'FVG' in fvg_df.columns:
        # Backward-compat: caller supplied pre-computed FVG dataframe
        for ts in df[df['smt_bias_event'] == 'BULLISH'].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            end = min(len(df), i + lookaround_bars + 1)
            if (fvg_df.iloc[i:end]['FVG'] == 1).any():
                df.loc[ts, 'smt_confirmed'] = True
        for ts in df[df['smt_bias_event'] == 'BEARISH'].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            end = min(len(df), i + lookaround_bars + 1)
            if (fvg_df.iloc[i:end]['FVG'] == -1).any():
                df.loc[ts, 'smt_confirmed'] = True
    else:
        # ICT-native: OB candle + FVG void + close-in on benchmark (p.222)
        for ts in df[df['smt_bias_event'] == 'BEARISH'].index:
            df.loc[ts, 'smt_confirmed'] = _ob_fvg_closed_in(bm, ts, 'BEARISH')
        for ts in df[df['smt_bias_event'] == 'BULLISH'].index:
            df.loc[ts, 'smt_confirmed'] = _ob_fvg_closed_in(bm, ts, 'BULLISH')

    # ── LIQUIDITY SWEEP CONFIRMATION ─────────────────────────────────────────
    if (liquidity_df is not None
            and not liquidity_df.empty
            and 'Level' in liquidity_df.columns
            and 'Swept' in liquidity_df.columns):
        for ts in df[~df['smt_swept_high'].isna()].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            bull_sw = liquidity_df[liquidity_df['Liquidity'] == 1]['Swept']
            bull_sw = bull_sw[(bull_sw > 0) & (~pd.isna(bull_sw))]
            if any((bull_sw >= max(0, i - lookaround_bars)) & (bull_sw <= i + lookaround_bars)):
                df.loc[ts, 'smt_at_liquidity'] = True
        for ts in df[~df['smt_swept_low'].isna()].index:
            i = df.index.get_indexer([ts], method='nearest')[0]
            bear_sw = liquidity_df[liquidity_df['Liquidity'] == -1]['Swept']
            bear_sw = bear_sw[(bear_sw > 0) & (~pd.isna(bear_sw))]
            if any((bear_sw >= max(0, i - lookaround_bars)) & (bear_sw <= i + lookaround_bars)):
                df.loc[ts, 'smt_at_liquidity'] = True
    else:
        df['smt_at_liquidity'] = True

    # smt_bias_event is kept in the return — verify_month3_video5.py reads it
    return df


def _smt_apply_bias_filter(signal_df, smt_df, signal_type):
    """
    ICT Month 3, Video 5, p.226 — Execution Layer Bias Wiring.

    Gates a signal DataFrame through the SMT macro bias so that only
    signals aligned with institutional directional intent are returned.

    Usage:
        ob_df = smc.ob(ohlc)
        short_obs = smc.smt_apply_bias_filter(ob_df[ob_df['OB']==-1], smt_df, 'BEARISH')

    Parameters
    ----------
    signal_df   : DataFrame of signals to filter (e.g. bearish Order Blocks)
    smt_df      : output of smt_divergence() — must contain 'smt_bias' column
    signal_type : 'BULLISH' or 'BEARISH'

    Returns
    -------
    Filtered signal_df containing only bias-aligned rows.
    """
    if smt_df is None or 'smt_bias' not in smt_df.columns or signal_df.empty:
        return signal_df

    combined_idx = signal_df.index.union(smt_df.index)
    bias_series = (
        smt_df['smt_bias']
        .reindex(combined_idx)
        .ffill()
        .reindex(signal_df.index)
        .fillna('NEUTRAL')
    )
    return signal_df[bias_series == signal_type]


# ── Attach to smc class ──────────────────────────────────────────────────────
# Runs AFTER @apply(inputvalidator) has already wrapped the class.
# _smt_divergence and _smt_apply_bias_filter are never subject to the decorator.
# Do NOT move these lines above the class definition.
smc.smt_divergence = _smt_divergence
smc.smt_apply_bias_filter = _smt_apply_bias_filter


# ================================================================
# MARKET PROTRACTION — module-level function (bypass @apply decorator)
# ICT Video 8 — Market Protraction (Temporal Manipulation)
#
# Three institutional clock anchors per trading day:
#   ASIA     : 20:00 NY (previous evening — London open preparation)
#   MIDNIGHT : 00:00 NY (new trading day — overnight session)
#   NY_OPEN  : 07:00 NY (New York open — primary institutional window)
#
# Each anchor opens a 2-hour lookahead window. The largest swing
# within that window is classified and tagged on the anchor bar.
# ================================================================


def _market_protraction(ohlc, threshold_pips=0.0005):
    """
    ICT Video 8: Market Protraction (Temporal Manipulation) Swing Detector.

    Scans any FX pair 15-minute bars for temporal manipulation swings
    anchored to three daily institutional clock times in New York time.

    Parameters
    ----------
    ohlc            : OHLC DataFrame with a naive (UTC) or tz-aware DatetimeIndex
    threshold_pips  : minimum swing magnitude to qualify (default 0.0005 = 5 pips)

    Returns
    -------
    DataFrame — same shape/index as ohlc, three columns added:
        protraction_anchor : 'ASIA' | 'MIDNIGHT' | 'NY_OPEN' | None
        protraction_dir    : 1 (bullish sweep) | -1 (bearish sweep) | 0 (none)
        protraction_mag    : swing magnitude in raw price units (0.0 if none)
    """
    import pytz

    result = ohlc.copy()
    result.columns = [c.lower() for c in result.columns]
    result['protraction_anchor'] = None
    result['protraction_dir']    = 0
    result['protraction_mag']    = 0.0

    ny_tz = pytz.timezone('America/New_York')

    # ── Normalise index to NY-aware ──────────────────────────────────────────
    idx = result.index
    if idx.tzinfo is None:
        idx_ny = idx.tz_localize('UTC').tz_convert(ny_tz)
    else:
        idx_ny = idx.tz_convert(ny_tz)

    result.index = idx_ny

    # ── Scan every trading date ──────────────────────────────────────────────
    trading_dates = sorted(set(idx_ny.normalize().date))

    for d in trading_dates:
        d_prev = d - pd.Timedelta(days=1)

        # Three anchor timestamps (NY local, DST-aware)
        def _ts(date_str, time_str):
            try:
                return pd.Timestamp(f"{date_str} {time_str}").tz_localize(
                    ny_tz, nonexistent='shift_forward', ambiguous='NaT'
                )
            except Exception:
                return pd.NaT

        anchors = [
            ('ASIA',     _ts(str(d_prev), '20:00:00')),
            ('MIDNIGHT', _ts(str(d),      '00:00:00')),
            ('NY_OPEN',  _ts(str(d),      '07:00:00')),
        ]

        for anchor_name, anchor_ts in anchors:
            if pd.isna(anchor_ts):
                continue

            window_end = anchor_ts + pd.Timedelta(hours=2)
            mask       = (result.index >= anchor_ts) & (result.index < window_end)
            window     = result[mask]

            if len(window) < 2:
                continue

            # Swing magnitude
            w_high    = window['high'].max()
            w_low     = window['low'].min()
            magnitude = float(w_high - w_low)

            if magnitude < threshold_pips:
                continue

            # ICT direction: whichever extreme is FARTHER from the window open
            # is the manipulation sweep direction.
            # Larger up-move from open  → BULLISH protraction (swept highs)
            # Larger down-move from open → BEARISH protraction (swept lows)
            open_price = float(window['open'].iloc[0])
            up_move    = float(w_high) - open_price
            down_move  = open_price - float(w_low)

            if up_move >= down_move:
                direction  = 1          # bullish: swept up
                anchor_bar = window['high'].idxmax()
                sweep_extreme = float(w_high)
            else:
                direction  = -1         # bearish: swept down
                anchor_bar = window['low'].idxmin()
                sweep_extreme = float(w_low)

            # ── 80% RETRACEMENT GATE (ICT mathematical criterion) ────────────
            # After the 2-hour window, price must retrace ≥ 80% of the sweep
            # magnitude back through the anchor price within 4 hours.
            # This filters out weak noise and qualifies only true protractions.
            retracement_end = window_end + pd.Timedelta(hours=4)
            post_mask = (result.index >= window_end) & (result.index < retracement_end)
            post_window = result[post_mask]

            if post_window.empty:
                continue

            required_retrace = 0.80 * magnitude

            if direction == 1:
                # Bullish sweep: need price to come back DOWN by 80% of up_move
                # i.e., post_low ≤ sweep_extreme - required_retrace
                post_low = float(post_window['low'].min())
                if post_low > (sweep_extreme - required_retrace):
                    continue   # insufficient retracement — sucker play, skip
            else:
                # Bearish sweep: need price to come back UP by 80% of down_move
                # i.e., post_high ≥ sweep_extreme + required_retrace
                post_high = float(post_window['high'].max())
                if post_high < (sweep_extreme + required_retrace):
                    continue   # insufficient retracement — sucker play, skip
            result.loc[anchor_bar, 'protraction_anchor'] = anchor_name
            result.loc[anchor_bar, 'protraction_dir']    = direction
            result.loc[anchor_bar, 'protraction_mag']    = magnitude


    # ── Restore original naive UTC index ────────────────────────────────────
    result.index = result.index.tz_convert('UTC').tz_localize(None)

    return result


smc.market_protraction = _market_protraction


def _filter_quarterly_swings(swings_df, min_days=60):
    """
    Enforce the ICT Quarterly Shift Constraint.
    Filter swing_highs_lows_v4 output to only keep pivots that are at least
    `min_days` calendar days apart. This simulates a 3-4 month macro lookback.
    """
    if swings_df.empty:
        return swings_df
    
    filtered = [swings_df.iloc[0]]
    for i in range(1, len(swings_df)):
        days_apart = (swings_df.iloc[i]['ts'] - filtered[-1]['ts']).days
        if days_apart >= min_days:
            filtered.append(swings_df.iloc[i])
    
    import pandas as pd
    return pd.DataFrame(filtered).reset_index(drop=True)


def _macro_bond_bias(zn_df, zb_df, dxy_df=None):
    """
    ICT Video 6: Macro Economic To Micro Technical (Bond SMT)
    Calculates Macro Regime (3-4 Month Shift) and Micro Execution Triggers.

    Layer 1: Macro Regime via ZB vs DXY inverse SMT (60-day quarterly filter).
             Forward-filled but expires after 130 trading days (~6 months per ICT).
    Layer 2: Micro Execution Triggers via ZN vs ZB positive SMT (unfiltered).
             Bearish bond divergence (ZN HH, ZB fails HH) = interest rates rising = USD Bullish.
    Layer 3: Alignment gate — trigger's USD directional effect must match active regime.
             Triple-instrument simultaneous pivot = manipulation spike, discarded.

    Returns a DataFrame with columns:
        'regime': +1 Bullish USD, -1 Bearish USD, 0 Neutral (capped at 130 days)
        'signal': +1 Long USD execution, -1 Short USD execution
    """
    import pandas as pd

    df_out = pd.DataFrame(index=zn_df.index)
    df_out['regime'] = 0
    df_out['signal'] = 0

    if dxy_df is None:
        return df_out

    # =========================================================================
    # LAYER 1: MACRO REGIME (Quarterly Shift)
    # ZB vs DXY Inverse Correlation with 60-day quarterly filter
    # =========================================================================
    zb_swings_raw = smc.swing_highs_lows_v4(zb_df)
    zb_swings_macro = _filter_quarterly_swings(zb_swings_raw, min_days=60)

    smt_macro = smc.smt_divergence(zb_df, dxy_df, zb_swings_macro, correlation="inverse")

    regime_series = pd.Series(0, index=zn_df.index)
    if 'smt_bullish_div' in smt_macro.columns:
        # ZB HH while DXY fails LL → bonds rising but dollar not falling → Bullish USD
        regime_series[smt_macro['smt_bearish_div'] == True] = 1
        # ZB LL while DXY fails HH → bonds falling but dollar not rising → Bearish USD
        regime_series[smt_macro['smt_bullish_div'] == True] = -1

    # FIX GAP 4: Forward-fill regime but expire after 130 trading days (~6 months per ICT)
    MAX_REGIME_DAYS = 130
    filled = []
    current_val = 0
    days_held = 0
    for val in regime_series:
        if val != 0:
            current_val = val
            days_held = 0
        elif days_held >= MAX_REGIME_DAYS:
            current_val = 0
        days_held += 1
        filled.append(current_val)
    df_out['regime'] = filled

    # =========================================================================
    # LAYER 2: MICRO EXECUTION TRIGGERS (Short-Term Timing)
    # ZN vs ZB Positive Correlation — Unfiltered native swings
    # =========================================================================
    zn_swings = smc.swing_highs_lows_v4(zn_df)
    smt_micro = smc.smt_divergence(zn_df, zb_df, zn_swings, correlation="positive")

    # FIX GAP 2: Map each trigger type to its USD directional effect.
    # ICT (p233): ZN HH + ZB lower high = both bonds declining = interest rates rising = USD Bullish.
    # In positive-correlation smt_divergence:
    #   smt_bearish_div = Asset(ZN) HH, Benchmark(ZB) fails HH → bond weakness → USD effect = +1
    #   smt_bullish_div = Asset(ZN) LL, Benchmark(ZB) fails LL → bond strength → USD effect = -1
    trigger_usd_effect = pd.Series(0, index=zn_df.index)
    if 'smt_bearish_div' in smt_micro.columns:
        trigger_usd_effect[smt_micro['smt_bearish_div'] == True] = 1
        trigger_usd_effect[smt_micro['smt_bearish_div_bm'] == True] = 1
        trigger_usd_effect[smt_micro['smt_bullish_div'] == True] = -1
        trigger_usd_effect[smt_micro['smt_bullish_div_bm'] == True] = -1

    # =========================================================================
    # LAYER 3: ALIGNMENT & MANIPULATION FILTER
    # =========================================================================
    dxy_swings_raw = smc.swing_highs_lows_v4(dxy_df)
    zn_dates = set(zn_swings['ts'])
    zb_dates = set(zb_swings_raw['ts'])
    dxy_dates = set(dxy_swings_raw['ts'])
    manipulation_dates = zn_dates.intersection(zb_dates).intersection(dxy_dates)

    for dt, effect in trigger_usd_effect[trigger_usd_effect != 0].items():
        # Discard false break manipulation (all 3 instruments pivoting same day = news spike)
        if dt in manipulation_dates:
            continue
        # Fire when the trigger's USD directional effect agrees with the Macro Regime
        active_regime = df_out.at[dt, 'regime']
        if active_regime != 0 and active_regime == effect:
            df_out.at[dt, 'signal'] = effect

    return df_out

smc.macro_bond_bias = _macro_bond_bias


def _macro_pair_bias(macro_bias_series, pair_name):
    """
    GAP 1: Currency Pair Classification Engine
    Translates the USD Macro Bias into an actionable LONG/SHORT bias for a specific pair.
    
    Pairs starting with USD (USDCAD, USDCHF, USDJPY) are directly correlated.
    Pairs ending with USD (EURUSD, GBPUSD, AUDUSD, NZDUSD) are inversely correlated.
    
    Returns a Series of +1 (LONG), -1 (SHORT), or 0 (NEUTRAL).
    """
    import pandas as pd
    
    pair_upper = pair_name.upper()
    is_usd_first = pair_upper.startswith('USD')
    
    pair_bias = pd.Series(0, index=macro_bias_series.index)
    
    if is_usd_first:
        pair_bias = macro_bias_series.copy()
    else:
        # Inverse correlation
        pair_bias = macro_bias_series * -1
        
    return pair_bias

smc.macro_pair_bias = _macro_pair_bias


def _macro_ob_alignment(zb_df, dxy_df, swing_length=3):
    """
    ICT Video 6 (p230): Detects the 'Prime Setup' confluence:
    - DXY price has TAPPED INTO a Daily Bullish Order Block (price <= OB Top)
    - ZB price has TAPPED INTO a Daily Bearish Order Block (price >= OB Bottom)
    Both conditions must be True simultaneously.

    FIX GAP 1: swing_length=3 required for daily data (default was too large).
    FIX GAP 3: Check price-in-zone tap, not just OB existence.
    """
    import pandas as pd
    import numpy as np

    # FIX GAP 1: Use swing_length=3 — produces meaningful OBs on daily chart
    zb_swings_ob  = smc.swing_highs_lows(zb_df,  swing_length=swing_length)
    dxy_swings_ob = smc.swing_highs_lows(dxy_df, swing_length=swing_length)
    zb_ob  = smc.ob(zb_df,  zb_swings_ob)
    dxy_ob = smc.ob(dxy_df, dxy_swings_ob)

    alignment = pd.Series(False, index=dxy_df.index)

    if 'OB' not in zb_ob.columns or 'OB' not in dxy_ob.columns:
        return alignment
    if 'Top' not in dxy_ob.columns or 'Bottom' not in zb_ob.columns:
        return alignment

    for i, dt in enumerate(dxy_df.index):
        dxy_close = dxy_df['close'].iloc[i]
        zb_close  = zb_df['close'].iloc[i] if dt in zb_df.index else np.nan
        if pd.isna(zb_close):
            continue

        # Find most recent active DXY Bullish OB (OB == 1)
        dxy_ob_slice = dxy_ob.iloc[:i+1]
        active_dxy_bull = dxy_ob_slice[dxy_ob_slice['OB'] == 1]
        if active_dxy_bull.empty:
            continue
        last_dxy_ob = active_dxy_bull.iloc[-1]
        dxy_ob_top    = last_dxy_ob['Top']
        dxy_ob_bottom = last_dxy_ob['Bottom']

        # FIX GAP 3: DXY price must have RETRACED INTO the Bullish OB zone
        dxy_tapping_ob = (dxy_ob_bottom <= dxy_close <= dxy_ob_top)
        if not dxy_tapping_ob:
            continue

        # Find most recent active ZB Bearish OB (OB == -1)
        zb_idx = zb_df.index.get_indexer([dt], method='nearest')[0]
        zb_ob_slice = zb_ob.iloc[:zb_idx+1]
        active_zb_bear = zb_ob_slice[zb_ob_slice['OB'] == -1]
        if active_zb_bear.empty:
            continue
        last_zb_ob = active_zb_bear.iloc[-1]
        zb_ob_top    = last_zb_ob['Top']
        zb_ob_bottom = last_zb_ob['Bottom']

        # FIX GAP 3: ZB price must have RALLIED INTO the Bearish OB zone
        zb_tapping_ob = (zb_ob_bottom <= zb_close <= zb_ob_top)
        if not zb_tapping_ob:
            continue

        alignment.iloc[i] = True

    return alignment

smc.macro_ob_alignment = _macro_ob_alignment



def _trendline_phantoms(ohlc, swings):
    """
    Detects False Trendline (Phantom) Traps from Month 3 Video 7.

    Returns a DataFrame with columns:
    - trap_interim  : price of the high/low between touches 2 and 3
    - trap_point2   : price of the 2nd touch (retail stop cluster)
    - trap_touch3   : price of the 3rd touch (for limit-order entry, Gap 7)
    - trap_p1_ts    : timestamp of Point 1 (for FVG target lookup)
    - trap_fvg_top  : top of the FVG left by Point 1 impulse (Gap 8)
    - trap_fvg_bot  : bottom of the FVG left by Point 1 impulse (Gap 8)
    - trap_ts       : timestamp when trap became active (after 3rd touch)
    - trap_type     : 1 for Bullish Trap, -1 for Bearish Trap
    """
    import pandas as pd
    import numpy as np

    result = pd.DataFrame(index=ohlc.index)
    result['trap_interim'] = np.nan
    result['trap_point2']  = np.nan
    result['trap_touch3']  = np.nan
    result['trap_p1_ts']   = pd.NaT
    result['trap_fvg_top'] = np.nan
    result['trap_fvg_bot'] = np.nan
    result['trap_ts']      = pd.NaT
    result['trap_type']    = 0

    highs = swings[swings['type'] == 'HIGH'].copy()
    lows  = swings[swings['type'] == 'LOW'].copy()

    def _find_p1_fvg(p1_ts, direction):
        """Return (fvg_top, fvg_bot) of the FVG at Point 1 impulse, or (nan, nan)."""
        try:
            idx = ohlc.index.get_loc(p1_ts)
        except KeyError:
            return np.nan, np.nan
        if idx + 1 >= len(ohlc):
            return np.nan, np.nan
        c0 = ohlc.iloc[idx]
        c1 = ohlc.iloc[idx + 1]
        if direction == 'bearish':
            if c1['high'] < c0['low']:
                return float(c0['low']), float(c1['high'])
        else:
            if c1['low'] > c0['high']:
                return float(c1['low']), float(c0['high'])
        return np.nan, np.nan

    # Bullish Traps: 3 consecutive Lower Highs
    if len(highs) >= 3:
        for i in range(len(highs) - 2):
            h1 = highs.iloc[i]
            h2 = highs.iloc[i+1]
            h3 = highs.iloc[i+2]
            if h1['p'] > h2['p'] > h3['p']:
                t1 = h1['ts']
                t2 = h2['ts']
                t3 = h3['ts']
                mask   = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    fvg_top, fvg_bot = _find_p1_fvg(t1, 'bearish')
                    result.loc[t3, 'trap_interim'] = float(window['low'].min())
                    result.loc[t3, 'trap_point2']  = float(h2['p'])
                    result.loc[t3, 'trap_touch3']  = float(h3['p'])
                    result.loc[t3, 'trap_p1_ts']   = t1
                    result.loc[t3, 'trap_fvg_top'] = fvg_top
                    result.loc[t3, 'trap_fvg_bot'] = fvg_bot
                    result.loc[t3, 'trap_ts']      = t3
                    result.loc[t3, 'trap_type']    = 1

    # Bearish Traps: 3 consecutive Higher Lows
    if len(lows) >= 3:
        for i in range(len(lows) - 2):
            l1 = lows.iloc[i]
            l2 = lows.iloc[i+1]
            l3 = lows.iloc[i+2]
            if l1['p'] < l2['p'] < l3['p']:
                t1 = l1['ts']
                t2 = l2['ts']
                t3 = l3['ts']
                mask   = (ohlc.index >= t2) & (ohlc.index <= t3)
                window = ohlc[mask]
                if not window.empty:
                    fvg_top, fvg_bot = _find_p1_fvg(t1, 'bullish')
                    result.loc[t3, 'trap_interim'] = float(window['high'].max())
                    result.loc[t3, 'trap_point2']  = float(l2['p'])
                    result.loc[t3, 'trap_touch3']  = float(l3['p'])
                    result.loc[t3, 'trap_p1_ts']   = t1
                    result.loc[t3, 'trap_fvg_top'] = fvg_top
                    result.loc[t3, 'trap_fvg_bot'] = fvg_bot
                    result.loc[t3, 'trap_ts']      = t3
                    result.loc[t3, 'trap_type']    = -1

    for col in ['trap_interim','trap_point2','trap_touch3','trap_fvg_top','trap_fvg_bot']:
        result[col] = result[col].ffill()
    result['trap_ts']    = result['trap_ts'].ffill()
    result['trap_p1_ts'] = result['trap_p1_ts'].ffill()
    result['trap_type']  = result['trap_type'].replace(0, np.nan).ffill().fillna(0)

    return result

smc.trendline_phantoms = _trendline_phantoms


def _phantom_signals(ohlc, phantoms, ob_df, htf_bias=None):
    """
    Full 3-Phase Market Maker Trap Execution Engine (Month 3, Video 7).

    Phase 2 Entry Triggers at the Interim Extreme:
      A. Turtle Soup       -- price sweeps below/above the interim level
      B. Limit at 3rd Touch -- price touches the 3rd-touch trendline level (Gap 7)
      C. OB Tap            -- price taps an Order Block at the interim level
      D. Breaker           -- price breaks a prior swing in the trap direction (Gap 6)

    Phase 2 Target        : trap_point2 (retail stop cluster)
    Secondary Target      : trap_fvg_top / trap_fvg_bot (FVG from Point 1, Gap 8)

    Phase 3 Reversal (after Point 2 is swept):
      Signal  : opposite direction
      Target  : trap_interim (deep liquidity pool)

    signal column  : 1=Buy, -1=Sell
    trigger_type   : identifies which phase and entry type fired
    target_price   : primary Take Profit
    secondary_target: FVG-based secondary Take Profit (Gap 8)
    """
    import pandas as pd
    import numpy as np

    signals = pd.DataFrame(index=ohlc.index)
    signals['signal']           = 0
    signals['trigger_type']     = ""
    signals['target_price']     = np.nan
    signals['secondary_target'] = np.nan

    if htf_bias is None:
        htf_bias = pd.Series(1, index=ohlc.index)

    consumed_traps = set()
    phase2_fired   = set()

    # Pre-compute Breaker flags (Gap 6)
    # Bearish Breaker: close breaks above prior bar high (retail trapped long -- we sell)
    # Bullish Breaker: close breaks below prior bar low  (retail trapped short -- we buy)
    breaker_up   = ohlc['close'] > ohlc['high'].shift(1)
    breaker_down = ohlc['close'] < ohlc['low'].shift(1)

    for i in range(len(ohlc)):
        ts = ohlc.index[i]

        trap_type = phantoms['trap_type'].iloc[i]
        if trap_type == 0:
            continue

        trap_ts = phantoms['trap_ts'].iloc[i]
        if pd.isna(trap_ts) or trap_ts in consumed_traps:
            continue

        bias = htf_bias.iloc[i]
        if pd.isna(bias) or trap_type != bias:
            continue

        low   = ohlc['low'].iloc[i]
        high  = ohlc['high'].iloc[i]

        trap_interim = phantoms['trap_interim'].iloc[i]
        trap_point2  = phantoms['trap_point2'].iloc[i]
        trap_touch3  = phantoms['trap_touch3'].iloc[i]
        trap_fvg_top = phantoms['trap_fvg_top'].iloc[i]
        trap_fvg_bot = phantoms['trap_fvg_bot'].iloc[i]

        ob_top    = ob_df['Top'].iloc[i]    if 'Top'    in ob_df.columns else np.nan
        ob_bottom = ob_df['Bottom'].iloc[i] if 'Bottom' in ob_df.columns else np.nan
        ob_type   = ob_df['OB'].iloc[i]     if 'OB'     in ob_df.columns else 0

        def _fvg_secondary(direction):
            if direction == 'bull':
                return float(trap_fvg_top) if not pd.isna(trap_fvg_top) else np.nan
            return float(trap_fvg_bot) if not pd.isna(trap_fvg_bot) else np.nan

        # ============================================================== #
        # BULLISH TRAP  (3 Lower Highs -- retail sells, we buy)          #
        # ============================================================== #
        if trap_type == 1:
            swept_point2  = high >= trap_point2
            swept_interim = low  <= trap_interim
            at_touch3     = high >= trap_touch3
            breaker_fired = bool(breaker_up.iloc[i]) and high >= trap_interim

            if trap_ts in phase2_fired and swept_point2:
                # Phase 3: buy-stops at Point 2 purged -- Market Maker SELLS
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 3 SELL -- Point2 High Swept"
                signals.loc[ts, 'target_price']      = trap_interim
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                consumed_traps.add(trap_ts)

            elif swept_interim and trap_ts not in phase2_fired:
                # Phase 2-A: Turtle Soup at Interim Low
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- Turtle Soup"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

            elif at_touch3 and trap_ts not in phase2_fired:
                # Phase 2-B: Limit Order at 3rd Touch (Gap 7)
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- Limit at 3rd Touch"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

            elif breaker_fired and trap_ts not in phase2_fired:
                # Phase 2-D: Bearish Breaker near Interim (Gap 6)
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- Bearish Breaker"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

            elif (ob_type == 1 and not pd.isna(ob_top)
                  and low <= ob_top
                  and not pd.isna(ob_bottom)
                  and ob_bottom <= trap_interim <= ob_top
                  and trap_ts not in phase2_fired):
                # Phase 2-C: OB Tap at Interim Low
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 2 BUY -- OB Tap"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                phase2_fired.add(trap_ts)

        # ============================================================== #
        # BEARISH TRAP  (3 Higher Lows -- retail buys, we sell)          #
        # ============================================================== #
        elif trap_type == -1:
            swept_point2  = low  <= trap_point2
            swept_interim = high >= trap_interim
            at_touch3     = low  <= trap_touch3
            breaker_fired = bool(breaker_down.iloc[i]) and low <= trap_interim

            if trap_ts in phase2_fired and swept_point2:
                # Phase 3: sell-stops at Point 2 purged -- Market Maker BUYS
                signals.loc[ts, 'signal']            = 1
                signals.loc[ts, 'trigger_type']      = "Phase 3 BUY -- Point2 Low Swept"
                signals.loc[ts, 'target_price']      = trap_interim
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bull')
                consumed_traps.add(trap_ts)

            elif swept_interim and trap_ts not in phase2_fired:
                # Phase 2-A: Turtle Soup at Interim High
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- Turtle Soup"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

            elif at_touch3 and trap_ts not in phase2_fired:
                # Phase 2-B: Limit Order at 3rd Touch (Gap 7)
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- Limit at 3rd Touch"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

            elif breaker_fired and trap_ts not in phase2_fired:
                # Phase 2-D: Bullish Breaker near Interim (Gap 6)
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- Bullish Breaker"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

            elif (ob_type == -1 and not pd.isna(ob_bottom)
                  and high >= ob_bottom
                  and not pd.isna(ob_top)
                  and ob_bottom <= trap_interim <= ob_top
                  and trap_ts not in phase2_fired):
                # Phase 2-C: OB Tap at Interim High
                signals.loc[ts, 'signal']            = -1
                signals.loc[ts, 'trigger_type']      = "Phase 2 SELL -- OB Tap"
                signals.loc[ts, 'target_price']      = trap_point2
                signals.loc[ts, 'secondary_target']  = _fvg_secondary('bear')
                phase2_fired.add(trap_ts)

    return signals

smc.phantom_signals = _phantom_signals


def _false_hns_patterns(ohlc, swings, max_neckline_slope_pct=0.005):
    """
    Detects False Head and Shoulders Traps (Month 3 Video 8).
    """
    # Clean swings
    swing_arr = swings[~swings['type'].isna()].copy()
    # Ensure ts column is always proper pd.Timestamp (not numpy datetime64)
    swing_arr['ts'] = pd.to_datetime(swing_arr['ts'])

    # Store detected patterns
    patterns = []

    # Iterate through swings in chunks of 5
    for i in range(len(swing_arr) - 4):
        window = swing_arr.iloc[i:i+5]
        types  = window['type'].values
        prices = window['p'].values
        # Convert numpy datetime64 → pd.Timestamp for safe comparison later
        timestamps = [pd.Timestamp(t) for t in window['ts'].values]
        
        # Bullish Trap: Standard H&S (H, L, H, L, H)
        if (types[0] == 'HIGH' and types[1] == 'LOW' and 
            types[2] == 'HIGH' and types[3] == 'LOW' and 
            types[4] == 'HIGH'):
            
            ls = prices[0]
            l1 = prices[1]
            t1 = timestamps[1]
            
            head = prices[2]
            
            l2 = prices[3]
            t2 = timestamps[3]
            rs = prices[4]
            
            # Constraints
            neckline_diff = abs(l1 - l2) / min(l1, l2)
            
            # Head must be highest
            if head > ls and head > rs and neckline_diff <= max_neckline_slope_pct:
                patterns.append({
                    'trap_type': 1, # Bullish trap
                    'trap_ts': timestamps[4],
                    'p1': l1,
                    't1': t1,
                    'p2': l2,
                    't2': t2,
                    'target_1': rs,
                    'target_2': head
                })
                
        # Bearish Trap: Inverted H&S (L, H, L, H, L)
        elif (types[0] == 'LOW' and types[1] == 'HIGH' and 
              types[2] == 'LOW' and types[3] == 'HIGH' and 
              types[4] == 'LOW'):
              
            ls = prices[0]
            h1 = prices[1]
            t1 = timestamps[1]
            
            head = prices[2]
            
            h2 = prices[3]
            t2 = timestamps[3]
            rs = prices[4]
            
            # Constraints
            neckline_diff = abs(h1 - h2) / min(h1, h2)
            
            # Head must be lowest
            if head < ls and head < rs and neckline_diff <= max_neckline_slope_pct:
                patterns.append({
                    'trap_type': -1, # Bearish trap
                    'trap_ts': timestamps[4],
                    'p1': h1,
                    't1': t1,
                    'p2': h2,
                    't2': t2,
                    'target_1': rs,
                    'target_2': head
                })
                
    return pd.DataFrame(patterns) if patterns else pd.DataFrame(columns=['trap_type', 'trap_ts', 'p1', 't1', 'p2', 't2', 'target_1', 'target_2'])

def _hns_signals(ohlc, patterns, htf_bias=None, htf_poi_top=None, htf_poi_btm=None):
    """
    Executes trades on the diagonal neckline sweep.
    """
    signals = pd.DataFrame(index=ohlc.index)
    signals['signal'] = 0
    signals['trigger_type'] = pd.Series(dtype='object')
    signals['target_1'] = np.nan
    signals['target_2'] = np.nan
    
    if patterns.empty:
        return signals
        
    if htf_bias is None:
        htf_bias = pd.Series(0, index=ohlc.index)
    if htf_poi_top is None:
        htf_poi_top = pd.Series(np.nan, index=ohlc.index)
    if htf_poi_btm is None:
        htf_poi_btm = pd.Series(np.nan, index=ohlc.index)
        
    consumed_traps = set()
    
    for i, (ts, row) in enumerate(ohlc.iterrows()):
        bias = htf_bias.loc[ts] if ts in htf_bias.index else 0
        if bias == 0:
            continue
            
        high = row['high']
        low = row['low']
        
        poi_t = htf_poi_top.loc[ts] if ts in htf_poi_top.index else np.nan
        poi_b = htf_poi_btm.loc[ts] if ts in htf_poi_btm.index else np.nan
        
        # We MUST have a valid POI defined
        if pd.isna(poi_t) or pd.isna(poi_b):
            continue
            
        # We also MUST have a directional bias (not 0)
        if bias == 0.0:
            continue
        
        # Get active patterns up to this point
        active = patterns[patterns['trap_ts'] < ts]
        
        for _, trap in active.iterrows():
            trap_ts = trap['trap_ts']
            if trap_ts in consumed_traps:
                continue
                
            trap_type = trap['trap_type']
            if trap_type != bias:
                continue
                
            t1 = trap['t1']
            t2 = trap['t2']
            p1 = trap['p1']
            p2 = trap['p2']
            target_1 = trap['target_1']
            target_2 = trap['target_2']
            
            if trap_type == 1:
                # Bullish Trap (Standard H&S)
                # ICT entry: Turtle Soup — buy the sweep of the EQUAL LOWS (sell stops below the neckline)
                # The two neckline lows (p1, p2) are the equal lows retail sells break below
                equal_lows_level = min(p1, p2)
                
                # Invalidate if Head (highest high) is violated upward first — trap is gone
                if high >= target_2:
                    consumed_traps.add(trap_ts)
                    continue
                    
                # Trigger: wick sweeps BELOW the equal lows (into the sell stops)
                if low <= equal_lows_level:
                    signals.loc[ts, 'signal'] = 1
                    signals.loc[ts, 'trigger_type'] = "H&S Equal-Lows Sweep BUY (Turtle Soup)"
                    signals.loc[ts, 'target_1'] = target_1   # Right shoulder (first partial)
                    signals.loc[ts, 'target_2'] = target_2   # Head (highest high — buy stops above)
                    signals.loc[ts, 't1'] = t1
                    signals.loc[ts, 'p1'] = p1
                    signals.loc[ts, 't2'] = t2
                    signals.loc[ts, 'p2'] = p2
                    consumed_traps.add(trap_ts)
                    
            elif trap_type == -1:
                # Bearish Trap (Inverted H&S)
                # ICT entry: sell the sweep of the EQUAL HIGHS (buy stops above the neckline)
                # The two neckline highs (p1, p2) are the equal highs retail buys break above
                equal_highs_level = max(p1, p2)
                
                # Invalidate if Head (lowest low) is violated downward first — trap is gone
                if low <= target_2:
                    consumed_traps.add(trap_ts)
                    continue
                    
                # Trigger: wick sweeps ABOVE the equal highs (into the buy stops)
                if high >= equal_highs_level:
                    signals.loc[ts, 'signal'] = -1
                    signals.loc[ts, 'trigger_type'] = "Inv H&S Equal-Highs Sweep SELL (Turtle Soup)"
                    signals.loc[ts, 'target_1'] = target_1   # Right shoulder (first partial)
                    # Gap 4: secondary target = sell stops BELOW the head (lowest low)
                    signals.loc[ts, 'target_2'] = target_2   # Head (lowest low — sell stops below)
                    signals.loc[ts, 't1'] = t1
                    signals.loc[ts, 'p1'] = p1
                    signals.loc[ts, 't2'] = t2
                    signals.loc[ts, 'p2'] = p2
                    consumed_traps.add(trap_ts)
                    
    return signals

smc.false_hns_patterns = _false_hns_patterns
smc.hns_signals = _hns_signals
