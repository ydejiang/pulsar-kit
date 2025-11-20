import logging
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import astropy.units as uu
from astropy.time import Time
# from datetime import datetime
import textwrap
import matplotlib.ticker as ticker 
import os

log = logging.getLogger('riptide.candidate')

class Candidate(object):
    """
    Final data product of the riptide pipeline

    Attributes
    ----------
    params : dict
        Dictionary with best-fit parameters of the signal:
        period, freq, dm, width, ducy, snr

    tsmeta : Metadata
        Metadata of the TimeSeries object (DM trial) in which the Candidate was
        found to have the highest S/N, and from which it was folded

    peaks : pandas.DataFrame
        A pandas DataFrame with the attributes of the periodogram peaks
        associated to the Candidate

    subints : ndarray
        A two-dimensional numpy array with shape (num_subints, num_bins)
        containing the folded sub-integrations

    profile : ndarray
        Folded profile as a one-dimensional numpy array, normalised such that
        the background noise standard deviation is 1, and the mean of the
        profile is zero

    dm_curve : tuple
        Tuple of numpy arrays (dm, snr) containing respectively the sequence
        of DM trials, and corresponding best S/N value across all trial widths
    """
    def __init__(self, params, tsmeta, peaks, subints):
        self.params = params
        self.tsmeta = tsmeta
        self.peaks = peaks
        self.subints = subints

    def to_dict(self):
        """ Convert to dictionary for serialization """
        return {
            'params': self.params,
            'tsmeta': self.tsmeta,
            'peaks': self.peaks,
            'subints': self.subints
        }

    @property
    def profile(self):
        if self.subints.ndim == 1:
            return self.subints
        return self.subints.sum(axis=0)

    @property
    def dm_curve(self):
        # NOTE: copy() works around a bug in pandas 0.23.x and earlier
        # https://stackoverflow.com/questions/53985535/pandas-valueerror-buffer-source-array-is-read-only
        # TODO: consider requiring pandas 0.24+ in the future
        df = self.peaks.copy().groupby('dm').max()
        return df.index.values, df.snr.values

    @classmethod
    def from_pipeline_output(cls, ts, peak_cluster, bins, subints=1):
        """
        Method used by the pipeline to produce a candidate from intermediate
        data products. 
        
        subints can be an int or None. None means pick the number of subints
        that fit inside the data.

        If 'subints' is too large to fit in the data, then
        this function will call TimeSeries.fold() with subints=None.
        """
        centre = peak_cluster.centre
        P0 = centre.period

        if subints is not None and subints * P0 >= ts.length:
            msg = (
                f"Period ({P0:.3f}) x requested subints ({subints:d}) exceeds time series length "
                f"({ts.length:.3f}), setting subints = full periods that fit in the data"
            )
            log.debug(msg)
            subints = None

        subints_array = ts.fold(centre.period, bins, subints=subints)
        return cls(centre.summary_dict(), ts.metadata, peak_cluster.summary_dataframe(), subints_array)

    @classmethod
    def from_dict(cls, items):
        """ De-serialize from dictionary """
        return cls(items['params'], items['tsmeta'], items['peaks'], items['subints'])
    #def plot(self, figsize=(18, 4.5), dpi=80):  # modify by Dejiang
    def plot(self, figsize=(16, 11), dpi=160):

        """
        Create a plot of the candidate

        Parameters
        ----------
        figsize : tuple
            figsize argument passed to plt.figure()
        dpi : int
            dpi argument passed to plt.figure()

        Returns
        -------
        fig : matplotlib.Figure
        """
        fig = plt.figure(figsize=figsize, dpi=dpi)
        plot_candidate(self)
        return fig

    def show(self, **kwargs):
        """
        Create a plot of the candidate and display it. Accepts the same keyword
        arguments as plot().
        """
        self.plot(**kwargs)
        plt.show()

    def savefig(self, fname, **kwargs):
        """
        Create a plot of the candidate and save it as PNG under the specified 
        file name. Accepts the same keyword arguments as plot().
        """
        fig = self.plot(**kwargs)
        # fig.savefig(fname)
        fig.savefig(fname, bbox_inches="tight", pad_inches=0.15)
        name, _ = os.path.splitext(fname); pdf_fname = f"{name}.pdf"; fig.savefig(pdf_fname, bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)

    def __str__(self):
        name = type(self).__name__
        return f"{name}({self.params})"

    def __repr__(self):
        return str(self)


