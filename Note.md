## A personal note

```
ls *.zst | xargs -n1 -P30 -I{} zstd --rm -d {}
ls *.xz | xargs -n1 -I{} -P50 xz -d  {}
```

```
docker ps -a
docker start ab2c65b5c89b
docker attach  ab2c65b5c89b
docker exec -it --user ydj ab2c65b5c89b /bin/bash
```

```
for ((i = 1; i <= 100; i++)); do echo $i ; done

files=$(ls /home/data/M92/20240101/*.fits | tail -n +210 | head -n 300)
prepfold -topo -nosearch -noxwin -n 64 -npart 128 -dm 35.30 -accelcand 87 -accelfile M92_20240101_DM35.30_ACCEL_10.cand  -o ./M92_20240101_DM35.30_ACCEL_10.cand-210-510fits ${files}
seq 1 1 1329 | xargs -n1 -P5 -I{} prepfold -nosearch -noxwin -topo -n 64 -accelcand {} -accelfile M15_20201221_DM66.95_red_ACCEL_600.cand M15_20201221_DM66.95_red.dat

find . -maxdepth 1 -name "*.fft" | sort -V
find . -maxdepth 1 -name "*_red.fft" | sort -V 
find ${Output_Dir}/segment_* -maxdepth 1 -name "*.fft" | sort -V | xargs -n1 -P"${P}" -I{} rm -rf {}

ls -v -d /home/data/ydj/ydj/M13/lwang/M13/search/*/segment_s*/ | xargs -n1 -I{} echo "cd {} && ls *.dat | xargs -n1 -P50 -I{} realfft {}" > realfft.txt
awk '/[0-9]:[0-9]/ {print $8"_DM"$2, $0}' cands.txt > Cands.txt

find ./20250529*/*s/ -maxdepth 1 -name "*dat" | sort -V | xargs -n1 -P100 -I{} echo "single_pulse_search.py -b -m 300 {}"  >> single_pulse_search.txt
ls -dv /root/sj-tmp/ydj/NGC6517_2025/*/*/bary_dat/ | xargs -n1 -I{} echo "cd {} && rffa -c /root/sj-tmp/ydj/SS+commands/FFA_pipeline_config_B.yml --log-timings  ./*DM*.inf "
```

```
#!/bin/bash

# Obs_data=(20250529 20250520 20250505 20250428 20250420 20250416 20250412)   #changs obs data
# File_path=/data31/DDT2024_11/NGC6517

# Obs_data=(20250126 20241126 20240926)   #changs obs data
# File_path=/data31/PT2024_0080/NGC6517

# Obs_data=(20240306 20240206 20240102 20230929)   #changs obs data
# File_path=/data31/PT2023_0012/NGC6517

# Obs_data=(20221231 20221228)   #changs obs data
# File_path=/data31/PT2022_0087/NGC6517

Obs_data=(20220430)   #changs obs data
File_path=/data31/PT2021_0105/NGC6517

Source_list=(A B C D E F G H I K L M N O P Q R S T U V)
# rm par_fitsfold.sh
for i in $(seq ${#Source_list[*]}); do
	for j in $(seq ${#Obs_data[*]}); do
		file_path=""${File_path}""/""${Obs_data[j-1]}""
		#echo "prepfold -nosearch -noxwin -topo -n 64 -npart 128 -nsub 128 -par J*""${Source_list[i-1]}""*.par -o ""${Obs_data[j-1]}""_""${Source_name}${Source_list[i-1]}""_fitsfold  -mask *""${Source_name}""*""${Obs_data[j-1]}""*.mask ""${File_Path}/*.fits""  "  >>  par_fitsfold.sh
                echo "prepfold -nosearch -noxwin -topo -n 64 -npart 128 -nsub 128 -par ./parfile-0/J1801-0857""${Source_list[i-1]}""*.par -o ""${Obs_data[j-1]}_NGC6517${Source_list[i-1]}"" ""${file_path}/NGC6517*M01*.fits""  "  >>  par_fitsfold.sh
	done
done

#cat par_fitsfold.sh | parallel -j 40 --halt soon,fail=1
#wait

```
