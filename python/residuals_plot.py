from __future__ import print_function
import argparse
import os
import numpy as np
import struct
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import ticker
from builtins import range
from builtins import object

# Deajing Yin, 20251105, @ yin dot dj at qq dot com

"""
The following scripts is from residuals.py of PRESTO.
https://github.com/scottransom/presto/tree/master/python/presto
"""
# ========== 1. Residual file reading function ==========

#
#  From the TEMPO Documentation:
#    
#  The file resid2.tmp contains residuals, etc. in inary format.  
#  Each record contains eight real*8 values:
#    --TOA (MJD, referenced to solar system barycenter)
#    --Postfit residual (pulse phase, from 0 to 1)
#    --Postfit residual (seconds)
#    --Orbital phase (where applicable)
#    --Observing frequency (in barycenter frame)
#    --Weight of point in the fit
#    --Timing uncertainty (according to input file)
#    --Prefit residual (seconds)
#

class residuals(object):
    pass

def read_residuals(filename="resid2.tmp"):
    """
    read_residuals(filename="resid2.tmp"):
        Read a TEMPO1 style binary residuals file and return all the elements
            in a residuals 'class'.  The class instance will have an attribute
            called .numTOAs with the number of TOAs and up to 8 arrays with
            the following (as appropriate):
            .bary_TOA     Barycentric TOA (MJD)
            .uncertainty  TOA uncertainty (seconds)
            .bary_freq    Observing frequency (in barycenter frame)
            .prefit_phs   Prefit residual (pulse phase, from 0 to 1)
            .prefit_sec   Prefit residual (seconds)
            .postfit_phs  Postfit residual (pulse phase, from 0 to 1)
            .postfit_sec  Postfit residual (seconds)
            .orbit_phs    Orbital phase (where applicable)
            .weight       Weight of point in the fit
    """
    r = residuals()
    infile = open(filename, "rb")
    swapchar = '<'  # This is little-endian (default)
    data = infile.read(8)
    test_int32 = struct.unpack(swapchar + "i", data[:4])[0]
    test_int64 = struct.unpack(swapchar + "q", data)[0]
    if ((test_int32 > 100 or test_int32 < 0) and
            (test_int64 > 100 or test_int64 < 0)):
        swapchar = '>'  # This is big-endian
    if (test_int32 < 100 and test_int32 > 0):
        marktype = 'i'  # 32-bit int
        reclen = test_int32 + 2 * 4
    else:
        marktype = 'q'  # long long
        reclen = test_int64 + 2 * 8
    rectype = swapchar + marktype + 9 * 'd' + marktype
    infile.seek(0, 2)  # Position at file end
    filelen = infile.tell()
    if (filelen % reclen or
            not (reclen == struct.calcsize(rectype))):
        print("Warning:  possibly reading residuals incorrectly... don't understand record size")
    infile.seek(0, 0)  # Position at file start
    r.numTOAs = filelen // reclen
    r.bary_TOA = np.zeros(r.numTOAs, 'd')
    r.postfit_phs = np.zeros(r.numTOAs, 'd')
    r.postfit_sec = np.zeros(r.numTOAs, 'd')
    r.orbit_phs = np.zeros(r.numTOAs, 'd')
    r.bary_freq = np.zeros(r.numTOAs, 'd')
    r.weight = np.zeros(r.numTOAs, 'd')
    r.uncertainty = np.zeros(r.numTOAs, 'd')
    r.prefit_phs = np.zeros(r.numTOAs, 'd')
    for ii in range(r.numTOAs):
        rec = struct.unpack(rectype, infile.read(reclen))
        (r.bary_TOA[ii],
         r.postfit_phs[ii],
         r.postfit_sec[ii],
         r.orbit_phs[ii],
         r.bary_freq[ii],
         r.weight[ii],
         r.uncertainty[ii],
         r.prefit_phs[ii]) = (rec[1], rec[2], rec[3], rec[4],
                              rec[5], rec[6], rec[7], rec[8])
    infile.close()
    if not np.nonzero(r.orbit_phs): del r.orbit_phs
    if not np.nonzero(r.bary_freq): del r.bary_freq
    if not np.nonzero(r.weight): del r.weight
    r.prefit_sec = r.postfit_sec / r.postfit_phs * r.prefit_phs
    r.uncertainty *= 1.e-6  # Convert uncertainties in usec to sec
    return r