TableEntryBase = namedtuple('TableEntry', ['name', 'value', 'formatter', 'unit'])


class TableEntry(TableEntryBase):
    def plot(self, X, y, **kwargs):
        """
        X : list
            list of X coordinates for each column
        y : float
            Y coordinate of the line
        """
        assert(len(X) == 3)
        fmt = "{{:{}}}".format(self.formatter)
        plt.text(X[0], y, self.name, **kwargs)
        plt.text(X[1], y, fmt.format(self.value), ha='right', **kwargs)
        plt.text(X[2], y, self.unit, **kwargs)

################################################################################################
################################################################################################
## original code
'''
def plot_table(params, tsmeta):
    """
    """
    #plt.axis('off')
    coord = tsmeta['skycoord']
    ra_hms = coord.ra.to_string(unit=uu.hour, sep=':', precision=2, pad=True)
    dec_hms = coord.dec.to_string(unit=uu.deg, sep=':', precision=2, pad=True)

    # TODO: Check that the scale is actually UTC in the general case
    # PRESTO, SIGPROC and other packages may not have the same
    # date/time standard
    obsdate = Time(tsmeta['mjd'], format='mjd', scale='utc', precision=0)

    blank = TableEntry(name='', value='', formatter='s', unit='')

    entries = [
        TableEntry(name='Period', value=params['period'] * 1000.0, formatter='.6f', unit='ms'),
        TableEntry(name='DM', value=params['dm'], formatter='.2f', unit='pc cm$^{-3}$'),
        TableEntry(name='Width', value=params['width'], formatter='d', unit='bins'),
        TableEntry(name='Duty cycle', value=params['ducy'] * 100.0, formatter='.2f', unit='%'),
        TableEntry(name='S/N', value=params['snr'], formatter='.1f', unit=''),
        blank,
        TableEntry(name='Source', value=tsmeta['source_name'], formatter='s', unit=''),
        TableEntry(name='RA', value=ra_hms, formatter='s', unit=''),
        TableEntry(name='Dec', value=dec_hms, formatter='s', unit=''),
        TableEntry(name='MJD', value=obsdate.mjd, formatter='.6f', unit=''),
        TableEntry(name='UTC', value=obsdate.iso, formatter='s', unit=''),

        TableEntry(name='analyst', value=tsmeta['analyst'], formatter='s', unit=''),
    ]

    y0 = 0.94  # Y coordinate of first line
    dy = 0.085  # line height
    X = [0.1, 0.50, 0.64] # Coordinate of columns name, value, unit

    for ii, entry in enumerate(entries):
        entry.plot(X, y0 - ii * dy, family='monospace', fontsize=16)


    ax = plt.gca()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")

    ax = plt.gca()
    ax.tick_params(axis='both', which='major',
               direction='in', length=8, width=1.5,
               labelsize=12)

def plot_dm_curve(dm, snr):
    dm_min = dm.min()
    dm_max = dm.max()
    plt.plot(dm, snr, color="r", marker="o", markersize=3)

    # Avoid matplotlib warning when calling xlim() with two equal values
    if dm_min == dm_max:
        plt.xlim(dm_min - 0.5, dm_min + 0.5)
    else:
        plt.xlim(dm_min, dm_max)
    plt.grid(linestyle=":")
    plt.xlabel("DM (pc cm$^{-3}$)")
    plt.ylabel("Best S/N")


def plot_subints(X, T):
    """
    X : ndarray
        Sub-integrations array, shape = (nsubs, nbins)
    T : float
        Integration time in seconds
    """
    __, nbins = X.shape

    X = np.hstack((X, X[:, : nbins // 2]))
    __, nbins_ext = X.shape

    plt.imshow(
        X,
        cmap="Greys",
        interpolation="nearest",
        aspect="auto",
        extent=[-0.5, nbins_ext - 0.5, T, 0],  # Note: t = 0 is at the top of the plot
    )
    plt.fill_between([nbins, nbins_ext], [0, 0], [T, T], color="b", alpha=0.08)
    plt.xlim(-0.5, nbins_ext - 0.5)
    plt.ylabel("Time (seconds)")
    plt.title("1.5 Periods of Signal")


def plot_profile(P):
    """
    P : profile normalised to unit background noise variance
    """
    nbins = len(P)
    P = np.concatenate((P, P[: nbins // 2]))
    nbins_ext = len(P)

    plt.bar(range(nbins_ext), P - np.median(P), width=1, color="#404040")

    ymin, ymax = plt.ylim()
    plt.fill_between(
        [nbins, nbins_ext], [ymin, ymin], [ymax, ymax], color="b", alpha=0.08
    )
    plt.ylim(ymin, ymax)

    plt.xlim(-0.5, nbins_ext - 0.5)
    plt.xlabel("Phase bin")
    plt.ylabel("Normalised amplitude")


def plot_candidate(cand):
    """
    Plot candidate on the current figure
    """
    # https://matplotlib.org/tutorials/intermediate/gridspec.html
    nrows, ncols = 2, 7
    gs = GridSpec(nrows, ncols, figure=plt.gcf())

    plt.subplot(gs[:1, 2:])
    plot_subints(cand.subints, cand.tsmeta["tobs"])

    plt.subplot(gs[1:, 2:])
    plot_profile(cand.profile)

    plt.subplot(gs[:1, :2])
    plot_table(cand.params, cand.tsmeta)

    plt.subplot(gs[1:, :2])
    plot_dm_curve(*cand.dm_curve)

    plt.tight_layout()

'''

