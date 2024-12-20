# Note: Mininet must be run as root. So invoke this shell script
# using sudo.

time=90
bwnet=1.5
# RTT mínimo de 20ms: atraso de 10ms em cada direção
delay=10

iperf_port=5001

# Apenas BBR como algoritmo de controle de congestionamento
cong=bbr

for qsize in 20 100; do
	dir=${cong}-q$qsize

	# Criação do diretório de saída, se não existir
	mkdir -p $dir

	# Executa o script bufferbloat.py com o algoritmo BBR
	python3 bufferbloat.py --bw-net $bwnet --delay $delay --dir $dir --time $time --maxq $qsize --cong $cong

	# Plota os gráficos com base nos resultados
	python3 plot_queue.py -f $dir/q.txt -o ${cong}-buffer-q$qsize.png
	python3 plot_ping.py -f $dir/ping.txt -o ${cong}-rtt-q$qsize.png
done