# ========== 2. Plotting function ==========
def plot_residuals(res_list, rows, cols, x_axis, output_prefix):
    """Plot residuals for multiple pulsars"""
    n = len(res_list)
    # Key parameters: Set minimum subplot width (inches) to ensure proportion consistency
    # Key parameters: Set subplot size and margins
    # min_subplot_width = 5        # Minimum width of each subplot (inches)
    min_subplot_width = 6        # Minimum width of each subplot (inches)
    margin_width = 1.8             # Total left-right margin width (fixed, inches)
    margin_height = 0.8            # Total top-bottom margin height (fixed, inches, adjustable)
    # --- Proportion settings ---
    bottom_ratio = 3/4           # Bottom margin takes 2/3 of total vertical margin
    top_ratio = 1/4              # Top margin takes 1/3 of total vertical margin
    left_ratio =3/4
    right_ratio = 1/4
    # Dynamically calculate figure size
    fig_width = (cols * min_subplot_width) + margin_width  # Width = total subplot width + left-right margins
    fig_height = (2 * rows) + margin_height                # Height = total subplot height + top-bottom margins
    # Create figure
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=300)
    gs = gridspec.GridSpec(rows, cols, hspace=0.15, wspace=0.15)

    for i, r in enumerate(res_list):
        ax = fig.add_subplot(gs[i])
        # Set border line width (key code)
        linewidth = 0.5   # Line width value, adjustable as needed (default is usually 0.8)
        for spine in ax.spines.values():  # Iterate over top, bottom, left, right borders
            spine.set_linewidth(linewidth)
        if x_axis.lower() == "mjd":
            x = r.bary_TOA
            xlabel = "MJD (days)"
        elif x_axis.lower() == "orbit":
            x = r.orbit_phs
            xlabel = "Orbital phase"
        else:
            raise ValueError("Invalid -x argument: use 'MJD' or 'orbit'")

        # Left axis: Time residual (μs)
        ax.errorbar(x, r.postfit_sec * 1e6, yerr=r.uncertainty * 1e6,
        #           fmt='b.', ms=8, capsize=3, elinewidth=1, markeredgecolor='k', markeredgewidth=0.1)
                    fmt='b.', ms=5, capsize=.1,  capthick=0.5, elinewidth=0.6, markeredgecolor='k', markeredgewidth=0.05)
        ax.axhline(0, color='black', linestyle='--', linewidth=0.6)
        # Add label in the top left corner of each subplot
        if r.label:
            ax.text(
                0.15, 0.85, r.label,
                transform=ax.transAxes,
                fontsize=11,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7)
            )
        """
        # Set x and y labels
        if i // cols == rows - 1:
            ax.set_xlabel(xlabel, fontsize=16)
        """
        current_col = i % cols
        below_index = i + cols
        is_col_last = below_index >= len(res_list)
        if is_col_last:
            ax.set_xlabel(xlabel, fontsize=16)
            ax.tick_params(axis='x', which='major', labelbottom=True)

        # if i % cols == 0:
        #    ax.set_ylabel("Residuals (μs)", fontsize=12)
        # if i % cols == cols-1:
        #    axr.set_ylabel("Residuals (phase)", fontsize=12)
        # New: Unify x-axis tick format (control tick count and decimal places)
        # 1. Control number of x-axis ticks (maximum 6)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6, integer=False))  # integer=False allows decimal ticks
        # 2. Control x-axis tick decimal places (0 decimal places)
        # ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.1f}'))
        # ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.0f}'))
        # 2. Control x-axis tick decimal places based on axis type
        if x_axis.lower() == "orbit":
            ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.1f}'))
            ax.set_xlim(-0.05, 1.05)
        else:
            ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.0f}'))
        ax.tick_params(axis='both', which='major', labelsize=10, direction='in', length=4, width=1)
        #axr.tick_params(axis='both', which='major', labelsize=10, direction='in', length=4, width=1)  # Unify right axis tick style

    fig.text(0.02, 0.5, "Residuals (μs)", va='center', rotation=90, fontsize=16)  # Left axis global label
    #fig.text(0.95, 0.5, "Residuals (pulse phase)", va='center', rotation=90, fontsize=16)  # Right axis global label
    # Save the figure in different formats
    # plt.tight_layout()
    left_margin = margin_width * left_ratio
    right_margin = margin_width * right_ratio
    bottom_margin = margin_height * bottom_ratio
    top_margin = margin_height * top_ratio
    left = left_margin / fig_width
    right = 1 - (right_margin / fig_width)
    bottom = bottom_margin / fig_height
    top = 1 - (top_margin / fig_height)

    plt.subplots_adjust(
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        hspace=0.15,
        wspace=0.25
    )
    for ext in ["png", "pdf", "eps"]:
    #for ext in ["png"]:
        #plt.savefig(f"{output_prefix}.{ext}", bbox_inches="tight", dpi=300)
        plt.savefig(f"{output_prefix}.{ext}", bbox_inches=None, dpi=300)
    plt.close()

# ========== 3. Main program entry ==========
def main():
    parser = argparse.ArgumentParser(
        description="Plot pulsar timing residuals from TEMPO resid2.tmp files.\n"
                    "Example: python residuals_plot.py -resfile psr1_resid.tmp,psr2_resid.tmp -name PSR1,PSR2 -row 2 -col 1 -x MJD -o output_plot",
                    formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-resfile", type=str, required=True, help="Comma-separated list of residual files")
    parser.add_argument("-name", type=str, default=None, help="Comma-separated list of pulsar names for labeling")
    parser.add_argument("-row", type=int, required=True, help="Number of subplot rows")
    parser.add_argument("-col", type=int, required=True, help="Number of subplot columns")
    parser.add_argument("-x", type=str, default="MJD", help="X-axis type: 'MJD' or 'orbit'")
    parser.add_argument("-o", type=str, required=True, help="Output filename prefix")
    args = parser.parse_args()
    files = args.resfile.split(",")
    names = args.name.split(",") if args.name else None
    if names and len(names) != len(files):
        raise ValueError("Number of names must match number of residual files.")

    res_list = []
    for i, f in enumerate(files):
        r = read_residuals(f)
        r.filename = f
        if names:
            r.label = names[i].strip()
        else:
            r.label = os.path.basename(f).split("_")[0]
        res_list.append(r)

    plot_residuals(res_list, args.row, args.col, args.x, args.o)

if __name__ == "__main__":
    main()
