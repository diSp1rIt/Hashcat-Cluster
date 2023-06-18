from threading import Thread
import subprocess
from sys import platform
from os.path import exists, isdir
from os import chdir
from time import sleep
from threading import Thread

process: subprocess.Popen = None
thread: Thread = None
last_output = ''
exit_ = False


def load_hashcat():
    if platform == 'win32':
        if not isdir('hashcat'):
            raise EnvironmentError('No such directory "hashcat"')
        if not exists('hashcat/hashcat.exe'):
            raise EnvironmentError('No such file "hashcat/hashcat.exe"')
        chdir('hashcat')
        return 'hashcat.exe'
    if platform == 'posix':
        return 'hashcat'


def start_hashcat(hash: str, hash_mod: str = '0', workload_profile: str = '3',
                  mask: str = None):
    global process, thread

    progname = load_hashcat()

    print(subprocess.check_output([progname, '-m', hash_mod, '--show', hash]).decode())
    exit()

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
        stdout=subprocess.PIPE
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
    if cmd == 'exit' or cmd == 'quit':
        # TODO exiting all nodes
        process.kill()
        exit_ = True
        print('Bye!')
        exit()
    elif cmd.split()[0] == 'echo':
        print(' '.join(cmd.split()[1:]))
    elif cmd.split()[0] == 'start':
        print('Wait...')
        start_hashcat(
            hash='5e8667a439c68f5145dd2fcbecf02209',
        )
        print('Started')
    elif cmd == 'status':
        status = get_status()
        print(status)
    else:
        print('Command not found')


def system_command_handler(cmd: str):
    pass


def main():
    while True:
        cmd = input('> ')
        user_command_handler(cmd)


if __name__ == '__main__':
    main()