################################################################################################
################################################################################################
## modify by Dejiang Yin

def plot_table(params, tsmeta):
    """
    Plot parameter table in a two-column layout (left-right side by side) with centered title.
    Follows original TableEntry definition requiring 'unit' parameter.
    """
    # Extract and format sky coordinates (RA/Dec) from metadata
    # TODO: Check that the scale is actually UTC in the general case
    # PRESTO, SIGPROC and other packages may not have the same
    # date/time standard
    coord = tsmeta['skycoord']
    ra_hms = coord.ra.to_string(unit=uu.hour, sep=':', precision=2, pad=True)
    dec_hms = coord.dec.to_string(unit=uu.deg, sep=':', precision=2, pad=True)
    # Convert observation time from MJD to UTC
    obsdate = Time(tsmeta['mjd'], format='mjd', scale='utc', precision=0)
    # Add centered title
    title_text = "riptide: Finding pulsars with the Fast Folding Algorithm"
    plt.text(
        x=0.5, 
        y=0.97, 
        s=title_text, 
        ha='center', 
        va='top', 
        #family='cursive', 
        fontsize=24,
        #fontweight='bold'
    )
   # --------------------------
    # Column-specific titles
    # --------------------------
    # Left column title: "Observation information"
    plt.text(
        x=0.25,  # Center of left column (between 0.05 and 0.35)
        y=0.89, 
        s="Observation information", 
        ha='center', 
        va='top', 
        #family='fantasy', 
        fontsize=20,
        #fontweight='bold'
    )

    # Right column title: "Search information"
    plt.text(
        x=0.75,  # Center of right column (between 0.55 and 0.85)
        y=0.89, 
        s="Search information", 
        ha='center', 
        va='top', 
        #family='monospace', 
        fontsize=20,
        #fontweight='bold'
    )
    ax = plt.gca()  # Get the current axes object (the subplot being worked on)
    # Basename text: Left-aligned + Auto-wrap for long text + Fixed Y-height
    basename = tsmeta['basename']
    wrapped_text = textwrap.fill(f"File: {basename}", width=57)
    
    ax.text(
    x=0.02,               # Left-alignment starting point: 5% to the right of the subplot's left edge
                          # (align with other left-aligned text elements in the plot)
    y=0.13,               # Fixed Y-height: 12% of the subplot's total height (adjust as needed)
    s=wrapped_text ,  # Text content: Combine label with the actual basename
    #s=textwrap.fill(f"Basename: {tsmeta['basename']}", width=30),
    ha='left',            # Horizontal alignment: Left-aligned (text extends right from x=0.05)
    va='top',             # Vertical alignment: Top-aligned (text base starts at y=0.12 and extends downward)
    family='monospace',   # Font family: Monospace (match the font of other text elements for consistency)
    fontsize=20,          # Font size (adjust based on overall plot scaling)
    transform=ax.transAxes,  # Coordinate system: Axes-relative coordinates (0-1 range for both X/Y)
                             # Ensures position stays consistent regardless of data range or subplot size
     wrap=True            # Auto-wrap enabled: Long text will automatically wrap to new lines
    )


    ax = plt.gca()
    current_time = Time.now()
    time_str = current_time.isot.split('.')[0] + ' UTC'
    ax.text(
        x=0.915, y=0.17,
        s=f'@: {time_str}',
        transform=ax.transAxes,  
        ha='right', va='bottom',
        fontsize=20,
    )
    # --------------------------
    # Define entries with ALL required parameters (including 'unit' as per original definition)
    # --------------------------
    # Left column: Core physical parameters
    left_entries = [
        # TableEntry requires: name, value, formatter, unit (original signature)
      TableEntry(
            name='Source', 
            value=tsmeta['source_name'], 
            formatter='s', 
            unit=''  # String values still need unit parameter
        ),
        TableEntry(
            name='RA', 
            value=ra_hms, 
            formatter='s', 
            unit=''
        ),
        TableEntry(
            name='Dec', 
            value=dec_hms, 
            formatter='s', 
            unit=''
        ),
        TableEntry(
            name='MJD', 
            value=obsdate.mjd, 
            formatter='.6f', 
            unit=''
        ),
        TableEntry(
            name='Date', 
            value=obsdate.strftime('%Y-%m-%d'), 
            formatter='s', 
            unit=''
        ),
#        TableEntry(
#            name='Observer', 
#            value=tsmeta['observer'], 
#            formatter='s', 
#            unit=''
#        ),
        TableEntry(
            name='Telescope',
            value=tsmeta['telescope'],
            formatter='s',
            unit=''
        ),
        TableEntry(
            name='Instrument',
            value=tsmeta['instrument'],
            formatter='s',
            unit=''
        ),
         TableEntry(
            name='Analyst',
            value=tsmeta['analyst'],
            formatter='s',
            unit=''
        ),
    ]

    # Right column: Source info & observation time
    right_entries = [
 
        TableEntry(
            name='Period (ms)', 
            value=params['period'] * 1000.0,  # Keep numeric value (not formatted string)
            formatter='.6f',  # Format specifier for numeric value
            unit=''  # Unit as separate parameter (critical for original class)
        ),
        TableEntry(
            name='DM (pc cm$^{-3}$)', 
            value=params['dm'], 
            formatter='.2f', 
            unit=''
        ),
        TableEntry(
            name='Width (bins)', 
            value=params['width'], 
            formatter='d', 
            unit=''
        ),
        TableEntry(
            name='Duty cycle (%)', 
            value=params['ducy'] * 100.0, 
            formatter='.2f', 
            unit=''
        ),
        TableEntry(
            name='S/N', 
            value=params['snr'], 
            formatter='.2f', 
            unit=''  # Empty string for no unit (but still required)
        ),
        TableEntry(
            name='Tobs (s)',
            value=tsmeta['tobs'],
            formatter='.2f',
            unit=''
        ),
        TableEntry(
            name='Barycentered',
            value=tsmeta['barycentered'],
            formatter='',
            unit=''
        ),
    ]

    # Layout parameters (adjusted for title)
    y0 = 0.78  # Lowered to make space for title
    dy = 0.086   # Row spacing
    left_X = [0.02, 0.46, 0.49]  # Original 3-column X coordinates (name, value, unit)
    right_X = [0.52, 0.97, 0.99]  # Right column uses same 3-column structure

    # Plot left column
    for row_idx, entry in enumerate(left_entries):
        entry.plot(
            X=left_X,
            y=y0 - row_idx * dy,
            family='monospace',
            fontsize=22
        )

    # Plot right column
    max_row_count = max(len(left_entries), len(right_entries))
    for row_idx in range(max_row_count):
        if row_idx < len(right_entries):
            entry = right_entries[row_idx]
            entry.plot(
                X=right_X,
                y=y0 - row_idx * dy,
                family='monospace',
                fontsize=22
            )

    # Hide axis elements
    ax = plt.gca()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax = plt.gca()
    ax.tick_params(axis='both', which='major',
               direction='in', length=8, width=1.5,
               labelsize=14)

