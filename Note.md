## A personal note

### data reduction
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

# 6517
prepsubband -nobary -nsub 128 -subdm 182.50 -sub -mask ../NGC6517_20200123_rfifind.mask -o NGC6517_20200123 ""${File_Path}""/*.fits
prepsubband -nobary -nsub 128 -subdm 182.50 -sub -mask ../*.mask -o NGC6517_20200120 ${a}
prepfold -nosearch -noxwin -topo -dm 182.00 -n 256 -npart 256  -accelcand 6 -accelfile NGC6517_20191017_DM182.00_ACCEL_0.cand ./subbands/NGC6517_20191017_DM182.00.sub???

```
### parfile raw data folding for many pulsar
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
### pulsar timing 
```
#parfile parameters of tempo2
PSRJ           J1801-0857A
RAJ             18:01:50.6080582         1  0.00010858853095316626   
DECJ           -08:57:31.90352           1  0.00526733498607433405   
F0             139.36088639769068735     1  0.00000000003156006786   
F1             9.8998320889143702294e-15 1  7.2487936211934637038e-19
PEPOCH         58871.058813851150013       
POSEPOCH       58871.058843851150478       
DMEPOCH        58871.05857                 
DM             182.56000849188692717       
START          58659.688811835754496       
FINISH         59944.222690395683543      
                                                               
TZRMJD         59105.512449299703981     #The TZRMJD, TZRFRQ, and TZRSITE paramaters define phase 0.0 for the ephemeris.                                                           
TZRFRQ         1000                      #Often, but NOT always, the fiducial point on the radio profile is the peak,
TZRSITE        fast                      # but you must always ask the person who made the ephemeris to be sure, because other conventions are used!
                                         # The fiducial point on the radio profile arrived at TZRSITE at frequency TZRFRQ at the moment TZRMJD. 


TRES           24.395                    #Rms timing residual    

EPHVER         5                         #(pam -h)--ephver ver     Ephem type for -E, 'ver' should be 'tempo' or 'tempo2' ;   
                                         #* WARNING: If your PAR file comes from Tempo2 (usually you can tell by "EPHVER 5" in the file), then the default time system is TCB, NOT TDB!
                                         # Tempo2 only uses TDB if there is "UNITS TDB" in the par file.       
          
NE_SW          10                        #The electron density at 1AU due to the solar wind  

CLK            TT(TAI)                   #Terrestrial Time (TT) and International Atomic Time (TAI)?
                                         # note: the tempo1 software switches off clock corrections in predictive mode. 
                                         #To emulate this the CLK flag in the parameter file should be set to CLK UNCORR.

MODE 1                                   # Fitting with errors MODE 1, or without MODE 0     
                             
UNITS          TCB                       # TDB - Barycentric Dynamic Time,  Barycentric Coordinate Time (TCB);

TIMEEPH        IF99                      # Which time ephemeris to use (IF99/FB90)

DILATEFREQ     Y                         # Whether or not to apply gravitational redshift and time dilation to observing frequency (Y/N)

PLANET_SHAPIRO Y                         #In pulsar timing, massive bodies within the solar system cause a Shapiro delay for observed pulses. 

T2CMETHOD      IAU2000B                  # Method for transforming from terrestrial to celestial frame (IAU2000B/TEMPO)

CORRECT_TROPOSPHERE  Y                   #Whether or not to apply tropospheric delay corrections. 
                                         #Troposphere is the atmospheric layer placed between earth's surface and an altitude of about 60 kilometres.

EPHEM          DE200                     #Which solar system ephemeris to use，  DE200， DE405 , DE438, DE440；
                                         #In order to correct the arrival time to the solar system's barycentre, tempo2 requires a solar system
                                         #ephemeris. By default the JPL ephemeris DE200 is chosen.

NITS           1                         #Number of iterations for the fitting routines

NTOA           151
CHI2R          1.6525 146

###---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Some code examples, pulsar timing
1. psrchive 
pam -FTp --setnsub 8 -e FTp *.pfd (*.ar = DSPSR, prepfold = *.pfd)
paas -iD standard.FTp 
First click   --> center of the gaussian component; Second click  --> halfwidth of the gaussian component; Third click   --> height of the gaussian component; THEN press "F" to FIT!!!!, q is just for quit and save!
pat -s paas.std -f tempo2 *.FTp  >  J.tim
pat -s paas.std *.FTp  -f "tempo2 i" > J.tim

2. tempo2
tempo2 -gr transform tempo1_style.par tempo2_style.par 
tempo2 -gr plk -f J.par J.tim 
  
3.presto and tmepo
  
# ls *.dat | xargs -n 1 --replace prepfold -noxwin -nosearch -topo -n 64 -npart 128 -par *.par {}
# parallel -j 20 'prepfold -noxwin -nosearch -topo -n 64 -npart 128 -par *.par {}' ::: *.dat &

#pfd_for_timing.py *.pfd
(True is OK!)

#pygaussfit.py name_standard.pfd.bestprof    
(name_standard.gaussians)

#for i in *.pfd; do get_TOAs.py -n 8 -g name_standard.gaussians ""${i}""; done
#for i in *.pfd; do get_TOAs.py -n 4 -s 4 -g name_standard.gaussians ""${i}""; done
#for i in *.pfd; do get_TOAs.py -n 4 -s 4 -2 -g name_standard.gaussians ""${i}""; done  #(-2, tempo2 format or style!)
(source_name.tim)

#tempo2 -gr transform tempo1_style.par tempo2_style.par #(from tempo1 to temop2 style)
#tempo source_name.tim -f source_name.par; pyplotres.py

## ---
1. psrchive 
pam -FTp --setnsub 8 -e FTp *.pfd (*.ar = DSPSR, prepfold = *.pfd)
paas -iD standard.FTp 
First click   --> center of the gaussian component; Second click  --> halfwidth of the gaussian component; Third click   --> height of the gaussian component; THEN press "F" to FIT!!!!, q is just for quit and save!
pat -s paas.std -f tempo2 *.FTp  >  J.tim
pat -s paas.std *.FTp  -f "tempo2 i" > J.tim

2. tempo2
tempo2 -gr transform tempo1.par tempo2.par 
tempo2 -gr plk -f J.par J.tim 
```



### docker
```
@ Yujie Chen
*************************************************服务器配置*****************************************************************************************
# centos and ubuntu ( under the root)
[root@localhost chenyujie]# apt install podman  # ubuntu
[root@localhost chenyujie]# yum install podman  # centos

# buildah pull the images ( under the root)
podman pull registry.cn-hangzhou.aliyuncs.com/pulsars/ubuntu22.04:v8.28  # created in 2025.8.28, include presto5.1, dspsr, psrchive et al.

****************************************************************************************************************************************************
# Verify the images exist ( use sudo!)
[chenyujie@localhost cyj]$ sudo podman images
REPOSITORY                                              TAG     IMAGE ID       CREATED        SIZE
registry.cn-hangzhou.aliyuncs.com/pulsars/ubuntu22.04   v8.28   026e8dc2e432   45 hours ago   16.9 GB

# created the container by the images (use sudo!)
[chenyujie@localhost cyj]$ sudo podman run -it -v /home/data:/home/data --privileged --name pulsars 026e8dc2e432
sudo podman run -it -v /home/data:/home/data -v /home/data22:/home/data22 --privileged --name pulsars_tjf 026e8dc2e432


# mount the catalogue and enter the container (use sudo!)
[chenyujie@localhost cyj]$ sudo podman exec -it -u chenyujie pulsars /bin/bash
```
