import argparse
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
import csv

# Dejiang Yin / 20250501
# ---- Parse command-line arguments ----
parser = argparse.ArgumentParser(
    description="Calculate and Plot FAST altitude tracks for celestial sources on a given date for given source(s).",
    formatter_class=argparse.RawTextHelpFormatter,
    epilog="""Example:
  python FAST_tracking.py -Date 2025-04-30 -RaDec "13:12:55.25 +18:10:06.4,13:42:11.62 +28:22:38.2" -Name M53,M3 -Zenith 40 -Show yes -Save yes"""
)
parser.add_argument('-Date', type=str, required=True, help="Observation date (YYYY-MM-DD)")
parser.add_argument('-RaDec', type=str, required=True, help="Comma-separated RA and Dec pairs (e.g. 'RA1 Dec1,RA2 Dec2')")
parser.add_argument('-Name', type=str, required=True, help="Comma-separated source names")
parser.add_argument('-Zenith', type=float, default=40.0, help="Maximum zenith angle in degrees (default: 40°)")
parser.add_argument('-Show', type=str, choices=['yes', 'no'], default='no', help="Whether to display the plot (default: yes)")
parser.add_argument('-Save', type=str, choices=['yes', 'no'], default='yes', help="Whether to save the results to a CSV file (default: yes)")

args = parser.parse_args()

# ---- FAST location ----
fast_location = EarthLocation(lat=25.652953 * u.deg, lon=106.856667 * u.deg, height=1110.03 * u.m)

# ---- Parse source names and coordinates ----
name_list = args.Name.split(',')
radec_pairs = args.RaDec.split(',')

if len(name_list) != len(radec_pairs):
    raise ValueError("The number of names must match the number of RA/Dec pairs.")

source_names = []
source_coords = []
for name, pair in zip(name_list, radec_pairs):
    parts = pair.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Invalid RA/Dec format: '{pair}' (should be 'RA Dec')")
    ra_str, dec_str = parts
    coord = SkyCoord(ra_str + ' ' + dec_str, frame='icrs', unit=(u.hourangle, u.deg))
    source_names.append(name)
    source_coords.append(coord)

# ---- Time grid ----
obs_date = args.Date
midnight = Time(obs_date + ' 12:00:00')
delta_hours = np.linspace(-12, 24, 20000)
times = midnight + delta_hours * u.hour
altaz_frame = AltAz(obstime=times, location=fast_location)

# ---- Minimum altitude ----
min_alt = 90.0 - args.Zenith

# ---- Prepare for plot if needed ----
fig, ax = plt.subplots(figsize=(14, 7)) if args.Show == 'yes' or args.Save == 'yes' else (None, None)
colors = plt.cm.tab20.colors
linestyles = ['-', '--', '-.', ':', (0, (3, 5, 1, 5)), (0, (5, 10)), (0, (1, 1)), (0, (5, 1))]

# ---- CSV file setup ----
csv_file = None
if args.Save == 'yes':
    csv_file = open(f"FAST_Tracking_{obs_date}.csv", mode='w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Source Name", "RA/Dec", "UTC Start", "UTC End", "Beijing Start", "Beijing End", "Duration (hr)"])

# ---- Loop through each source and compute its altitude track ----
for i, (name, coord) in enumerate(zip(source_names, source_coords)):
    altazs = coord.transform_to(altaz_frame)
    altitudes = altazs.alt
    observable = altitudes >= min_alt * u.deg
    observable_indices = np.where(observable)[0]

    if len(observable_indices) > 0:
        splits = np.where(np.diff(observable_indices) > 1)[0] + 1
        blocks = np.split(observable_indices, splits)

        complete_blocks = []
        for block in blocks:
            if (block[0] > 0 and block[-1] < len(times) - 1 and
                altitudes[block[0]-1] < min_alt * u.deg and altitudes[block[-1]+1] < min_alt * u.deg):
                complete_blocks.append(block)

        if complete_blocks:
            best_block = complete_blocks[0]
            t1_utc = times[best_block[0]].datetime
            t2_utc = times[best_block[-1]].datetime
            t1_bj = t1_utc + timedelta(hours=8)
            t2_bj = t2_utc + timedelta(hours=8)
            duration = (t2_utc - t1_utc).total_seconds() / 3600.0
            print(f"{name:10s}:")
            print(f"  UTC        : {t1_utc.strftime('%Y-%m-%d %H:%M')} – {t2_utc.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Beijing    : {t1_bj.strftime('%Y-%m-%d %H:%M')} – {t2_bj.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Duration   : {duration:.3f} hr\n")

            if csv_file:
                csv_writer.writerow([name, f"{coord.ra.to_string(unit=u.hourangle)} {coord.dec.to_string(unit=u.deg)}",
                                     t1_utc.strftime('%Y-%m-%d %H:%M'), t2_utc.strftime('%Y-%m-%d %H:%M'),
                                     t1_bj.strftime('%Y-%m-%d %H:%M'), t2_bj.strftime('%Y-%m-%d %H:%M'), f"{duration:.3f}"])
        else:
            print(f"{name:10s}: No complete observable block\n")
            duration = 0.0
    else:
        print(f"{name:10s}: Not observable")
        duration = 0.0

    if fig is not None:
        color = colors[i % len(colors)]
        linestyle = linestyles[i % len(linestyles)]
        ax.plot(times.datetime, altitudes, label=f"{name} ({duration:.3f} h)", color=color, linestyle=linestyle, linewidth=2)

# ---- Finalize plot and save it ----
if fig is not None:
    ax.axhline(min_alt, color='gray', linestyle='--', label=f'Min Alt ({90 - min_alt:.0f}° zenith)', linewidth=1.5)
    ax.set_title(f"FAST Altitude Tracks on {obs_date}", fontsize=20)
    ax.set_xlabel("Time (UTC)", fontsize=20)
    ax.set_ylabel("Altitude (degrees)", fontsize=20)
    ax.tick_params(axis='both', labelsize=18)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(ncol=2, fontsize=10)
    plt.tight_layout()

    if args.Save == 'yes':
        plot_filename0 = f"FAST_Altitude_Plot_{obs_date}.png"
        plot_filename1 = f"FAST_Altitude_Plot_{obs_date}.pdf"
        plt.savefig(plot_filename0, dpi=300)
        plt.savefig(plot_filename1, dpi=300)

    if args.Show == 'yes':
        plt.show()
    else:
        plt.close()

# ---- Close the CSV file if it was opened ----
if csv_file:
    csv_file.close()