def plot_dm_curve(dm, snr):
    dm_min = dm.min()
    dm_max = dm.max()
    #plt.plot(dm, snr, color='r', marker='o', markersize=3)
    #plt.plot(dm, snr, marker='o', markersize=8, color='black', linestyle='--', linewidth=2)
    plt.plot(dm, snr, marker='o', markersize=12, color='black', linewidth=2., markeredgecolor='black',markerfacecolor='none', markeredgewidth=2.0)
    max_snr_idx = snr.argmax()
    max_dm = dm[max_snr_idx]
    max_snr = snr[max_snr_idx]
    plt.axvline(x=max_dm, color='black', linestyle='--', linewidth=2.2,
                label='optimal S/N')

    # Avoid matplotlib warning when calling xlim() with two equal values 
    if dm_min == dm_max:
        plt.xlim(dm_min - 0.5, dm_min + 0.5)
    else:
        plt.xlim(dm_min, dm_max)
    plt.grid(linestyle=':')
    #plt.xlabel("Trial DM (pc cm$^{-3}$)")
    plt.xlabel("Trial DM (pc cm$^{-3}$)", fontsize=16)
    plt.ylabel("Best S/N", fontsize=16)
    plt.tick_params(axis='y', labelrotation=90)
    plt.legend(loc='best',fontsize=18)
    #ax = plt.gca()
    #ax.set_xticks([])
    ax = plt.gca()
    ax.tick_params(axis='both', which='major',
               direction='in', length=6, width=1.5,
               labelsize=14)
    ax.tick_params(axis='x', top=True, labeltop=False)
    ax.tick_params(axis='y', right=True, labelright=False) 

