#!/usr/bin/env python
# @ Dejiang Yin -- 2025/01/04
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
import argparse
from builtins import map
import re
import glob
import presto.sifting as sifting
from operator import itemgetter, attrgetter
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as ticker 
import os
import shutil

# Create an argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description='Pulsar Candidate Sifting routine by Dejiang Yin @ 2025/01/04. \nThe script is adapted from ACCEL_sift.py of PRESTO. \nPRESTO: https://github.com/scottransom/presto')
parser.add_argument('-ACCEL', type=int, default=20, help='The suffix of accelsearch results files from PRESTO.\nDefault=20')
parser.add_argument('-JERK', type=int, default=None, help='The suffix for JERK files.\nDefault=None')
parser.add_argument('-minP', type=float, default=0.5, help='Ignore candidates with Minimum period less than this (ms).\nDefault=0.5')
parser.add_argument('-maxP', type=float, default=15000.0, help='Ignore candidates with Maximum period more than this (ms).\nDefault=15000')
parser.add_argument('-numP', type=int, default=2, help='The number of each candidate appears in different trial DM, at least!\nDefault=2')
parser.add_argument('-rDM', type=float, default=100.0, help='The range of detected trial DM for each candidate.\nDefault=100')
parser.add_argument('-minDM', type=float, default=2.0, help='Lowest DM to consider as a "real" pulsar.\nDefault=2')
parser.add_argument('-minS', type=float, default=2.0, help='Ignore candidates with a sigma less than this.\nDefault=2')
parser.add_argument('-maxS', type=float, default=100.0, help='Ignore candidates with a sigma more than this.\nDefault=100')
parser.add_argument('-cpu', type=int, default=10, help='Number of processes to use for generate the DM - Sigma plot in parallel (cpu number).\nDefault=10')
parser.add_argument('-c_pow_threshold', type=float, default=100.0, help='Ignore candidates with a coherent power less than this.\nDefault=100.0')
parser.add_argument('-harm_pow_cutoff', type=float, default=8.0, help='Ignore any candidates where at least one harmonic does exceed this power.\nDefault=8.0')
parser.add_argument('-r_err', type=float, default=1.1, help='How close a candidate has to be to another candidate to consider it the same candidate (in Fourier bins).\nDefault=1.1')

args = parser.parse_args()

DM_range = args.rDM
sigma_max = args.maxS
Num_processes = args.cpu

if args.JERK is not None:
    globaccel = f"*_ACCEL_{args.ACCEL}_JERK_{args.JERK}"
else:
    globaccel = f"*_ACCEL_{args.ACCEL}"

# glob for .inf files
globinf = "*DM*.inf"
# In how many DMs must a candidate be detected to be considered "good"
min_num_DMs = args.numP
# Lowest DM to consider as a "real" pulsar
low_DM_cutoff = args.minDM
# Ignore candidates with a sigma (from incoherent power summation) less than this
sifting.sigma_threshold = args.minS
# Ignore candidates with a coherent power less than this
sifting.c_pow_threshold = args.c_pow_threshold
# How close a candidate has to be to another candidate to consider it the same candidate (in Fourier bins)
sifting.r_err = args.r_err
# Ignore any candidates where at least one harmonic does exceed this power
sifting.harm_pow_cutoff = args.harm_pow_cutoff

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

# Shortest period candidates to consider (s)
sifting.short_period = args.minP / 1000  # 转换为秒
# Longest period candidates to consider (s)
sifting.long_period = args.maxP / 1000  # 转换为秒
#--------------------------------------------------------------
# Try to read the .inf files first, as _if_ they are present, all of
# them should be there.  (if no candidates are found by accelsearch
# we get no ACCEL files...
inffiles = glob.glob(globinf)
candfiles = glob.glob(globaccel)
"""
# Check to see if this is from a short search
if len(re.findall("_[0-9][0-9][0-9]M_" , inffiles[0])):
    dmstrs = [x.split("DM")[-1].split("_")[0] for x in candfiles]
else:
    dmstrs = [x.split("DM")[-1].split(".inf")[0] for x in inffiles]
dms = list(map(float, dmstrs))
dms.sort()
dmstrs = ["%.2f"%x for x in dms]
"""
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
# Check if the 'ACCEL' directory exists, if so, remove it and recreate it
if os.path.exists("ACCEL"):
    shutil.rmtree("ACCEL")
