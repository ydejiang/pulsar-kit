from __future__ import absolute_import
from builtins import map
import re, sys
import glob
import presto.sifting as sifting
from operator import itemgetter, attrgetter
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import os
import shutil
import argparse
from multiprocessing import Pool

# Adapted from ACCEL_sift.py of PRESTO, @ Yin Dejiang, 20250811

# Note:  You will almost certainly want to adjust
#        the following variables for your particular search

# Create an argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description='Pulsar Candidate Sifting routine ACCEL_sift.py of PRESTO.\n# Note:  You will almost certainly want to adjust the following variables for your particular search')
parser.add_argument('-ACCEL', type=int, default=20, help='The suffix of accelsearch results files (also the zmax value) from PRESTO.\nDefault=20')
parser.add_argument('-JERK', type=int, default=None, help='The suffix for JERK files (the wmax value) .\nDefault=None')
parser.add_argument('-minP', type=float, default=0.5, help='Shortest period candidates to consider (ms).\nDefault=0.5')
parser.add_argument('-maxP', type=float, default=15000.0, help='Longest period candidates to consider (ms).\nDefault=15000')
parser.add_argument('-numDM', type=int, default=2, help='In how many DMs must a candidate be detected to be considered "good".\nDefault=2.0')
parser.add_argument('-minS', type=float, default=4.0, help='Ignore candidates with a sigma (from incoherent power summation) less than this.\nDefault=4.0')
parser.add_argument('-minDM', type=float, default=2.0, help='Lowest DM to consider as a "real" pulsar.\nDefault=2.0')
parser.add_argument('-c_pow_threshold', type=float, default=100.0, help='Ignore candidates with a coherent power less than this.\nDefault=100.0')
parser.add_argument('-harm_pow_cutoff', type=float, default=8.0, help='Ignore any candidates where at least one harmonic does exceed this power.\nDefault=8.0')
parser.add_argument('-r_err', type=float, default=1.1, help='Consider it the same candidate (in Fourier bins).\nDefault=1.1')
parser.add_argument('-nproc', type=int, default=5, help='Number of processes for parallel DM–Sigma plotting. \nDefault=5')


args = parser.parse_args()

if args.JERK is not None:
    globaccel = f"*_ACCEL_{args.ACCEL}_JERK_{args.JERK}"
else:
    globaccel = f"*_ACCEL_{args.ACCEL}"

# glob for .inf files
globinf = "*DM*.inf"
# In how many DMs must a candidate be detected to be considered "good"
min_num_DMs = args.numDM
# Lowest DM to consider as a "real" pulsar
low_DM_cutoff = args.minDM
# Ignore candidates with a sigma (from incoherent power summation) less than this
sifting.sigma_threshold = args.minS
# Ignore candidates with a coherent power less than this
sifting.c_pow_threshold = args.c_pow_threshold

# If the birds file works well, the following shouldn't
# be needed at all...  If they are, add tuples with the bad
# values and their errors.
#                (ms, err)
sifting.known_birds_p = []
#                (Hz, err)
sifting.known_birds_f = []

# The following are all defined in the sifting module.
# But if we want to override them, uncomment and do it here.
# You shouldn't need to adjust them for most searches, though.

# How close a candidate has to be to another candidate to 
# consider it the same candidate (in Fourier bins)
sifting.r_err = args.r_err
# Shortest period candidates to consider (s)
sifting.short_period = args.minP / 1000
# Longest period candidates to consider (s)
sifting.long_period = args.maxP / 1000
# Ignore any candidates where at least one harmonic does exceed this power
sifting.harm_pow_cutoff = args.harm_pow_cutoff

#--------------------------------------------------------------

# Try to read the .inf files first, as _if_ they are present, all of
# them should be there.  (if no candidates are found by accelsearch
# we get no ACCEL files...
inffiles = glob.glob(globinf)
candfiles = glob.glob(globaccel)
# Check to see if this is from a short search
if len(re.findall("_[0-9][0-9][0-9]M_" , inffiles[0])):
    dmstrs = [x.split("DM")[-1].split("_")[0] for x in candfiles]
