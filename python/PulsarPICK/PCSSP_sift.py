#!/usr/bin/env python
# @ Dejiang Yin -- 2025/01/04
import pandas as pd
import os
import shutil
import re
import numpy as np
import glob
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as ticker 
from multiprocessing import Pool, Value, Lock
import argparse

# Create an argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description='Pulsar Candidate Sifting routine by Dejiang Yin @ 2025/01/04, and this code is called PCSSP_sift.py (PCSSP_sift.py is the short for Pulsar Candidate Sifting and Synthesis Pipeline). \nThe script is adapted from JinglePulsar. \nJingle Pulsar: https://github.com/jinglepulsar')
parser.add_argument('-ACCEL', type=int, default=20, help='The suffix of accelsearch results files from PRESTO.\nDefault=20')
parser.add_argument('-JERK', type=int, default=None, help='The suffix for JERK files.\nDefault=None')
parser.add_argument('-lenthP', type=int, default=4, help='The precise decimal point of the different periods divided into one group.\nDefault=4')
parser.add_argument('-minP', type=float, default=0.5, help='Ignore candidates with Minimum period less than this (ms).\nDefault=0.5')
parser.add_argument('-maxP', type=float, default=15000.0, help='Ignore candidates with Maximum period more than this (ms).\nDefault=15000')
parser.add_argument('-numP', type=int, default=2, help='The number of each candidate appears in different trial DM, at least!\nDefault=2')
parser.add_argument('-rDM', type=float, default=100.0, help='The range of trial DM for each candidate.\nDefault=100')
parser.add_argument('-minS', type=float, default=2.0, help='Ignore candidates with a sigma less than this.\nDefault=2')
parser.add_argument('-maxS', type=float, default=100.0, help='Ignore candidates with a sigma more than this.\nDefault=100')
parser.add_argument('-cpu', type=int, default=10, help='Number of processes to use for generate the DM - Sigma plot in parallel (cpu number).\nDefault=10')

args = parser.parse_args()

Period_digital = args.lenthP
Min_period = args.minP
Max_period = args.maxP
period_num_min = args.numP
DM_range = args.rDM
sigma_min = args.minS
sigma_max = args.maxS
Num_processes = args.cpu

path = os.getcwd()
os.chdir(path)

# Determine the file matching pattern based on whether the JERK parameter is set
if args.JERK is None:
    globaccel = f"*_ACCEL_{args.ACCEL}"
else:
    globaccel = f"*_ACCEL_{args.ACCEL}_JERK_{args.JERK}"

candfiles = glob.glob(globaccel)

# Check if the 'PCSSP' directory exists, if so, remove it and recreate it
if os.path.exists("PCSSP"):
    shutil.rmtree("PCSSP")
os.makedirs("PCSSP")
os.makedirs("./PCSSP/DmSigmaFig")
os.makedirs("./PCSSP/PCSSP_fig")

# Print total number of files
print(f"Reading candidates from {len(candfiles)} files")
# ----------- Global Result DF and Counter ----------- 
# Create an empty DataFrame to store the final result
DF = pd.DataFrame()
# Initialize counter to track the progress of file processing
counter = Value('i', 0)
lock = Lock()
# ----------- Candidate File Processor Function ----------- 
# Function to process each candidate file and extract data
def process_candidate_file(fire):
    new_lines = []
    if args.JERK is None:
        header = "Cand,Sigma,SummedPower,CoherentPower,NumHarm,Period(ms),Frequency(Hz),FFTr(bin),FreqDeriv(Hz/s),FFTz(bins),Accel(m/s^2),Notes"
    else:
        header = "Cand,Sigma,SummedPower,CoherentPower,NumHarm,Period(ms),Frequency(Hz),FFTr(bin),FreqDeriv(Hz/s),FFTz(bins),FFTw(bins),Accel(m/s^2),Notes"
    new_lines.append(header)

    with open(fire, 'r') as file:
        for line in file:
            if re.match(r"^[0-9]", line):
                new_line = re.sub(r"\s+", ",", line.strip())
                new_lines.append(new_line)

    processed_data = []
    if args.JERK is None:
        for line in new_lines[1:]:
            parts = line.split(',')
            processed_parts = parts[:11] + [','.join(parts[11:])] if len(parts) > 11 else parts + [''] * (12 - len(parts))
            processed_data.append(processed_parts)
    else:
        for line in new_lines[1:]:
            parts = line.split(',')
            processed_parts = parts[:12] + [','.join(parts[12:])] if len(parts) > 12 else parts + [''] * (13 - len(parts))
            processed_data.append(processed_parts)

    df = pd.DataFrame(processed_data, columns=new_lines[0].split(','))
    # Extract the DM string from the file name
    dm_string = fire.split("DM")[-1].split("_")[0]
    dm_string1 = "DM" + dm_string
    df.insert(loc=2, column='DM', value=dm_string)
    df.insert(loc=3, column='DM1', value=dm_string1)
    df['DM'] = pd.to_numeric(df['DM'], errors='coerce')
    # Process Period and other values
    Period_1 = df['Period(ms)'].str.replace(r"\(.*\)", "", regex=True)
    df.insert(loc=8, column='Period_1', value=Period_1)

    pattern = r'\d+\.\d+x10\^\d+'
    mask = df['Period_1'].str.contains(pattern, regex=True)
    df.loc[mask, 'Period_1'] = df.loc[mask, 'Period_1'].apply(lambda x: float(re.sub(r'x10\^', 'e', x)))
    df.insert(loc=9, column='Period_2', value=df['Period_1'].astype(float).apply(
        lambda x: float(str(x).split('.')[0] + '.' + str(x).split('.')[1][:Period_digital]) if '.' in str(x) else x))
    # Remove duplicate rows based on 'Period_2' column, keeping the first occurrence
    df = df.drop_duplicates(subset="Period_2", keep='first')
    df['Period_1'] = pd.to_numeric(df['Period_1'], errors='coerce')
    df['Period_2'] = pd.to_numeric(df['Period_2'], errors='coerce')
    df['Sigma'] = pd.to_numeric(df['Sigma'], errors='coerce')
    # Update the global counter and print progress
    with lock:
        counter.value += 1
        print(f"\rRead {counter.value} of {len(candfiles)} files", end='', flush=True)

    return df