os.makedirs("ACCEL")
os.makedirs("./ACCEL/DmSigmaFig")
os.makedirs("./ACCEL/ACCEL_fig")
# Write candidates to STDOUT
if len(cands):
    cands.sort(key=attrgetter('sigma'), reverse=True)
    # sifting.write_candlist(cands)
    sifting.write_candlist(cands, './ACCEL/cands.txt')  # add by Dejiang Yin

######----------------------------------------------------------------------------------
# Process 'cands.txt' to generate 'Cands.txt' with required format
with open("./ACCEL/cands.txt", "r") as fin, open("./ACCEL/Cands.txt", "w") as fout:
    for line in fin:
        # Check if the line contains a time pattern (e.g., 'HH:MM')
        if re.search(r'\d+:\d+', line):
            parts = line.strip().split()
            if len(parts) >= 8:
                fout.write(f"{parts[7]}_DM{parts[1]} {line}")

# Open and read the contents of 'cands.txt'
with open('./ACCEL/cands.txt', 'r') as f:
    lines = f.readlines()
# Step 1: Remove lines starting with '#' and capture the content after '#'
filtered_lines = [line for line in lines if not line.startswith('#')]
# Step 2: Handle the logic similar to AWK for processing 'DM=' lines
last = ""
processed_lines = []
for line in filtered_lines:
    if 'DM=' in line:
        processed_lines.append(f"{last}\t{line}")
    else:
        processed_lines.append(line)
        last = f"{line.split()[7]}{line.split()[10]}{line.split()[1]}"
# Step 3: Remove lines containing '_ACCEL_'
processed_lines = [line for line in processed_lines if '_ACCEL_' not in line]
# Step 4: Use regular expressions to remove special characters (e.g., '*', 'DM=', 'SNR=', 'Sigma=')
processed_lines = [re.sub(r'\*|DM=|SNR=|Sigma=', '', line) for line in processed_lines]
# Step 5: Replace content inside parentheses with '_DM'
processed_lines = [re.sub(r'\([^)]*\)', '_DM', line) for line in processed_lines]
# Write the processed content to 'Cands_all.txt' in the './ACCEL' directory
with open('./ACCEL/Cands_all.txt', 'w') as f:
    f.writelines(processed_lines)
# print("Processing complete. Output saved to './ACCEL'.")
# read data to plot DM-Sigma or SNR 
with open('./ACCEL/Cands_all.txt', 'r') as f:
    lines = f.readlines()

data = []
for line in lines:
    row = line.strip().split()
    data.append(row)

Df = pd.DataFrame(data, columns=['p_DM', 'DM', 'SNR', 'Sigma'])
Df['DM'] = pd.to_numeric(Df['DM'], errors='coerce')
Df['Sigma'] = pd.to_numeric(Df['Sigma'], errors='coerce')
Df['SNR'] = pd.to_numeric(Df['SNR'], errors='coerce')
Df.to_csv('./ACCEL/Cands_all.csv', index=False)
#read  all information of  total candidates 
with open('./ACCEL/Cands.txt', 'r') as f:
    lines = f.readlines()

data = []
for line in lines:
    row = line.strip().split()
    data.append(row)

df = pd.DataFrame(data, columns=['p_DM','file:candnum', 'DM', 'SNR', 'Sigma', 'numharm', 'ipow', 'cpow', 'P(ms)', 'r', 'z', 'numhits'])
df.insert(12, 'DM1', 'DM' + df.iloc[:, 2].astype(str))

