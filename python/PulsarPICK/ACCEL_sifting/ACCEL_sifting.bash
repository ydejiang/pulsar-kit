#!/bin/bash
#-------------------------------
#- dj.yin at foxmail dot com   -
#- Dejiang Yin, 2026-01-04      -
#-------------------------------

# Number of parallel processes for xargs (default 45)
P=45
# Path to Python scripts
code_path=/home/data/code

# Define Python script paths
python_1="${code_path}/ACCEL_sifting.py"
export py_combine_plots="${code_path}/combine_plots.py"
# Run the first-stage sifting pipeline (disabled by default)
python ""${python_1}"" -ACCEL 10 -minP 0.5 -maxP 2000000.8 -minS 1 -nproc ${P}  2> ./prepfold_combine_cmd.txt
# For jerk search:
#python ""${python_1}"" -ACCEL 10 -JERK 40 -minP 0.5 -maxP 2000000.8 -minS 1 -nproc ${P}  2> ./prepfold_combine_cmd.txt

cat ./prepfold_combine_cmd.txt | xargs -P "${P}" -I {} sh -c "{}"

# Move result files to final folders (robust to large number of files)
mv ./prepfold_combine_cmd.txt ./zmax_sifting/
#find . -maxdepth 1 -name "*.pfd*" -exec mv -t ./zmax_sifting/logs/ {} +
find . -maxdepth 1 -name "*.pfd*" -type f -delete
rm -rf ./zmax_sifting/DM_sigma_plots/

# Print summary
echo "[INFO] All steps completed."
date
