from socket import socket, AF_INET, SOCK_STREAM


def send_command(cmd: bytes, ip: str, wait=True):
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((ip, 24545))
            s.sendall(cmd)
            if wait:
                return s.recv(1024)
            return
    except Exception as e:
        print(e)
        return False


class Node:
    def __init__(self, ip: str):
        self.ip = ip
        self.benchmark = dict()

    def sendCommand(self, command: str, wait: bool = True):
        command = command.encode()
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((self.ip, 24545))
                s.sendall(command)
                if wait:
                    return s.recv(1024)
                return
        except Exception as e:
            print(e)
        return False

    def echo(self, text: str):
        return self.sendCommand(f'echo|{text}')

    def setBenchmark(self, mode: int, value: int) -> None:
        self.benchmark[mode] = value

    def getBenchmark(self, mode: int):
        if mode not in self.benchmark:
            return -1
        return self.benchmark[mode]

    def doBenchmark(self, mode: int) -> None:
        self.sendCommand(f'bench|{mode}', wait=False)


class NodePool:
    def __init__(self):
        self.nodes: set[Node] = set()

    def __iter__(self):
        return iter(self.nodes)

    def addNode(self, node: Node):
        if node not in self:
            self.nodes.add(node)

    def __contains__(self, item: Node):
        return item in self.nodes

    def enumerate(self) -> tuple[int, int]:
        valid = 0
        invalid = 0
        for node in self.nodes:
            if node.echo('enum') == 'enum':
                valid += 1
            else:
                invalid += 1
        return valid, invalid

    def doBenchmark(self, mode: int) -> None:
        for node in self:
            node.doBenchmark(mode)

    def setBenchmark(self, ip: str, value: int):
        pass

