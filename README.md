### A toolkit for pulsar hunters.
<table>
  <tr>
    <td>
      <details><summary><code>update log</code></summary>
        1. <code>residuals_plot.py</code>; this code generates publication-quality pulsar timing residual plots from <code>TEMPO</code> (https://tempo.sourceforge.net/tempo_idx.html) resid2.tmp files.<br>
        2. <code>ACCEL_sift.py</code>; a modified version of <code>PRESTO</code> (https://www.cv.nrao.edu/~sransom/presto/) toolkit’s original script, allowing users to run the sifting routine directly with command-line input parameters for more flexible and convenient use.<br>
        3. <code>FAST_tracking.py</code>; this script calculates and plots the altitude tracks (also tracking time) of celestial sources observed by the Five-hundred-meter Aperture Spherical radio Telescope (<code>FAST</code>, https://fast.bao.ac.cn/) for a given date and specified source(s).<br>
        4. <code>PulsarHub.md</code>; a catalog of several pulsar catalogs.<br>
        5. <code>Note.md</code>; a personal note.<br>
        6. <code>candidate.py</code> and <code>dmiter.py</code> are used in FFA search package <code>riptide</code> (https://github.com/v-morello/riptide) for generating customized candidate plots and ignoring optimal DM step plan.<br>
        7. <code>PulsarPICK</code>, a simple pipeline adapted from PRESTO's <code>ACCEL_sift.py</code> for processing <code>accelsearch</code> results. It also generates user-friendly candidate diagnostic plots by combining the standard time-series folding plot with a trial-DM versus detection-significance curve, where real pulsars typically show a bell-shaped peak around the optimal DM.<br>
        8. <code>Astronomy_Alerts</code>; a simple pipeline for aggregating ATel (The Astronomer's Telegram) and GCN Circular (NASA's Time-Domain and Multimessenger Alert System) emails using a Tencent email address (QQ).<br>
        ...
      </details>
    </td>
  </tr>
</table>