df[['file','candnum']] = df['file:candnum'].str.split(':', expand=True)
df.drop('file:candnum', axis=1, inplace=True)

# Name of the new column for zmax
new_col_name_zmax = 'zmax'
# Name of the new column for wmax
new_col_name_wmax = 'wmax'
# List to store zmax values
zmax_data = []
# List to store wmax values
wmax_data = []
for index, row in df.iterrows():
    fire = row['file']
    firelist = fire.split('_')
    if args.JERK is None:
        # If JERK is not provided, take the last part of the split file name as zmax
        zmax = firelist[-1]
        # Set wmax to None when there is no JERK
        wmax = None
    else:
        # If JERK is provided, take the third - last part of the split file name as zmax
        zmax = firelist[-3]
        # Take the last part of the split file name as wmax
        wmax = firelist[-1]
    zmax_data.append(zmax)
    wmax_data.append(wmax)

# Add zmax column to the DataFrame
df[new_col_name_zmax] = zmax_data
# Add wmax column to the DataFrame
df[new_col_name_wmax] = wmax_data
# print(df)
candidate_p = df
candidate_P = candidate_p.copy()
#candidate_P.loc[:, ['DM', 'Sigma','SNR']] = candidate_P.loc[:, ['DM', 'Sigma','SNR']].apply(pd.to_numeric)
candidate_P[['DM', 'Sigma', 'SNR']] = candidate_P[['DM', 'Sigma', 'SNR']].apply(pd.to_numeric)
candidate_p_DM = list(df["p_DM"])
df[['p', 'DM2']] = df['p_DM'].str.split('_', expand=True)
df.to_csv('./ACCEL/Cands.csv', index=False)
# print(df)
##------------------------------------------------------
# add another conditons for candidates selection, DM range.
# This is effective for selecting faint millisecond pulsars with high dispersion measures.
Df['DM'] = Df['DM'].astype(float)
CAND = []
Non_CAND = []

for i in range(len(candidate_p_DM)):
    if ( (max(Df[Df["p_DM"] == candidate_p_DM[i]].DM) - min(Df[Df["p_DM"] == candidate_p_DM[i]].DM))  <= DM_range ) \
    and ( max(Df[Df["p_DM"] == candidate_p_DM[i]].Sigma)  <= sigma_max ):
    # You can add other conditions here.
        CAND.append(candidate_p_DM[i])
    else:
        Non_CAND.append(candidate_p_DM[i])

p = []
p_DM = []
dm = []
cand = []

for i in CAND:
    candi = df[df["p_DM"] == i ]
    dm.append(candi["DM1"].values[0])
    cand.append(candi["candnum"].values[0])
    p_DM.append(candi["p_DM"].values[0])
    p.append(candi["p"].values[0])
       
c ={"CAND":cand,
   "DM":dm,
   "p_DM":p_DM,
   "p":p}

best_cand = pd.DataFrame(c)
best_cand.to_csv("./ACCEL/"+'best_Candidate.csv',sep=',',index=0,header=1)

## the following information is to prepfold candidate, DM and Cand number
DM={"DM" : dm}
DM = pd.DataFrame(DM)
DM_T = DM.T
DM_T.to_csv('./ACCEL/'+str(len(best_cand)) +'-ACCEL-DM.txt',sep=' ',index=0,header=0)

accelcand = {"accelcand" : cand}
accelcand = pd.DataFrame(accelcand)
accelcand_T = accelcand.T
accelcand_T.to_csv('./ACCEL/'+str(len(best_cand)) +'-ACCEL-accelcand.txt',sep=' ',index=0,header=0)
print("ACCEL_sifty candidate numbers:",len(best_cand))

Pms = {"Pms" : p}
Pms = pd.DataFrame(Pms)
Pms_T = Pms.T
Pms_T.to_csv('./ACCEL/'+str(len(CAND)) +'-ACCEL-Pms.txt',sep=' ',index=0,header=0)

