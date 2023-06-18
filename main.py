from threading import Thread
import subprocess
from sys import platform
from os.path import exists, isdir
from os import chdir
from time import sleep
from threading import Thread


process: subprocess.Popen = None
last_output = ''


def load_hashcat():
    if platform == 'win32':
        if not isdir('hashcat'):
            raise EnvironmentError('No such directory "hashcat"')
        if not exists('hashcat/hashcat.exe'):
            raise EnvironmentError('No such file "hashcat/hashcat.exe"')
        return 'hashcat/hashcat.exe'


def start_hashcat():
    global process
    chdir('hashcat')
    process = subprocess.Popen('hashcat.exe -a 3 -m 22000 -w 1 hand.hc22000 --status-json --quiet --status --status-timer=5'.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    def manage_output():
        global last_output

        while True:
            last_output = process.stdout.readline()
            sleep(5)

    thr = Thread(target=manage_output)
    thr.start()

    sleep(15)


def get_status():
    if not process:
        return False
    return last_output


def user_command_handler(cmd: str):
    if cmd == 'exit' or cmd == 'quit':
        # TODO exiting all nodes
        process.terminate()
        print('Bye!')
        exit()
    elif cmd.split()[0] == 'echo':
        print(' '.join(cmd.split()[1:]))
    elif cmd.split()[0] == 'start':
        print('Wait...')
        start_hashcat()
        print('Started')
    elif cmd == 'status':
        status = get_status()
        if not status:
            print('Process is not started yet')
            return
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
