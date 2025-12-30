#!/bin/bash
# Multiple Observations Segment Search && search_split 
# @Dejiang Yin, dj.yin@foxmail.com, 20251230
#****************************************************
#-----------------------------------------------------

#-----------------------------------------------------
# The observation containing the different dates, as following
obs_dates=(20201217 20201218 20201219)
# The path of your fits data for one source, as following:
file_Path=/data/demo
# The path for you to save the searching results, as following:
output_Dir=/data/moss
# The name of your observation source name, as follow:
Source_name=demo
#-----------------------------------------------------
# The path for sifting code, as followiing:
PCSSP_sift=/data/code/ACCEL_sift_drifting.bash 
pm_split_datfile=/data/code/pm_split_datfile.py
#-----------------------------------------------------
# Setting for ls *. | xargs -n1 -P{} -I{} ... # ""${P}"",-P, --max-procs=MAX-PROCS  Run up to max-procs processes at a time.
P=100
#-----------------------------------------------------
# The number of fits file for each segment searching of each observation.
files_per_segment=10
# The number of overlapping files between segments
overlap_files=0
#----------------------------------------------------
# dat-level split setting (pm_split_datfile)
Nsplit=2              # e.g. 2, 4, 8, 12 ...
ck_prefix=chunk          # pm_split_datfile fixed naming: ckunkXofN
# padding width for ck index (pm_split_datfile behavior)
# Nsplit < 10  -> ck1of8
# Nsplit >=10  -> ck01of12
pad_width=1
if [ "${Nsplit}" -ge 10 ] && [ "${Nsplit}" -le 99 ]; then
    pad_width=2
fi
#-----------------------------------------------------
#-----------------------------------------------------
# Setting for prepsubbad -nsub {} -lodm {} -dmstep {} -numdms {} -downsamp {}
nsub=1024
lodm=30
dmstep=0.2
numdms=10
downsamp=1
#-----------------------------------------------------
# Setting for accelsearch -zmax {} -numharm {} -sigma {}
zmax=20
numharm=16
sigma=2.0
#-----------------------------------------------------
# The command setting for the searching routines,
rfifind="rfifind -time 2.0"
prepsubband="prepsubband -nobary -nsub ${nsub} -lodm ${lodm} -dmstep ${dmstep} -numdms ${numdms} -downsamp ${downsamp}"
realfft="realfft -fwd "
accelsearch="accelsearch -zmax ${zmax} -numharm ${numharm} -sigma ${sigma} "
#-----------------------------------------------------