###  DM - Sigma relation figure
def generate_plot(i):
    candidate_ = Df[Df["p_DM"] == CAND[i]]
    candidate_1 = candidate_.copy()
    #candidate_1.loc[:, ['DM', 'Sigma','SNR']] = candidate_1.loc[:, ['DM', 'Sigma','SNR']].apply(pd.to_numeric)
    candidate_1[['DM', 'Sigma', 'SNR']] = candidate_1[['DM', 'Sigma', 'SNR']].apply(pd.to_numeric)
    candi = candidate_P[candidate_P["p_DM"] == CAND[i]]
    fig,ax = plt.subplots(1,1,figsize=(10, 3))
    d = {'DM': candidate_1["DM"], 'Sigma': candidate_1["Sigma"], 'SNR':candidate_1["SNR"]}
    df = pd.DataFrame(data=d)
    df = df.sort_values(by='DM', ascending=True)
    #ax0 = ax.scatter(df['DM'], df['Sigma'], c=df['SNR'], cmap="cool")
    ax0 = ax.scatter(df['DM'], df['Sigma'], c=df['SNR'], cmap="jet")
    ax.scatter(df['DM'], df['Sigma'], marker='o', facecolors='none', edgecolors='#000000', s=50,linewidths=1.5)
    ax.plot(df['DM'], df['Sigma'],color="#791E94")
    if args.JERK is None:
   	 ax.axvline(candi["DM"].values[0],c="#791E94",linestyle='--', linewidth=1, \
               label="DM / sigma: "+str(candi["DM"].values[0])+ " / "+ str(candi["Sigma"].values[0]) + "\n "
               "period: " + candi["P(ms)"].values[0] + " (ms)\n"
               "z: " + zmax_data[0] + "; " + "cand: " + candi["candnum"].values[0]+ "\n"
               "harm: " + candi["numharm"].values[0] + "; " + "FFT'z': " + candi["z"].values[0])
    else:
    	ax.axvline(candi["DM"].values[0],c="#791E94",linestyle='--', linewidth=1, \
               label="DM / sigma: "+str(candi["DM"].values[0])+ " / "+ str(candi["Sigma"].values[0]) + "\n "   
               "period: " + candi["P(ms)"].values[0] + " (ms)\n"
               "z / w: " + zmax_data[0] + " / " + wmax_data[0]+ "; " + "cand: " + candi["candnum"].values[0]+ "\n"
               "harm: " + candi["numharm"].values[0] + "; " + "FFT'z': " + candi["z"].values[0])
    ax.legend(fontsize=9)
    ax.set_xlabel("Trial DM" +" (cm$^{-3}$ pc)", fontsize=9)
    ax.set_ylabel("Sigma",fontsize=9)
    ax.tick_params(direction="in")
    ax.tick_params(axis='y', rotation=90)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    # ax.set_xlim(min(candidate_1["DM"])-0.05 ,max(candidate_1["DM"])+0.05)
    cbar = fig.colorbar(ax0, ax=ax, label="SNR",pad = 0.01, fraction=0.05)
    cbar.set_label(label="SNR", size=9)   
    plt.savefig("./ACCEL/DmSigmaFig/" +candi["DM1"].values[0]+ "_"+"Cand"+"_" + candi["candnum"].values[0] +".png",bbox_inches="tight",dpi=200 )
    #plt.savefig("./ACCEL_PCSSP1/DmSigmaFig/" +candidate_P["DM1"][i]+ "_"+"Cand"+"_" + candidate_P["candnum"][i] +".jpg",bbox_inches="tight",dpi=200 )
    plt.cla()
    plt.clf()
    plt.close("all")

if __name__ == '__main__':
    # Define the number of processes to use
    num_processes = Num_processes  # You can adjust this as needed
    # Create a pool of processes
    pool = Pool(processes=num_processes)
    # Define the range of iterations
    iterations = range(len(CAND))
    # Run the function in parallel
    pool.map(generate_plot, iterations)
    # Close the pool
    pool.close()
    pool.join()
