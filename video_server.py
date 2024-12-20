import os
import time
import socket

def start_video_server(host, port, video_file, chunk_size=1024):
    # Abre o arquivo de vídeo
    with open(video_file, "rb") as f:
        print("Starting video server...")
        print(f)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)
        print("toma")
        print(f"Server listening on {host}:{port}")

        # Aceita a conexão do cliente
        client_socket, client_address = server_socket.accept()
        print(f"Connection established with {client_address}")

        # Envia chunks do arquivo de vídeo
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break  # Fim do arquivo

            # Envia o chunk de vídeo para o cliente
            client_socket.sendall(chunk)

            # Simula o atraso entre o envio dos chunks (representando o streaming)
            time.sleep(0.1)  # Delay para simular o streaming em tempo real

        print("Video streaming finished.")
        client_socket.close()
        server_socket.close()

if __name__ == "__main__":
    host = "0.0.0.0"  # Escuta em todos os IPs disponíveis
    port = 12345  # Porta para o servidor
    video_file = "video.mp4"  # Caminho para o arquivo de vídeo
    start_video_server(host, port, video_file)

