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