# ----------- Parallel Process Execution ----------- 
# Start multiprocessing pool to process files in parallel
if __name__ == '__main__':
    with Pool(processes=Num_processes) as pool:
        results = pool.map(process_candidate_file, candfiles)

    # Concatenate the processed data into a final DataFrame
    DF = pd.concat(results, ignore_index=False)
    # Save the final result to CSV files
    DF.to_csv("./PCSSP/All_Candidate.csv", sep=',', index=0, header=1)
    DF_ = DF.drop_duplicates(subset="Period_2", keep='first')
    DF_.to_csv("./PCSSP/One_Candidate.csv", sep=',', index=0, header=1)
    print("\nCandidate extraction completed.")

##
candidate_p = list(DF_["Period_2"])

def process_candidate(i):
    # Setting of candidate conditions!
    if ( len(DF[DF["Period_2"] == candidate_p[i]].Period_2) >= period_num_min ) \
    and ( (max(DF[DF["Period_2"] == candidate_p[i]].DM) - min(DF[DF["Period_2"] == candidate_p[i]].DM))  <= DM_range )\
    and ( candidate_p[i] >= Min_period )\
    and ( candidate_p[i] <= Max_period )\
    and ( max(DF[DF["Period_2"] == candidate_p[i]].Sigma)  >= sigma_min )\
    and ( max(DF[DF["Period_2"] == candidate_p[i]].Sigma)  <= sigma_max ):
        return (candidate_p[i], True)
    else:
        return (candidate_p[i], False)

with Pool(processes=Num_processes) as pool:
    results = pool.map(process_candidate, range(len(candidate_p)))

CAND = [p for p, is_cand in results if is_cand]
Non_CAND = [p for p, is_cand in results if not is_cand]
###
def extract_best_row(i):
    candidate_ = DF[DF["Period_2"] == CAND[i]]
    AAA = list(candidate_["Sigma"])
    AA = [j for j in range(len(candidate_)) if AAA[j] == max(candidate_["Sigma"])]
    
    idx = AA[0] 
    return (
        str(list(candidate_["Period_2"])[0]),
        str(list(candidate_["DM1"])[idx]),
        str(list(candidate_["Sigma"])[idx]),
        str(list(candidate_["Cand"])[idx]),
        str(list(candidate_["NumHarm"])[idx]),
        str(list(candidate_["Accel(m/s^2)"])[idx])
    )

with Pool(processes=Num_processes) as pool:
    results = pool.map(extract_best_row, range(len(CAND)))

pp, dmdm, sigma, Cand, NumHarm, Accel = map(list, zip(*results))
##
c ={"CAND":Cand,
   "DM":dmdm,
   "p":pp,
   "Sigma":sigma,
   "NumHarm":NumHarm,
   "Accel":Accel}
best_cand = pd.DataFrame(c)
best_cand.to_csv("./PCSSP/best_Candidate.csv",sep=',',index=0,header=1)

dm = best_cand["DM"]
DM={"DM" : dm}
DM = pd.DataFrame(DM)
DM_T = DM.T
DM_T.to_csv('./PCSSP/'+str(len(CAND)) +'-ACCEL-DM.txt',sep=' ',index=0,header=0)

cand = best_cand["CAND"]
accelcand = {"accelcand" : cand}
accelcand = pd.DataFrame(accelcand)
accelcand_T = accelcand.T
accelcand_T.to_csv('./PCSSP/'+str(len(CAND)) +'-ACCEL-accelcand.txt',sep=' ',index=0,header=0)

