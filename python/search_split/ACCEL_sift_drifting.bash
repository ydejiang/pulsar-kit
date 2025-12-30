#!/bin/bash
#-------------------------------
#- dj.yin at foxmail dot com   -
#- Dejiang Yin, 2025-12-30     -   
#-------------------------------
##
# Path to Python scripts
ACCEL_sift_pulsarx=/data/20251216/LSI/code/ACCEL_sift_drifting.py
# Only accel:
python ""${ACCEL_sift_pulsarx}"" -ACCEL 20 -minP 1 -maxP 2800000 -minS 1 2> cands_cmd.txt
# For jerk search:
#python ""${ACCEL_sift_pulsarx}"" -ACCEL 300 -JERK 900 -minP 2. -maxP 10.8 -minS 6 2> pulsarX_cands.List

# For folding
MASK_FILE=$(ls ../*.mask)
FILELIST_TEXT=$(cat ../*.FileList)
CURDIR=$(pwd)

while IFS= read -r line; do
	#printf '%s %s\n' "$line" "$FILELIST_TEXT"
	#printf '%s -mask %s %s\n' "$line" "$MASK_FILE" "$FILELIST_TEXT"
	printf 'cd %s && %s -mask %s %s\n' "$CURDIR" "$line" "$MASK_FILE" "$FILELIST_TEXT"
done < cands_cmd.txt > cands_cmd_prepfold.txt

