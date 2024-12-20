import socket

def start_video_client(server_ip, server_port, output_file, chunk_size=1024):
    print("Starting video client...")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    print(f"Connected to {server_ip}:{server_port}")

    with open(output_file, "wb") as f:
        while True:
            chunk = client_socket.recv(chunk_size)
            if not chunk:
                break  # Fim do streaming

            # Escreve o chunk de vídeo no arquivo de saída
            f.write(chunk)

    print("Video streaming finished.")
    client_socket.close()

if __name__ == "__main__":
    server_ip = "127.0.0.1"  # IP do servidor
    server_port = 12345  # Porta do servidor
    output_file = "received_video.mp4"  # Arquivo de saída onde o vídeo será salvo
    start_video_client(server_ip, server_port, output_file)

