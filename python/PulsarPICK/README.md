# PCSSP_sift
PCSSP_sift is the short for Pulsar Candidate Sifting and Synthesis Pipeline. This scripts are designed for the ”accelsearch“ results files from PulsaR Exploration and Search TOolkit (PRESTO,  a large suite of pulsar search and analysis software).

These scripts are written based on python and shell！

---

You just need to copy PCSSP_sift.py and PCSP _ sift.sh to your directory of "\*ACCEL\*0" files from accelsearch search of PRESTO and run PCSSP_sift.sh!

That is, on your terminal:

sh PCSSP_sift.sh

---

Before you run these scripts directly to generate the diagnosis plots of pulsar candidates, you'd better check whether the relevant packages and libraries are installed in your system！
1. pandas, os, shutil, re, numpy, glob, matplotlib are necessary for python3.x. (Python 3.9.19 (main, May  6 2024, 19:43:03)  was OK, in my testing!)
If you choose to install ananconda on your system, these basic packages are available.

# Notes
The writing of this scripts are inspired from both the DM-Sigma plot of Pan et al and the ACCEL_sift.py of PRESTO.

This script was originally designed to select faint millisecond pulsars with high dispersion mearsure (e.g., DM > 100 cm$\-3$pc).

In this script, you are allowed to set the conditions of pulsar candidate filtering in the first few lines of python script, by yourself.

The following are related references：

1. PRESTO

https://github.com/scottransom/presto

2. DM-Sigma plot from Pan et al

https://ui.adsabs.harvard.edu/abs/2021RAA....21..143P/abstract

3. If there is any help to you, please cite or indicate the source, thank you!


