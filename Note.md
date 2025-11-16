## A personal note

### data reduction
```
ls *.zst | xargs -n1 -P30 -I{} zstd --rm -d {}
ls *.xz | xargs -n1 -I{} -P50 xz -d  {}
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
###-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
**pdmp:
psredit -c itrf:ant_x=-1668557.2070983793 -m J1801-0857B_1.par.ar.pazi
psredit -c itrf:ant_y=5506838.5266271923 -m J1801-0857B_1.par.ar.pazi
psredit -c itrf:ant_z=2744934.9655897617 -m J1801-0857B_1.par.ar.pazi
psredit -c coord=18:01:50.52-08:57.31.6 -m  J1801-0857B_1.par.ar.pazi

### 不修改坐标的结果如下：
[yindejiang@localhost search_bin]$ pdmp -dr 20 -ds 0.1 -pr 1000 -ps 1  -g J1801-0857B-c0.02896-DM170.ar.pazi1.ps/cps J1801-0857B-c0.02896-DM170.ar.pazi

ls -v  *.pazi| xargs -n1 -I{} echo "psredit -c itrf:ant_x=-1668557.2070983793 -m {} && psredit -c itrf:ant_y=5506838.5266271923 -m {} && psredit -c itrf:ant_z=2744934.9655897617 -m {} && psredit -c coord=17:13:49.5300+07:47:37.5000 -m {}" > psredit.txt
ls -v  *.pazi | xargs -n1 -I{} echo "pdmp -dr 500 -ds 0.1 -pr 10000 -ps 10 -ar 100 -as 1  -g {}.ps/cps {}" > pdmp.txt
ls *.ps | xargs -n1 -P10 -I{} convert -density 600 {} {}.jpg
ls *.ps | xargs -n1 -P20 -I{} convert -density 600 -rotate 90 {} {}.jpg**
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

###---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
###---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
1：脉冲星计时钟差文件说明
1、更新TEMPO、TEMPO2的钟差文件：
git clone https://github.com/ipta/pulsar-clock-corrections.git
上述命令下载后、替换本地对应的目录下的钟差文件（对应目录没有FAST的clk文件，直接加进去即可），这样的话就只需要在TEMPO，TEMPO2更新最新的time_fast.dat、fast2gps.clk即可。

2、FAST钟差文件下载地址：
https://github.com/NAOC-pulsar/FAST_ClockFile/tree/master
https://github.com/ipta

3、TEMPO钟差文件、需要将/tempo/clock/目录内、下述三个文件更新：
time.dat
time_fast.dat
ut1.dat
其中要在time.dat中添加 INCLUDE time_fast.dat 到该文件的末尾，方能成功调用。

4、TEMPO2的则是在/tempo2/T2runtime/clock/目录下更新，其他该目录下的文件也最好用最新的版本，这样，钟文件MJD可以覆盖TOA：
fast2gps.clk
ut1.dat
在TEMPO2里边更新FAST台站位置：/tempo2/T2runtime/observatory/observatories.dat
# FAST
#-1666460.00    5499910.00       2759950.00       FAST                fast
-1668557.0    5506838.0       2744934.0          FAST                fast
TEMPO内的FAST位置目前是对的。

5、下面是未作修改前的TEMPO2的钟文件警告
Warning #2: [CLK3] no clock corrections available for clock UTC(fast) for MJD 58397.3
TEMPO未作ut1.dat更新前的警告：
*** Warning - MJD = 59126 outside UT1 table range (41689-58894)
 *** Warning - Further UT1 messages suppressed
TEMPO未作钟差文件修正的警告：
 Clk corr error: TOA at 58454.19275 greater than last clk file entry for nsite  20
 *** Additional clock-correction messages suppressed. ***

6、TEMPO2:  CLK            TT(TAI) 
      TEMPO:  CLK                 TT(BIPM2021) / 
TEMPO的CLK选项
CLK     Terrestrial time standard  
        Allowed values: 'UNCORR' (default), 'UTC(NIST)', 'UTC(BIPM)', 
                       'TT(BIPM)', 'PTB', 'AT1'

7、TEMPO2其他修正：
[tempo2Util.C:397] [TROP2] Assume standard atmospheric pressure (no data) for site fast at MJD 58397.3
[tempo2Util.C:397] [TROP1] Assume zero zenith wet delay (no data) for site fast  at MJD 58397.3
L-band的影响可忽略。

20251104：
#tempo：如果上述问题都解决了，还是没有正确调用clk。那么检查钟差文件的格式，如小数点，参数列间隔的空格数<第1，2列需要7个空格，第二列三个小数点： 0.000>。

在vim time_fast.dat，使用``:%s/0.0/0.000/g’’全局替换
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

##-------------------------------------------------------------------------------------------------------------------------------------------------
Docker
Some things to try with docker
docker images (shows images that you’ve downloaded)
docker ps -a (shows all containers)
docker stop ipta (stop your container) 
docker rm ipta (remove your container) 
docker run -v /path/to/local/dir:/home/jovyan/work/data
docker run -it -v E:\Docker\data:/home/data -v E:\Docker\data1:/home/data1 -e DISPLAY=host.docker.internal:0.0 --name pulsar registry.cn-hangzhou.aliyuncs.com/pulsars/ubuntu22.04:latest
docker exec -it -u jovyan ipta /bin/bash
docker pull registry.cn-hangzhou.aliyuncs.com/pulsars/ubuntu22.04:latest
git clone https://github.com/ipta/ipta-2018-workshop
```
### polarization calibration
```
@ Tong Liu
0.准备工作

>>> psrcat -E [星名] > [命名].par
# 获得已知脉冲星的星历，在atnf查找星名

>>> readfile [.fits文件]
# 查看fits头文件 关注time per file

1.dspsr信号折叠

>>> dspsr -b 128 -L 60 -A -t 16 -E [.par文件] -O [输出名] [.fits文件]
# -c 用已知周期来折叠 没有par文件时使用
# -cont 输入fits文件为连续
# -K remove inter-channel dispersion delays
# -D 7.3 override dispersion measure 单脉冲使用
# -nsub 10 output archives with n integrations each

>>> pam -f 16 -e f16 [.ar文件]
# 把4096个通道数除以16
# 得到.f16文件
# 经过这一步之后再pazi

>>> psradd -e ar -o [输出名] [输入文件]
# 输入文件用空格隔开
# -e 改变扩展名 如果前一步没有f16则不需要

>>> pav -DFTp -g [M13A.png]/PNG [.ar文件]
# ar文件转png

>>> pazi [.ar文件]
# 交互式rfi处理
# 按u - undo

2.处理噪声

>>> dspsr -b 1024 -L 60 -A -t 16 -c 0.201326592 -O [输出名] [.fits文件]
# 折叠噪声文件
# -b 1024, 2048 给bin数量
# -c 0.100663296
# -t 16线程

>>> pav -DFTp -g [noise.png]/PNG [.ar文件]
# ar文件转png

>>> psredit -c type=PolnCal -m [噪声文件.ar]
# 修改头文件为偏振校准文件

>>> pam -f 16 -e f16 [.ar文件]
# 非必需 但有时候需要这一步再pazi

>>> pazi [.ar文件]
# 交互式rfi处理

>>> cp [噪声文件.ar] noise.mv
# 如果有pazi 则输入为pazi

3.其他图像查看

>>> psrzap [.ar文件]
# 查看折叠后图像 信息更多

>>> pacv [噪声文件.ar]
# 生成比较小的图像并查看 推荐
# 输出格式选/PS或/PNG都可
# 或者输入.pazi文件
# 如果不成功 执行前面psredit再试一下

4.偏振校准

>>> pac -U -n q -w -u [mv或pazi]
# -U关闭望远镜旋转修正
# -w生成database.txt 记录标准文件一些基本信息
# -q 把q的符号反过来 因为数据里写错了
# -u write to file extensions recognized in search

>>> pac -T -U -c -Z -n q -d database.txt -e ac [脉冲星文件.ar]
# 用标准文件修正脉冲星文件 开始校准
# -e extension added to output filenames
# -T take closest time
# -c take closest sky coordinates
# -Z do not try to match instruments 
# 生成acP文件

>>> pav -FTSC -g [M13A.png]/PNG [校准文件.acP]
# 生成新的图像文件 

5.其他

>>> paz -J paz.psh -e zap [M13A.ar] 
# 自动消干扰 需要已经折叠出ar
# -J -e固定参数 不太需要改
# paz.psh文件内容如下

#! /usr/bin/env psrsh

# zap 1000:1050
zap median window=24
zap median  cutoff=3
zap median exp={$all:max-$all:min}
zap median
zap mow robust
zap mow window=0.1
zap mow cutoff=4.0
zap mow

>>> pdmp -dr [185.65] -ds [0.05] -pr 0.00071756144 -b test [.ar文件]
# 在一个范围内折

叠最佳信号

psredit -c type=PolnCal -m J1402+13_20230514_off.zap

mv J1402+13_20230514_off.zap J1402+13_20230514_off.mv

pac -U -n q -w -u mv

pac -d database.txt -T -c -Z -U -n q J1402+13_20230514.zap 


$(ls /home/data/C1/20240929/*.fits | tail -n +1 | head -n 10)

C1 as an example!

# 0.100663296 for 0.1s noise, 1.00663296 for 1s noise 
# 0.201326592 for 0.2s noise, 2.01326592 for 2s nise

dspsr -b 256 -L 30 -A -t 16 -c 1.00663296 -O C1_noise $(ls /home/data/C1/20240929/*.fits | tail -n +1 | head -n 9)
dspsr -b 256 -L 30 -A -t 16 -E J2338+4818_best_1.par -O C1 $(ls /home/data/C1/20240929/*.fits | tail -n +1 | head -n 109)

psredit -c type=PolnCal -m C1_noise.ar
pazi C1.ar
pazi C1_noise.ar
# pacv C1_noise.ar
mv C1_noise.ar.pazi C1_noise.ar.pazi.cal
pac -U -n q -w -u cal
cat database.txt
pac -d database.txt -T -c -Z -U -n q C1.ar.pazi

pav -C -SFT --publnc -g C1.ps/cps C1.ar.calibP
pav -z 0.3,0.7 -C -SFT --publnc -g C1.ps/cps C1.ar.calibP

ls *.ps | xargs -n1 -P20 -I{} convert -density 600 -rotate 90 {} {}.jpg

RM拟合, 校准完后就能直接RM拟合了, 不过这个流程的拟合结果是星际介质的贡献加大气层的贡献值,ionFR,github就能找到,去除大气层贡献值
```
