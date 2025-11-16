#!/bin/bash
#-------------------------------
#- dj.yin at foxmail dot com   -
#- Dejiang Yin, 2024-12-30      -   
#-------------------------------
##
P=60  ## ""${P}"",-P, --max-procs=MAX-PROCS    Run up to max-procs processes at a time
zmax=_ACCEL_600
#zmax=_ACCEL_300_JERK_900

code_path=/home/data/ydj/M13/M13_DM29.45-30.75/siftcode

python_1=""${code_path}""/PCSSP_sift.py
python_2=""${code_path}""/combine_plots.py
python_3=""${code_path}""/second_sifting.py

python ""${python_1}"" -ACCEL 600 -minP 2.3 -maxP 10.8 -rDM 4 -minS 6 -maxS 50 -cpu ${P}
#python ""${python_1}"" -ACCEL 300 -JERK 900 -minP 2.3 -maxP 10.8 -rDM 4 -minS 6 -maxS 50 -cpu ${P}
##
dm=`cat ./PCSSP/*ACCEL-DM.txt`
cand=`cat ./PCSSP/*ACCEL-accelcand.txt`
Pms=($(awk '{ for(i=1; i<=NF; i++) printf "%.4f ", $i; printf "\n" }' ./PCSSP/*ACCEL-Pms.txt))
DM=($dm)
Cand=($cand)
# presto prepfold for .dat files
rm -rf commands_1.sh
rm -rf commands_2.sh
##
for i in $(seq ${#Cand[*]}); do
    datfile=`ls ""*${DM[i-1]}*.dat""`;
    # echo "prepfold -noxwin -nosearch -n 64 -npart 128 -accelcand ""${Cand[i-1]}"" -accelfile ""*${DM[i-1]}*.cand"" -o Pms""${Pms[i-1]}""_${datfile} ${datfile} " >> commands_1.sh
    # echo "prepfold -noxwin -nosearch -n 64 -npart 128 -accelcand ""${Cand[i-1]}"" -accelfile ""*${DM[i-1]}*.cand"" -o PCSSP_Pms""${Pms[i-1]}""_${datfile} ${datfile} " >> commands_1.sh
    echo "prepfold -noxwin -nosearch -n 64 -npart 128 -accelcand ""${Cand[i-1]}"" -accelfile ""*${DM[i-1]}*${zmax}.cand"" -o Pms""${Pms[i-1]}""_${datfile} ${datfile} " >> commands_1.sh
done
##
cat commands_1.sh | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""
wait
# merge .dat plot and dm-sigma plot
for i in $(seq ${#Cand[*]}); do Fig1=`ls *""${DM[i-1]}""*_Cand_""${Cand[i-1]}"".pfd.png`;  Fig2=`ls ./PCSSP/DmSigmaFig/${DM[i-1]}_Cand_${Cand[i-1]}.png` ; echo "python ""${python_2}"" ""${Fig1}"" ""${Fig2}"" -output ""${Fig1}"" " >> commands_2.sh
done
##
cat commands_2.sh | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""
wait
# mv files
mv commands* ./PCSSP/
mv *.png ./PCSSP/PCSSP_fig
mv *.pfd.bestprof ./PCSSP/PCSSP_fig
rm -rf *.pfd
rm -rf *.pfd.ps
cd ./PCSSP/PCSSP_fig
##
python ""${python_3}""
##
echo ""The numbers of candidate: ${#Cand[*]}""
date
