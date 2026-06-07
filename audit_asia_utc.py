"""
Forensic UTC Anchor Audit — ASIA signals only.
Answers: What UTC hour does each ASIA protraction signal fire at?
Expected:  20:00 NY EDT = 00:00 UTC  |  20:00 NY EST = 01:00 UTC
"""
import pandas as pd
from smartmoneyconcepts import smc

csv_path = "tests/test_data/EURUSD/EURUSD_15M.csv"
df = pd.read_csv(csv_path)
date_col = "Date" if "Date" in df.columns else "date"
df[date_col] = pd.to_datetime(df[date_col])
df.set_index(date_col, inplace=True)
df = df.iloc[-3000:]

result = smc.market_protraction(df, threshold_pips=0.0005)
signals = result[result["protraction_dir"] != 0].copy()

print("=" * 80)
print("FORENSIC UTC ANCHOR AUDIT — ALL ANCHORS")
print("=" * 80)

# Show all anchors so we can cross-check
print(f"\n{'Timestamp (UTC)':<25} | {'UTC H':<5} | {'Anchor':<10} | {'Direction':<9} | Mag (pips)")
print("-" * 80)
for idx, row in signals.tail(30).iterrows():
    utc_ts = pd.Timestamp(idx)
    utc_hour = utc_ts.hour
    utc_min  = utc_ts.minute
    direction = "BULLISH" if row["protraction_dir"] == 1 else "BEARISH"
    mag_pips = row["protraction_mag"] / 0.0001
    anchor = row["protraction_anchor"]
    print(f"{str(idx)[:25]:<25} | {utc_hour:02d}:{utc_min:02d} | {anchor:<10} | {direction:<9} | {mag_pips:.2f}")

print("\n" + "=" * 80)
print("ASIA SIGNAL BREAKDOWN — UTC HOUR DISTRIBUTION")
print("=" * 80)
asia = signals[signals["protraction_anchor"] == "ASIA"]
print(f"\nTotal ASIA signals: {len(asia)}\n")

utc_hour_counts = {}
for idx, row in asia.iterrows():
    h = pd.Timestamp(idx).hour
    utc_hour_counts[h] = utc_hour_counts.get(h, 0) + 1

for h in sorted(utc_hour_counts):
    # 20:00 NY EDT -> UTC 00:00  |  20:00 NY EST -> UTC 01:00
    note = ""
    if h == 0:
        note = "  <- 20:00 NY EDT (Summer/DST)"
    elif h == 1:
        note = "  <- 20:00 NY EST (Winter/Standard)"
    print(f"  UTC {h:02d}:xx  ->  {utc_hour_counts[h]} signal(s){note}")

print("\n" + "=" * 80)
print("VERDICT")
print("=" * 80)
# Determine the dominant UTC hour
if utc_hour_counts:
    dominant = max(utc_hour_counts, key=utc_hour_counts.get)
    if dominant == 0:
        print(f"ASIA anchor is firing at UTC 00:00  = 20:00 NY EDT. Correct for summer data.")
    elif dominant == 1:
        print(f"ASIA anchor is firing at UTC 01:00  = 20:00 NY EST. Correct for winter data.")
    else:
        print(f"ASIA anchor firing at UTC {dominant:02d}:xx — INVESTIGATE. This does NOT match 20:00 NY.")
else:
    print("No ASIA signals found to analyze.")
