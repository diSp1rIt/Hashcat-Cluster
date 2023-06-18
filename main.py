from threading import Thread
import subprocess
from sys import platform
from os.path import exists, isdir
from os import chdir
from time import sleep
from threading import Thread
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM

process: subprocess.Popen = None
thread: Thread = None
last_output = ''
exit_ = False
nodes = set()


def terminate():
    global exit_
    if process:
        process.kill()
    exit_ = True
    exit()


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


def start_hashcat(hash: str, mask: str, hash_mod: str = '0', workload_profile: str = '1',
                  ):
    global process, thread

    progname = load_hashcat()

    try:
        print(subprocess.check_output([progname, '-m', hash_mod, '--show', hash]).decode())
        terminate()
    except:
        pass

    command = ' '.join([
        progname,
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
        with socket(AF_INET, SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((cmd_list[1], 24545))
            s.sendall(b'setup')
            if s.recv(1024) == b'done':
                nodes.add(cmd_list[1])
                print(f'Added node {cmd_list[1]}')
    elif cmd_list[0] == 'send':
        for ip in nodes:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((ip, 24545))
                s.sendall(' '.join(cmd_list[1:]).encode())
                print(f'From {ip}: {s.recv(1024).decode()}')
    elif cmd_list[0] == 'bench' or cmd_list[0] == 'benchmark':
        for ip in nodes:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((ip, 24545))
                s.sendall(b'bench' + f'|{cmd_list[1]}'.encode())
                s.close()
        print('Benchmark started')
    else:
        print('Command not found')


def system_command_handler(cmd: bytes, client: socket, addr: str, server_ip: str):
    cmd = cmd.strip()
    cmd_list = cmd.split(b'|')
    if cmd_list[0] == b'echo':
        client.sendall(cmd_list[1])
    elif cmd_list[0] == b'setup':
        nodes.add(addr)
        client.sendall(b'done')
        print(f'Added node {addr}')
    elif cmd_list[0] == b'bench':
        progname = load_hashcat()
        res = subprocess.check_output([progname, '-m', cmd_list[1].decode(), '-b', '--quiet', '--machine-readable'])
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((addr, 24545))
            s.sendall(b'benchans|' + res.split(b':')[-1])
            s.close()
    elif cmd_list[0] == b'benchans':
        print(f'From {addr}:', cmd_list[1].decode())
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
        cmd = input('> ')
        user_command_handler(cmd)


if __name__ == '__main__':
    main()