else:
    dmstrs = [x.split("DM")[-1].split(".inf")[0] for x in inffiles]

valid_dmstrs = []
for dmstr in dmstrs:
    match = re.search(r'[-+]?\d*\.\d+|[-+]?\d+', dmstr)
    if match:
        valid_dmstrs.append(match.group())

dmstrs = [x for x, _ in sorted(
    [(s, float(s)) for s in valid_dmstrs], key=lambda t: t[1]
)]

# Read in all the candidates
cands = sifting.read_candidates(candfiles)

# Remove candidates that are duplicated in other ACCEL files
if len(cands):
    cands = sifting.remove_duplicate_candidates(cands)

# Remove candidates with DM problems
if len(cands):
    cands = sifting.remove_DM_problems(cands, min_num_DMs, dmstrs, low_DM_cutoff)

# Remove candidates that are harmonically related to each other
# Note:  this includes only a small set of harmonics
if len(cands):
    cands = sifting.remove_harmonics(cands)

def plot_dm_sigma(cand, outdir="./zmax_sifting/DM_sigma_plots"):
    """
    Generate DM-Sigma relation figure for a single PRESTO candidate.
    Parameters
    ----------
    cand : presto.sifting.Candidate
        Candidate object returned by PRESTO sifting.
    outdir : str
        Output directory for DM-Sigma figures.
    """
    # Safety check: candidate must have DM hits
    if not hasattr(cand, "hits") or len(cand.hits) == 0:
        return
    # Build a local DataFrame from PRESTO hits
    # Each hit is a tuple: (DM, SNR, Sigma)
    df = pd.DataFrame(cand.hits, columns=["DM", "SNR", "Sigma"])
    df = df.sort_values(by="DM")
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 3))

    ax0 = ax.scatter(df["DM"], df["Sigma"], c=df["SNR"], cmap="jet")
    ax.scatter(df["DM"], df["Sigma"], marker='o', facecolors='none', edgecolors='#000000', s=50, linewidths=1.2)
    ax.plot(df["DM"], df["Sigma"], color="#791E94")
    label_txt = (
        f"DM / sigma: {cand.DMstr} / {cand.sigma:.2f}\n"
        f"period: {cand.p:.8f} (s)\n"
        f"z / w: {cand.z:.2f} / {cand.w:.2f}; cand: {cand.candnum}\n"
        f"harm: {cand.numharm}; numhits: {len(cand.hits)}"
    )
    ax.axvline(cand.DM, color="#791E94", linestyle='--', label=label_txt)
    ax.legend(fontsize=8)
    ax.set_xlabel("Trial DM (cm$^{-3}$ pc)")
    ax.set_ylabel("Sigma")
    ax.set_title("#. " + cand.filename, loc="right", fontsize=8)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    ax.tick_params(direction="in")
    ax.tick_params(axis='y', rotation=90)
    #ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    cbar = fig.colorbar(ax0, ax=ax, pad=0.01, fraction=0.05)
    cbar.set_label("SNR")
    cbar.ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    cbar.ax.tick_params(axis='y', rotation=90)
    outfile = f"{outdir}/{cand.filename}_Cand_{cand.candnum}.png"
    plt.savefig(outfile, bbox_inches="tight", pad_inches=0.0, dpi=120)
    plt.close("all")

# Save to dir
basedir = "./zmax_sifting"
subdirs = ["DM_sigma_plots","prepfold_plots","logs",]
assert os.path.basename(basedir) == "zmax_sifting"
shutil.rmtree(basedir, ignore_errors=True)
for sd in subdirs:
    os.makedirs(os.path.join(basedir, sd))

