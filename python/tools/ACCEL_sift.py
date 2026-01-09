import argparse
from builtins import map
import re
import glob
import presto.sifting as sifting
from operator import itemgetter, attrgetter

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

# Write candidates to STDOUT
if len(cands):
    cands.sort(key=attrgetter('sigma'), reverse=True)
    # sifting.write_candlist(cands)
    sifting.write_candlist(cands, 'cands.txt')