pms = best_cand["p"]
Pms = {"Pms" : pms}
Pms = pd.DataFrame(Pms)
Pms_T = Pms.T
Pms_T.to_csv('./PCSSP/'+str(len(CAND)) +'-ACCEL-Pms.txt',sep=' ',index=0,header=0)
print("Candidate numbers:",len(CAND))
print("Ploting")
##
sample_file = candfiles[0]
firelist = sample_file.split('_')
if args.JERK is None:
    zmax = firelist[-1]
else:
    zmax = firelist[-3]
    wmax = firelist[-1]
##
###  DM - Sigma relation figure
def generate_plot(i):
    candidate_ = DF[DF["Period_2"] == CAND[i]]
    AA = []
    for j in range(len(candidate_)):
        AAA = list(candidate_.Sigma)
        if AAA[j] == max(candidate_["Sigma"]):
            AA.append(j)

    fig,ax = plt.subplots(1,1,figsize=(10, 3))
    d = {'DM': candidate_["DM"], 'Sigma': candidate_["Sigma"], 'P':candidate_["Period_1"]}
    df = pd.DataFrame(data=d)
    df = df.sort_values(by='DM', ascending=True)
    # Create scatter plot
    ax0 = ax.scatter(df['DM'], df['Sigma'], c=df['P'], cmap='Greys')
    # Add circles to scatter plot
    ax.scatter(df['DM'], df['Sigma'], marker='o', facecolors='none', edgecolors='#000000', s=50,linewidths=1.5)
    # Add line to scatter plot
    ax.plot(df['DM'], df['Sigma'], color="#791E94")
    num_decimals = 8
    format_str = f'%.{num_decimals}f'
    ax.axvline(list(candidate_["DM"])[AA[0]],c="#791E94",linestyle='--', linewidth=2, label="DM / sigma: " + str(list(candidate_["DM"])[AA[0]]) +" / "+ str(list(candidate_["Sigma"])[AA[0]]))
    ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], s=30, c="red",alpha=0.0, marker='s', label = "period: " + str(list(candidate_["Period(ms)"])[AA[0]])+ " ms")
    if args.JERK is None:
        ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], c="red",alpha=0.0, label = "zmax: " + zmax+"; "+"candnum"+": " +str(list(candidate_["Cand"])[AA[0]]))
        ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], c="red",alpha=0.0, label = "accel: " + str(list(candidate_["Accel(m/s^2)"])[AA[0]])+ " m/s^2")
        ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], c="red",alpha=0.0, label = "harm: " + str(list(candidate_["NumHarm"])[AA[0]])+"; "+"FFT'z'"+": " +str(list(candidate_['FFTz(bins)'])[AA[0]]))
    else:
        ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], c="red",alpha=0.0, label = "z / w: " + zmax+ " / " + wmax +"; "+"cand"+": "+ str(list(candidate_["Cand"])[AA[0]]))
        ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], c="red",alpha=0.0, label = "harm: " + str(list(candidate_["NumHarm"])[AA[0]]) +"; " + "a: " + str(list(candidate_["Accel(m/s^2)"])[AA[0]])+ " m/s^2")
        ax.scatter(list(candidate_["DM"])[AA[0]],list(candidate_["Sigma"])[AA[0]], c="red",alpha=0.0, label = "'z' / 'w'"+": " +str(list(candidate_['FFTz(bins)'])[AA[0]]) + " / " +  str(list(candidate_['FFTw(bins)'])[AA[0]]))
    ax.set_xlabel("Trial DM" +" (cm$^{-3}$ pc)", fontsize=9)
    ax.set_ylabel("Sigma",fontsize=9)
    ax.tick_params(direction="in")
    ax.tick_params(axis='y', rotation=90)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    ax.legend(fontsize=9)
    # Set colorbar limits to data limits
    cbar = fig.colorbar(ax0, ax=ax, format=format_str, label="Period (ms)",pad = 0.01, fraction=0.035)  
    vmin = df['P'].min()
    vmax = df['P'].max()
    cbar.set_ticks([vmin, vmax])
    cbar.set_label(label="Period (ms)", size=9)
    df1 = df.drop_duplicates(subset="P",keep='first')      
    num_ticks = 5
    cbar.ax.yaxis.set_major_locator(ticker.MaxNLocator(num_ticks))
    plt.savefig("./PCSSP/DmSigmaFig/" +str(list(candidate_["DM1"])[AA[0]]) + "_" +"Cand"+"_" +str(list(candidate_["Cand"])[AA[0]])  +".png",bbox_inches="tight", dpi=200 )
    plt.cla()
    plt.clf()
    plt.close("all")

if __name__ == '__main__':
    # Define the number of processes to use
    num_processes = Num_processes
    # Create a pool of processes
    pool = Pool(processes=num_processes)
    # Define the range of iterations
    iterations = range(len(CAND))
    # Run the function in parallel
    pool.map(generate_plot, iterations)
    # Close the pool
    pool.close()
    pool.join()

print("OK!")
