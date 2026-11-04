"""
One-shot patch for _propulsion_blocks() in smartmoneyconcepts/smc.py.
Adds Phase 3 retest detection, two new columns, updates docstring.
"""
import sys

path = 'smartmoneyconcepts/smc.py'
content = open(path, encoding='utf-8').read()

# ---- EDIT 1: Docstring ENGINEERING ASSUMPTIONS -- add item 7 after item 6 ----
old_ea = (
    '       any future sourced definition of local or proximity scope.\n'
    '       \n'
    '    Parameters:'
)
new_ea = (
    '       any future sourced definition of local or proximity scope.\n'
    '    7. Retest Detection (PARTIALLY SOURCED -- BOUNDARY ONLY): Source M4V8 p.346\n'
    '       describes a "later retest" of the propulsion block\'s wick extreme as a valid\n'
    '       continuation-phase entry. The wick extreme (wick_extreme, already computed in\n'
    '       Phase 1) is used as the retest boundary -- this boundary is sourced. Whether\n'
    '       a retest is confirmed by the NEXT bar\'s close returning beyond wick_extreme\n'
    '       (PBRetestRejected) is an ENGINEERING ASSUMPTION: M4V8 p.346 does not specify\n'
    '       close-vs-wick or how many bars constitute a "rejection". The retest scan runs\n'
    '       independently of Phase 2 (MeanThresholdViolated / Invalidated) because the\n'
    '       p.346 retest is a distinct continuation-phase entry signal, not a restatement\n'
    '       of the original setup\'s validity. A block that has been invalidated by Phase 2\n'
    '       may still register a retest -- this reflects source intent and is intentional.\n'
    '\n'
    '    Parameters:'
)
assert old_ea in content, 'EDIT1: EA target not found'
content = content.replace(old_ea, new_ea, 1)

# ---- EDIT 2: Docstring Returns section ----
old_ret = (
    "        DataFrame with columns: ['PB', 'PBTop', 'PBBottom', 'AnchorOB_Index', \n"
    "                                 'MeanThresholdViolated', 'Invalidated']"
)
new_ret = (
    "        DataFrame with columns: ['PB', 'PBTop', 'PBBottom', 'AnchorOB_Index', \n"
    "                                 'MeanThresholdViolated', 'Invalidated',\n"
    "                                 'PBRetestIndex', 'PBRetestRejected']"
)
assert old_ret in content, 'EDIT2: Returns target not found'
content = content.replace(old_ret, new_ret, 1)

# ---- EDIT 3: out = pd.DataFrame(...) columns list ----
old_df = (
    "    out = pd.DataFrame(index=ohlc.index, columns=[\n"
    "        'PB', 'PBTop', 'PBBottom', 'AnchorOB_Index', \n"
    "        'MeanThresholdViolated', 'Invalidated'\n"
    "    ])"
)
new_df = (
    "    out = pd.DataFrame(index=ohlc.index, columns=[\n"
    "        'PB', 'PBTop', 'PBBottom', 'AnchorOB_Index', \n"
    "        'MeanThresholdViolated', 'Invalidated',\n"
    "        'PBRetestIndex', 'PBRetestRejected'\n"
    "    ])"
)
assert old_df in content, 'EDIT3: DataFrame init target not found'
content = content.replace(old_df, new_df, 1)

# ---- EDIT 4: Phase 2 loop body -- add Phase 3 and new column writes ----
old_p2_tail = (
    "        # Map back to DatetimeIndex\n"
    "        ts = ohlc.index[idx]\n"
    "        out.loc[ts, 'PB'] = direction\n"
    "        out.loc[ts, 'PBTop'] = rec['body_top']\n"
    "        out.loc[ts, 'PBBottom'] = rec['body_bottom']\n"
    "        out.loc[ts, 'AnchorOB_Index'] = rec['anchor_ts']\n"
    "        out.loc[ts, 'MeanThresholdViolated'] = mt_violated\n"
    "        out.loc[ts, 'Invalidated'] = invalidated\n"
    "        \n"
    "    return out"
)
new_p2_tail = (
    '        # Phase 3: Retest Detection (M4V8 p.346 "later retest" -- runs independently of Phase 2)\n'
    "        retest_index = np.nan\n"
    "        retest_rejected = np.nan\n"
    "        \n"
    "        for k in range(idx + 1, len(ohlc)):\n"
    "            if direction == 1:\n"
    "                # Bullish: retest when low touches or breaches wick_extreme (wick low)\n"
    "                if ohlc['low'].iloc[k] <= wick_extreme:\n"
    "                    retest_index = ohlc.index[k]\n"
    "                    # Rejection confirmed if next bar's close is back above wick_extreme\n"
    "                    if k + 1 < len(ohlc):\n"
    "                        retest_rejected = ohlc['close'].iloc[k + 1] > wick_extreme\n"
    "                    else:\n"
    "                        retest_rejected = False\n"
    "                    break\n"
    "            else:\n"
    "                # Bearish: retest when high touches or breaches wick_extreme (wick high)\n"
    "                if ohlc['high'].iloc[k] >= wick_extreme:\n"
    "                    retest_index = ohlc.index[k]\n"
    "                    # Rejection confirmed if next bar's close is back below wick_extreme\n"
    "                    if k + 1 < len(ohlc):\n"
    "                        retest_rejected = ohlc['close'].iloc[k + 1] < wick_extreme\n"
    "                    else:\n"
    "                        retest_rejected = False\n"
    "                    break\n"
    "        \n"
    "        # Map back to DatetimeIndex\n"
    "        ts = ohlc.index[idx]\n"
    "        out.loc[ts, 'PB'] = direction\n"
    "        out.loc[ts, 'PBTop'] = rec['body_top']\n"
    "        out.loc[ts, 'PBBottom'] = rec['body_bottom']\n"
    "        out.loc[ts, 'AnchorOB_Index'] = rec['anchor_ts']\n"
    "        out.loc[ts, 'MeanThresholdViolated'] = mt_violated\n"
    "        out.loc[ts, 'Invalidated'] = invalidated\n"
    "        out.loc[ts, 'PBRetestIndex'] = retest_index\n"
    "        out.loc[ts, 'PBRetestRejected'] = retest_rejected\n"
    "        \n"
    "    return out"
)
assert old_p2_tail in content, 'EDIT4: Phase 2 tail target not found'
content = content.replace(old_p2_tail, new_p2_tail, 1)

open(path, 'w', encoding='utf-8').write(content)
print('ALL_DONE')