def plot_subints(X, T):
    """
    X : ndarray
        Sub-integrations array, shape = (nsubs, nbins)
    T : float
        Integration time in seconds
    """
    nsubs, nbins = X.shape  # Get number of sub-integrations and phase bins
    # --------------------------
    # Core: Local normalization (each sub-integration scaled to 0~1 independently)
    # --------------------------
    X_norm = np.zeros_like(X, dtype=np.float32)
    for i in range(nsubs):
        sub_data = X[i, :]
        min_val = np.min(sub_data)
        max_val = np.max(sub_data)
        if np.isclose(min_val, max_val, atol=1e-7):
            X_norm[i, :] = 0.0  # Set flat data (no fluctuation) to 0
        else:
            X_norm[i, :] = (sub_data - min_val) / (max_val - min_val)  # Normalize to 0~1 range

    # Extend phase to two periods
    X_norm = np.hstack((X_norm, X_norm[:, :nbins//2 * 2]))
    _, nbins_ext = X_norm.shape
    # Define extent in phase (0~2) and time (0~T) units
    extent = [0, 2, 0, T]
    # Use reversed grayscale (white→black gradient, stronger signals appear darker, matching Presto style)
    plt.imshow(
        X_norm,
        cmap='gray_r',  # Replace viridis with reversed grayscale to mimic Presto's white-black gradient
        interpolation='nearest',
        aspect='auto',
        extent=extent,
        origin='upper'  # So t=0 is at the top
    )
    # Highlight the second period region (1.0–2.0)
    plt.fill_between([1, 2], [0, 0], [T, T], color='b', alpha=0.04)
    # Axis settings
    plt.xlim(0, 2)
    plt.ylabel("Time (seconds)", fontsize=16)
    plt.xlabel("Pulse Phase (2 Periods)", fontsize=16)
    plt.tick_params(axis='y', labelrotation=90)
    # Phase axis ticks
    plt.xticks([0.0, 0.5, 1.0, 1.5, 2.0], fontsize=14)
    ax = plt.gca()
    #ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    #ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    # Tick style
    ax = plt.gca()
    ax.tick_params(
        axis='both',
        which='major',
        direction='in',
        length=6,
        width=1.5,
        labelsize=14
    )
    #ax.tick_params(axis='both', which='minor', direction='in', length=6,width=1.5,labelsize=12)
    ax.tick_params(axis='x', top=True, labeltop=False) 
    ax.tick_params(axis='y', right=True, labelright=False)

def plot_profile(P):
    """
    P : profile normalised to unit background noise variance
    """
    nbins = len(P)
    # Extend profile to 2 periods
    P = np.concatenate((P, P[:nbins//2 * 2]))
    nbins_ext = len(P)
    # Convert bin index to phase (0–2)
    phase = np.linspace(0, 2, nbins_ext, endpoint=False)
    # Plot profile
    plt.plot(phase, P - np.median(P), color='black', lw=2.)
    plt.axhline(y=0, color='gray', linestyle='--', linewidth=1)
    ymin, ymax = plt.ylim()
    # Fill the second period region (1.0–2.0)
    plt.fill_between([1, 2], [ymin, ymin], [ymax, ymax], color='b', alpha=0.04)
    plt.ylim(ymin, ymax)
    # Axis limits
    plt.xlim(0, 2)
    plt.ylabel("Flux (Arb. Units)", fontsize=16)
    # Set tick positions but hide labels
    ax = plt.gca()
    ax.set_xticks([0.0, 0.5, 1.0, 1.5, 2.0])
    #ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    #ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.set_xticklabels([])   # <-- hide numbers
    #ax.set_xticks([])
    #ax.set_xticklabels([])
    #ax.set_yticklabels([])
    plt.tick_params(axis='y', labelrotation=90)
    # Beautify ticks
    ax.tick_params(axis='y', which='major',
                   direction='in', length=6, width=1.5,
                   labelsize=14)
    ax.tick_params(axis='y', right=True, labelright=False, which='major')
    ax.tick_params(axis='x', top=True, which='major',
                   direction='in', length=6, width=1.5,
                   labelsize=14)
    ax.tick_params(axis='x', top=True, labeltop=False, which='major')

def plot_candidate(cand):
    """
    Plot candidate on the current figure
    """
    # https://matplotlib.org/tutorials/intermediate/gridspec.html
    nrows, ncols = 18, 14
    gs = GridSpec(nrows, ncols, figure=plt.gcf())
    plt.subplot(gs[5:, :4])
    plot_subints(cand.subints, cand.tsmeta['tobs'])
    plt.subplot(gs[:5, :4])
    plot_profile(cand.profile)
    plt.subplot(gs[:10, 4:])
    plot_table(cand.params, cand.tsmeta)
    plt.subplot(gs[10:, 4:])
    plot_dm_curve(*cand.dm_curve)
    plt.tight_layout()


