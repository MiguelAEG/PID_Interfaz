import socket
import time
import json

def start_server(host="127.0.0.1", port=5000):  # Cambia a localhost
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Servidor escuchando en {host}:{port}")
        conn, addr = server_socket.accept()
        print(f"Conexión establecida con {addr}")
        with conn:
            time_step = 0
            while True:
                data = {
                    "Time": time_step * 0.1,
                    "Setpoint": 50.0,
                    "Valor Medido": 50.0 - time_step * 0.5,
                    "Error": time_step * 0.5,
                    "P": 0.1,
                    "I": 0.05,
                    "D": 0.01
                }
                print(f"Enviando datos: {data}")  # Mensaje de depuración
                conn.sendall(json.dumps(data).encode('utf-8'))
                time.sleep(1)
                time_step += 1

if __name__ == "__main__":
    start_server()