# Write candidates to STDOUT
if len(cands):
    cands.sort(key=attrgetter('sigma'), reverse=True)
    #sifting.write_candlist(cands)
    sifting.write_candlist(cands, './zmax_sifting/cands.txt')

    # Parallel plotting
    if args.nproc > 1:
        with Pool(processes=args.nproc) as pool:
            pool.map(plot_dm_sigma, cands)
    else:
        for c in cands:
            plot_dm_sigma(c)
    """
    ['DM', 'DMstr', 'T', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', 
    '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__',
    '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'add_as_hit', 'candnum', 'cpow', 'f', 'filename',
    'harm_amps', 'harm_pows', 'harms_to_snr', 'hits', 'ipow_det', 'note', 'numharm', 'p', 'path', 'r', 'sigma', 'snr', 'w', 'z']
    """

    """
    # From ypmen, pulsarX
    # print(dir(cands[0])); print(cands[0].DMstr) 
    # For PulsarX folding
    print("#id   dm acc  F0 F1 F2 S/N", file=sys.stderr)
    for k,cand in enumerate(cands):
        z0 = cand.z - 0.5 * cand.w
        r0 = cand.r - 0.5 * z0 - cand.w / 6.
        f = r0 / cand.T
        fd = z0 / (cand.T * cand.T)
        fdd = cand.w / (cand.T * cand.T * cand.T)
        f0 = f + fd * (cand.T / 2.) + 0.5 * fdd * (cand.T / 2.)**2
        f1 = fd + fdd * (cand.T / 2.) 
        f2 = fdd
        print("%d\t%.3f\t%.15f\t%.15f\t%.15f\t%.15f\t%.2f" % (k+1, cand.DM, 0., f0, f1, f2, cand.snr), file=sys.stderr)
    """

    #"""
    # ---- PRESTO folding commands & combine DM-sigma plot----
    # For .dat file folding
    # print("# PRESTO prepfold commands", file=sys.stderr)
    for k, cand in enumerate(cands):
        candnum = cand.candnum
        accelfile = cand.filename
        outprefix = accelfile
        accelfile = accelfile + ".cand"
        datfile = accelfile.split("_ACCEL")[0] + ".dat"
        #cmd = f"prepfold -topo -nosearch -noxwin -n 64 -npart 128 -accelcand {candnum} -accelfile {accelfile} -o {outprefix} {datfile}"
        cmd = f"""prepfold -topo -nosearch -noxwin -n 64 -npart 128 -accelcand {candnum} -accelfile {accelfile} -o {outprefix} {datfile} && python ${{py_combine_plots}} ./{outprefix}_*_Cand_{candnum}.pfd.png ./zmax_sifting/DM_sigma_plots/{outprefix}_Cand_{candnum}.png -output ./zmax_sifting/prepfold_plots/{outprefix}_ACCEL_Cand_{candnum}.png"""
        print(cmd, file=sys.stderr)
    #"""

    """
    # ---- PRESTO folding commands ----
    # For .dat file folding
    print("# PRESTO prepfold commands", file=sys.stderr)
    for k, cand in enumerate(cands):
        candnum = cand.candnum
        accelfile = cand.filename
        outprefix = accelfile.split("_ACCEL")[0]
        accelfile = accelfile + ".cand"
        datfile = accelfile.split("_ACCEL")[0] + ".dat"
        cmd = f"prepfold -topo -nosearch -noxwin -accelcand {candnum} -accelfile {accelfile} -o {outprefix} {datfile}"
        print(cmd, file=sys.stderr)
    """

    """
    # ---- PRESTO folding commands ----
    # For .fits file folding && pm_pm_split_datfile of PULSAR_MINER / chunks
    # print("# PRESTO prepfold commands", file=sys.stderr)
    for k, cand in enumerate(cands):
        candnum = cand.candnum
        accelfile = cand.filename
        dm = cand.DMstr
        outprefix = accelfile.split("_ACCEL")[0]
        accelfile = accelfile + ".cand"
        # ---- parse chunk info ----
        m = re.search(r"_ck(\d+)of(\d+)_", accelfile)
        if m:
            ck = int(m.group(1))
            Nck = int(m.group(2))
            start = (ck - 1) / Nck
            end   = ck / Nck
            start_end_opt = f"-start {start:.4f} -end {end:.4f}"
        else:
            # fallback: full observation, none
            start_end_opt = ""

        cmd = f"prepfold -topo -nosearch -noxwin {start_end_opt} -dm {dm} -accelcand {candnum} -accelfile {accelfile} -o {outprefix}"
        print(cmd, file=sys.stderr)
    """
