#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

time=90
bwnet=1.5
# TODO: If you want the RTT to be 20ms what should the delay on each
# link be?  Set this value correctly.
delay=10

iperf_port=5001

protocol=quic

for qsize in 20 100; do
    dir=quic-q$qsize

    # TODO: Run bufferbloat.py here...
    python3 bufferbloat.py --bw-net $bwnet --delay $delay --dir $dir --time $time --maxq $qsize --protocol $protocol

    # TODO: Ensure the input file names match the ones you use in
    # bufferbloat.py script.  Also ensure the plot file names match
    # the required naming convention when submitting your tarball.
    python3 plot_queue.py -f $dir/q.txt -o quic-buffer-q$qsize.png
    python3 plot_ping.py -f $dir/ping.txt -o quic-rtt-q$qsize.png
done