#-----------------------------------------------------
# Define function to process fits files in segments for multiple observations segment search
multiple_obs_segment_search() {
    File_Path="${file_Path}/${1}"
    mkdir -p "${output_Dir}/${1}"
    Output_Dir="${output_Dir}/${1}"
    Obs_data=${1}
    # Get the list of fits files in the specified directory  
    fits_files=($(ls "${File_Path}"/*.fits))                                                                                                                                                         
    # Calculate the number of segments based on the number of fits files                                                                                            
    total_files=${#fits_files[@]}                                                                                                                                                                
    total_segments=$(((total_files - overlap_files) / (files_per_segment - overlap_files)))                                                                                               
    if [ $(((total_files - overlap_files) % (files_per_segment - overlap_files))) -ne 0 ]; then                                                                                                
        total_segments=$((total_segments + 1))                                                                                                                      
    fi                                                                                                                                             

    #-----------------------------------------------------
    # Define function to process fits files in segments for "rfifind"                                                                                               
    rfifind_segment() {                                                                                                                                             
        segment_number=$1          
        start_index=$((segment_number * (files_per_segment - overlap_files)))                                                                                                                                 
        end_index=$((start_index + files_per_segment - 1))                                                                                                          
        if [ $end_index -ge $total_files ]; then                                                                                                                    
            end_index=$((total_files - 1))                                                                                                            
        fi                                                                                                                                                          
        # Create a directory for the segment if it doesn't exist                                                                                                    
        segment_dir="${Output_Dir}/segment_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"                                                
        mkdir -p "$segment_dir"                                                                                                                                     
        # Generate rfifind command with modified output name and directory                                                                                          
        output_name="${Source_name}_${Obs_data}_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"                                                                      
        echo "cd ${segment_dir} && ${rfifind} -o ${output_name} \$(ls ${File_Path}/*.fits | tail -n +$((start_index + 1)) | head -n $((end_index - start_index + 1))) > ${segment_dir}/${output_name}_rfifind.log"
	echo "\$(ls ${File_Path}/*.fits | tail -n +$((start_index + 1)) | head -n $((end_index - start_index + 1)))" > "${segment_dir}/${output_name}.FileList"
    } 
    #----------------------------------------------------- 
    # Define function to process fits files in segments for "prepsubband"  
    prepsubband_segment() {          
        segment_number=$1
        start_index=$((segment_number * (files_per_segment - overlap_files)))
        end_index=$((start_index + files_per_segment - 1))
        if [ $end_index -ge $total_files ]; then
            end_index=$((total_files - 1))
        fi
        # Create a directory for the segment if it doesn't exist                                                                                                    
        segment_dir="${Output_Dir}/segment_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
        # Generate rfifind command with modified output name and directory                                                                                          
        output_name="${Source_name}_${Obs_data}_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
        echo "cd ${segment_dir} && ${prepsubband} -o ${output_name} -mask ${output_name}_rfifind.mask \$(ls ${File_Path}/*.fits | tail -n +$((start_index + 1)) | head -n $((end_index - start_index + 1))) > ${segment_dir}/${output_name}_prepsubband.log"                                                                                                                                                                        
    }
    #-----------------------------------------------------
    # Define function to split .dat into chunks using pm_split_datfile
    pm_split_datfile_segment() {
        segment_number=$1
        start_index=$((segment_number * (files_per_segment - overlap_files)))
        end_index=$((start_index + files_per_segment - 1))
        if [ $end_index -ge $total_files ]; then
            end_index=$((total_files - 1))
        fi

        segment_dir="${Output_Dir}/segment_s$((${segment_number}+1))_$((${start_index}+1))-$((${end_index}+1))"
        output_name="${Source_name}_${Obs_data}_s$((${segment_number}+1))_$((${start_index}+1))-$((${end_index}+1))"

        # split into Nsplit chunks (ck1of8, ck2of8, ...)
        echo "cd ${segment_dir} && python3 ${pm_split_datfile} -dat \"${output_name}*.dat\" -n ${Nsplit} > ${segment_dir}/${output_name}_pm_split_datfile.log"
    }

    #-----------------------------------------------------
    # Define function to organize split outputs into folders
    organize_ck_segment() {
        segment_number=$1
        start_index=$((segment_number * (files_per_segment - overlap_files)))
        end_index=$((start_index + files_per_segment - 1))
        if [ $end_index -ge $total_files ]; then
            end_index=$((total_files - 1))
        fi

        segment_dir="${Output_Dir}/segment_s$((${segment_number}+1))_$((${start_index}+1))-$((${end_index}+1))"

        # create dat_split_01..dat_split_08 and move ckXof8.* into them
        echo "cd ${segment_dir} && for i in \$(seq 1 ${Nsplit}); do \
        idx=\$(printf \"%0${pad_width}d\" \$i); mkdir -p ${ck_prefix}\${idx}of${Nsplit}; done"
        # move files (ck1of8.* etc.)
	echo "cd ${segment_dir} && for i in \$(seq 1 ${Nsplit}); do \
        idx=\$(printf \"%0${pad_width}d\" \$i); find . -maxdepth 1 -type f -name \"*_ck\${idx}of${Nsplit}.*\" -exec mv {} chunk\${idx}of${Nsplit}/ ';' ; done"
    }

    #-----------------------------------------------------                                      
    # Define function to process fits files in segments for "realfft"                                                                                       
    realfft_segment() {                                                                                                                                     
        segment_number=$1
        start_index=$((segment_number * (files_per_segment - overlap_files)))
        end_index=$((start_index + files_per_segment - 1))
        if [ $end_index -ge $total_files ]; then
            end_index=$((total_files - 1))
        fi
        # Create a directory for the segment if it doesn't exist                                                                                                    
        segment_dir="${Output_Dir}/segment_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
        # Generate rfifind command with modified output name and directory                                                                                          
        output_name="${Source_name}_${Obs_data}_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"  
	echo "cd ${segment_dir} && find ${ck_prefix}*of${Nsplit} -maxdepth 1 -name \"*.dat\" | sort -V | xargs -n1 -I{} echo \"cd ${segment_dir} && ${realfft} \$(basename {})\" >> ${segment_dir}/${output_name}_realfft.txt"
    }  
    #*****************************************************                                            
    #-----------------------------------------------------
    # Define function to process fits files in segments for "accelsearch"                                                                                                            
    accelsearch_segment() {                                                                                                                                                          
        segment_number=$1
        start_index=$((segment_number * (files_per_segment - overlap_files)))
        end_index=$((start_index + files_per_segment - 1))
        if [ $end_index -ge $total_files ]; then
            end_index=$((total_files - 1))
        fi
        # Create a directory for the segment if it doesn't exist                                                                                                    
        segment_dir="${Output_Dir}/segment_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
        # Generate rfifind command with modified output name and directory                                                                                          
        output_name="${Source_name}_${Obs_data}_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
	echo "cd ${segment_dir} && find ${ck_prefix}*of${Nsplit} -maxdepth 1 -name \"*.fft\" | sort -V | xargs -n1 -I{} echo \"cd ${segment_dir}  && ${accelsearch} \$(basename {})\" >> ${segment_dir}/${output_name}_accelsearch.txt"
    }                                                                                                                                                                                
    #*****************************************************                                            
    #-----------------------------------------------------
    # Define function to process fits files in segments for "sifting"                                                     
    sifting_segment() {                                                                                                   
        segment_number=$1
        start_index=$((segment_number * (files_per_segment - overlap_files)))
        end_index=$((start_index + files_per_segment - 1))
        if [ $end_index -ge $total_files ]; then
            end_index=$((total_files - 1))
        fi
        # Create a directory for the segment if it doesn't exist                                                                                                    
        segment_dir="${Output_Dir}/segment_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
        # Generate rfifind command with modified output name and directory                                                                                          
        output_name="${Source_name}_${Obs_data}_s$((${segment_number} + 1))_$((${start_index} + 1))-$((${end_index} + 1))"
        # echo "cd ${segment_dir} && bash ${PCSSP_sift} "   
	# echo "cd ${segment_dir} && find . -maxdepth 1 -type d -name \"chunk*of${Nsplit}\" | sort -V | xargs -I{} echo \"cd ${segment_dir}/{} && bash ${PCSSP_sift}\""
	for ((ck=1; ck<=Nsplit; ck++)); do
            printf "cd %s/chunk%sof%s && bash %s\n" "${segment_dir}" "${ck}" "${Nsplit}" "${PCSSP_sift}"
        done
    }                                                                                                                     
    #*****************************************************                                            
    #-----------------------------------------------------
    # porferming above defined functions
    #-----------------------------------------------------
    # Process fits files in segments                               
    # rfifind
    for ((i = 0; i < total_segments; i++)); do                     
        rfifind_segment $i >> ${Output_Dir}/rfifind_segment.txt                  
    done                                                           
    # prepsubband
    for ((i = 0; i < total_segments; i++)); do                               
        prepsubband_segment $i >> ${Output_Dir}/prepsubband_segment.txt  	
    done 
    # pm_split_datfile
    for ((i = 0; i < total_segments; i++)); do
        pm_split_datfile_segment $i >> ${Output_Dir}/pm_split_datfile_segment.txt
    done
    # organize ck directories
    for ((i = 0; i < total_segments; i++)); do
        organize_ck_segment $i >> ${Output_Dir}/organize_ck_segment.txt
    done
    # realfft 
    for ((i = 0; i < total_segments; i++)); do           
        realfft_segment $i >> ${Output_Dir}/realfft_segment.txt
    done                                                 
    # accelsearch
    for ((i = 0; i < total_segments; i++)); do                       
        accelsearch_segment $i >> ${Output_Dir}/accelsearch_segment.txt             
    done                                                             
    # sifting
    for ((i = 0; i < total_segments; i++)); do                    
        sifting_segment $i >> ${Output_Dir}/sifting_segment.txt                  
    done  
    #*****************************************************                                            
    #-----------------------------------------------------
    # Others
    # remove the command.txt to segment_command           
    mkdir -p ${Output_Dir}/segment_command                  
    mv ${Output_Dir}/*_segment.txt ${Output_Dir}/segment_command       
    ##-----------------------------------------------------
}

#*****************************************************                                            
#-----------------------------------------------------
# The all observations to search for psulsar with segment search, as following
#-----------------------------------------------------
#***************************************************** 

for obs_date in "${obs_dates[@]}"; do
    multiple_obs_segment_search $obs_date
done

#*****************************************************                                            
#-----------------------------------------------------
# Searching in "all" parallel with "xargs -n 1 -P {} -I {}"
#-----------------------------------------------------
#***************************************************** 
cd ${output_Dir}
mkdir -p ${output_Dir}/ss_commands
# rfifind 
ls -v ${output_Dir}/*/segment_command/rfifind_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_rfifind_commands.txt
cat ${output_Dir}/ss_commands/ss_rfifind_commands.txt | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""
# prepsubband
ls -v ${output_Dir}/*/segment_command/prepsubband_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_prepsubband_commands.txt
cat ${output_Dir}/ss_commands/ss_prepsubband_commands.txt | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""
# pm_split_datfile
ls -v ${output_Dir}/*/segment_command/pm_split_datfile_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_pm_split_commands.txt
# cat ${output_Dir}/ss_commands/ss_pm_split_commands.txt | xargs -n 1 -P "${P}" -I {} sh -c "{}"
# bash  ${output_Dir}/ss_commands/ss_pm_split_commands.txt
cat ${output_Dir}/ss_commands/ss_pm_split_commands.txt |  xargs -d '\n' -n 1 -P "${P}" sh -c 'eval "$0"'

# organize ck directories
ls -v ${output_Dir}/*/segment_command/organize_ck_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_organize_ck_commands.txt
bash ${output_Dir}/ss_commands/ss_organize_ck_commands.txt
# realfft
ls -v ${output_Dir}/*/segment_command/realfft_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_realfft1_commands.txt
bash  ${output_Dir}/ss_commands/ss_realfft1_commands.txt
ls -v ${output_Dir}/*/segment_*/*_realfft.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_realfft2_commands.txt
cat ${output_Dir}/ss_commands/ss_realfft2_commands.txt | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""   
# accelsearch
ls -v ${output_Dir}/*/segment_command/accelsearch_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_accelsearch1_commands.txt
bash  ${output_Dir}/ss_commands/ss_accelsearch1_commands.txt
ls -v ${output_Dir}/*/segment_*/*_accelsearch.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_accelsearch2_commands.txt
cat ${output_Dir}/ss_commands/ss_accelsearch2_commands.txt | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""   
# remove .fft
# find ${output_Dir}/*/segment_* -maxdepth 1 -name "*_red.inf" | sort -V | xargs -n1 -I{} -P10 echo "{}" | while read i; do rm -rf "${i:0:-8}".dat "${i:0:-8}".inf "${i:0:-8}".fft; done
find ${output_Dir}/*/segment_* -maxdepth 1 -name "*_DM*.dat" | sort -V | xargs -n1 -P"${P}" -I{} rm -rf {}
find ${output_Dir}/*/segment_* -maxdepth 1 -name "*_DM*.inf" | sort -V | xargs -n1 -P"${P}" -I{} rm -rf {}
# sifiting and folding
ls -v ${output_Dir}/*/segment_command/sifting_segment.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_sifting_commands.txt
cat ${output_Dir}/ss_commands/ss_sifting_commands.txt | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""
## All fits folding
ls -v ${output_Dir}/*/segment_*/*c*of*/cands_cmd_prepfold.txt | xargs -n 1 -I {} cat {} >> ${output_Dir}/ss_commands/ss_prepfold_commands.txt
cat ${output_Dir}/ss_commands/ss_prepfold_commands.txt | xargs -n 1 -P ""${P}"" -I {} sh -c ""{}""
#-----------------------------------------------------
#***************************************************** 
#-----------------------------------------------------
#*****************************************************


