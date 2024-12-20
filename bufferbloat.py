from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

import numpy as np

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen

import sys
import os
import math

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default that doesn't have the usual sawtooth
# behaviour.  For those who are curious, invoke this script with
# --cong cubic and see what happens...
# sysctl -a | grep cong should list some interesting parameters.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

parser.add_argument('--protocol',
                    help="Protocol to use: tcp or quic",
                    choices=['tcp', 'quic'],
                    default='tcp')

# Expt parameters
args = parser.parse_args()

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        # TODO: create two hosts
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        # TODO: Add links with appropriate characteristics
        # h1 - switch
        self.addLink(h1, switch, bw=1000, delay=0)

        # switch - h2
        self.addLink(switch, h2, bw=1.5, delay=10, max_queue_size=100)

# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!

def start_quic(net):
    h1 = net.get("h1")
    h2 = net.get("h2")
    print("Iniciando servidor QUIC")

    server = h2.popen("./quiche_server --port 4433")

    print("Iniciando cliente QUIC")

    server_ip = h1.IP()
    client = h1.popen(f"./quic_client --host {server_ip} --port 443 --duration {args.time}")

    return server, client

def start_iperf(net):
    h1 = net.get('h1')
    h2 = net.get('h2')
    print("Starting iperf server...")
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    server = h2.popen("iperf -s -w 16m")

    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    # client = ... 
    print("Starting iperf CLIENT...")
    client = h1.popen("iperf -c %s -t %d"%(h2.IP(), args.time))
    return server, client

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_ping(net):
    # TODO: Start a ping train from h1 to h2 (or h2 to h1, does it
    # matter?)  Measure RTTs every 0.1 second.  Read the ping man page
    # to see how to do this.
    h1 = net.get("h1")
    h2 = net.get("h2")

    print("Executando ping...")
    ping_proc = h1.popen("ping -i 0.1 %s > %s/ping.txt"% (h2.IP(), args.dir), shell=True)

    # Hint: Use host.popen(cmd, shell=True).  If you pass shell=True
    # to popen, you can redirect cmd's output using shell syntax.
    # i.e. ping ... > /path/to/ping.
    return ping_proc

# Função para baixar a página da web periodicamente e medir o tempo

def fetch_webpage(net, repetitions=3, interval=5):
    h2 = net.get('h2')  # Cliente que fará o download
    h1_ip = net.get('h1').IP()  # IP do servidor web
    times = []  # Lista para armazenar os tempos de download

    for _ in range(repetitions):
        # Inicia a medição de tempo
        start_time=time()
        # Realiza o download da página usando curl e registra o tempo de download
        result = h2.cmd("curl -o /dev/null -s -w %%{time_total} http://%s/index.html" % h1_ip)
        # Calcula o tempo total para o download e armazena
        
        fetch_time = float(result)
        times.append(fetch_time)
        
        print("Fetch time:", fetch_time, "seconds")
        
        # Aguarda o intervalo de tempo especificado antes da próxima repetição
        sleep(interval)
    
    # Calcula a média e o desvio padrão dos tempos de download
    mean_fetch_time = np.mean(times)
    std_dev_fetch_time = np.std(times)
    
    print("Tempo médio de download da página:", mean_fetch_time, "segundos")
    print("Desvio padrão do tempo de download da página:", std_dev_fetch_time, "segundos")
    
    return times  # Retorna os tempos para análise posterior


# Função para iniciar o servidor web em h1
def start_webserver(net):
    h1 = net.get('h1')
    proc = h1.popen("python3 -m http.server --directory content 80", shell=True)  # Inicia o servidor web em h1
    sleep(1)  # Aguarda um segundo para garantir que o servidor esteja ativo
    return proc

def fetch_complex_webpage(net, repetitions=3, interval=5):
    h2 = net.get("h2")
    h1_ip = net.get("h1").IP()
    times = []

    files = [
        "image1.jpg",
        "image2.jpg",
        "image3.jpg",
        "image4.jpg",
        "image5.jpg",
        "image6.jpg",
        "script1.js",
        # "video1.mp4",
        "index.html"
    ]

    for _ in range(repetitions):
        start_time = time()

        # Realizar requisicoes para diferentes arquivos em ./content
        for file in files:
            result = h2.cmd("curl -o /dev/null -s -w %%{time_total} http://%s/%s"%(h1_ip, file))
            fetch_time = float(result)
            times.append(fetch_time)
            print(f"Tempo de fetch do arquivo: {file}: {fetch_time} seconds")

        total_time = time() - start_time
        print(f"Tempo total de fetch dos arquivos: {total_time}")
        sleep(interval)

    mean_fetch_time = np.mean(times)
    std_dev_fetch_time = np.std(times)

    print("Tempo médio de download (arquivos complexos):", mean_fetch_time, "segundos")
    print("Desvio padrão:", std_dev_fetch_time, "segundos")

    return times

def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    # Set congestion control algorithm (for TCP only)
    if args.protocol == 'tcp':
        os.system(f"sysctl -w net.ipv4.tcp_congestion_control={args.cong}")
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()

    # TODO: Start monitoring the queue sizes.  Since the switch I
    # created is "s0", I monitor one of the interfaces.  Which
    # interface?  The interface numbering starts with 1 and increases.
    # Depending on the order you add links to your network, this
    # number may be 1 or 2.  Ensure you use the correct number.
    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/q.txt' % (args.dir))


    if args.protocol == 'quic':
        quic_server, quic_client = start_quic(net)
    else:
        iperf_server, iperf_client = start_iperf(net)
        # server = start_video_server(net)  # Inicia o servidor de vídeo
        # client = start_video_client(net)  # Inicia o cliente de vídeo

    # TODO: measure the time it takes to complete webpage transfer
    # from h1 to h2 (say) 3 times.  Hint: check what the following
    # command does: curl -o /dev/null -s -w %{time_total} google.com
    # Now use the curl command to fetch webpage from the webserver you
    # spawned on host h1 (not from google!)
    # Hint: Verify the url by running your curl command without the
    # flags. The html webpage should be returned as the response.

    # Inicia o trem de pings entre h1 e h2 para medir RTTs
    ping_proc = start_ping(net)

    # Inicia o servidor web em h1 e realiza downloads periódicos de h1 para h2
    web_server_proc = start_webserver(net)
    fetch_times = fetch_complex_webpage(net)

    # Calcula a média e o desvio padrão dos tempos de busca
    mean_fetch_time = np.mean(fetch_times)
    std_dev_fetch_time = np.std(fetch_times)


    # Hint: have a separate function to do this and you may find the
    # loop below useful.
    start_time = time()
    while True:
        # do the measurement (say) 3 times.
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print("%.1fs left..." % (args.time - delta))

    # TODO: compute average (and standard deviation) of the fetch
    # times.  You don't need to plot them.  Just note it in your
    # README and explain.

    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    # CLI(net)
    if args.protocol == 'quic':
        quic_server.terminate()
        quic_client.terminate()
    else:
        iperf_server.terminate()
        iperf_client.terminate()
    ping_proc.terminate()
    web_server_proc.terminate()


    # server.terminate()
    # client.terminate()
    qmon.terminate()
    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()
