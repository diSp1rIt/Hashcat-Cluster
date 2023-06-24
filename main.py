from threading import Thread
import subprocess
from sys import platform
from os.path import exists, isdir
from os import chdir
from time import sleep
from threading import Thread
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from nodesystem import *

print_ = print


def print(*args, **kwargs):
    print_('\r', end='')
    print_(*args, end='\n> ')


def load_hashcat():
    if platform == 'win32':
        if not isdir('hashcat'):
            raise EnvironmentError('No such directory "hashcat"')
        if not exists('hashcat/hashcat.exe'):
            raise EnvironmentError('No such file "hashcat/hashcat.exe"')
        chdir('hashcat')
        return 'hashcat.exe'
    if platform == 'linux':
        return 'hashcat'


process: subprocess.Popen = None
thread: Thread = None
last_output = ''
exit_ = False
controller = NodePool()
prog_name = load_hashcat()


def terminate():
    global exit_
    if process:
        process.kill()
    exit_ = True
    exit()


def do_benchmark(mode):
    return subprocess.check_output([prog_name, '-m', mode, '-b', '--quiet', '--machine-readable']).split(b':')[
        -1].decode().strip()


def start_hashcat(hash: str, mask: str, hash_mod: str = '0', workload_profile: str = '1',
                  ):
    global process, thread

    try:
        print(subprocess.check_output([prog_name, '-m', hash_mod, '--show', hash]).decode())
        terminate()
    except:
        pass

    command = ' '.join([
        prog_name,
        '--quiet',
        '--status',
        '--status-json',
        '--status-timer=5',
        '-m',
        hash_mod,
        '-a',
        '3',
        '-w',
        workload_profile,
    ])
    if hash:
        command += f' {hash}'
    if mask:
        command += f' {mask}'
    process = subprocess.Popen(
        command.split(),
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE
    )

    def manage_output():
        global last_output

        while True and not exit_:
            last_output = process.stdout.readline()
            sleep(5)

    thread = Thread(target=manage_output)
    thread.start()

    sleep(15)


def get_status():
    if not process:
        return False
    return last_output


def user_command_handler(cmd: str):
    global exit_

    cmd = cmd.strip()
    cmd_list = cmd.split()
    if cmd_list[0] == 'exit' or cmd_list[0] == 'quit':
        # TODO exiting all nodes
        terminate()
        print('Bye!')
        exit()
    elif cmd_list[0] == 'echo':
        print(' '.join(cmd_list[1:]))
    elif cmd_list[0] == 'start':
        print('Wait...')
        start_hashcat(
            hash=cmd_list[1],
            mask=cmd_list[2]
        )
        print('Started')
    elif cmd_list[0] == 'status':
        status = get_status()
        print(status)
    elif cmd_list[0] == 'add':
        if send_command(b'setup', cmd_list[1]) == b'done':
            controller.addNode(Node(cmd_list[1]))
            print(f'Added node {cmd_list[1]}')
        else:
            print(f'Node is not accessible')
    elif cmd_list[0] == 'send':
        for node in controller:
            res = send_command(' '.join(cmd_list[1:]).encode(), node.ip)
            if res:
                print(f'From {node.ip}: {res}')
            else:
                print(f'{node.ip} is not answering')
    elif cmd_list[0] == 'bench' or cmd_list[0] == 'benchmark':
        for node in controller:
            node.doBenchmark(int(cmd_list[1]))
        print('Benchmark started')
        print('Host:', do_benchmark(cmd_list[1]))
    else:
        print('Command not found')


def system_command_handler(cmd: bytes, client: socket, addr: str, server_ip: str):
    cmd = cmd.strip()
    command, *args = cmd.split(b'|')
    if command == b'echo':
        message = args[0]
        client.sendall(message)
    elif command == b'setup':
        controller.addNode(Node(addr))
        client.sendall(b'done')
        print(f'Added node {addr}')
    elif command == b'bench':
        mode = int(args[0])
        print('Node started benchmark')
        res = subprocess.check_output([prog_name, '-m', mode, '-b', '--quiet', '--machine-readable'])
        send_command(b'benchans|' + str(mode).encode() + b'|' + res.split(b':')[-1].strip(), addr, wait=False)
    elif command == b'benchans':
        mode, value = int(args[0]), int(args[1])
        for node in controller:
            if node.ip == addr:
                node.setBenchmark(mode, value)
        print(f'From {addr}:', mode, value)
    client.close()


def main():
    def server():
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(('10.0.0.0', 0))
        ip = s.getsockname()[0]
        del s

        with socket(AF_INET, SOCK_STREAM) as s:
            s.bind((ip, 24545))
            s.settimeout(5)
            print(f'Started listener on {ip}:24545')
            while not exit_:
                s.listen()
                try:
                    sock, addr = s.accept()
                except:
                    continue
                data = sock.recv(1024)
                system_command_handler(data, sock, addr[0], ip)
            s.close()

    thr = Thread(target=server)
    thr.start()
    sleep(1)
    while True:
        cmd = input()
        user_command_handler(cmd)


if __name__ == '__main__':
    main()
