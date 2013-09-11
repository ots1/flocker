import socket
import asyncore
import asynchat
from time import sleep


class Channel(asynchat.async_chat):
    """The server's representation of a client"""
    message_terminator = '\n\n'

    def __init__(self, conn, addr, server=None):
        asynchat.async_chat.__init__(self, conn)
        self.addr = addr
        self.server = server
        self.ibuffer = ""
        self.obuffer = []
        self.set_terminator(self.message_terminator)

    def collect_incoming_data(self, data):
        self.ibuffer += data
    
    def found_terminator(self):
        data = self.ibuffer
        self.ibuffer = ""

        if hasattr(self, 'handle_data'):
            self.handle_data(data)
        else:
            print "ignoring data from channel %s\n" % self.addr

    def pump(self):
        [asynchat.async_chat.push(self, d) for d in self.obuffer]
        self.obuffer = []

    # 'send' would collide with inherited method
    def Send(self, data):
        """Append data to the outgoing buffer."""
        self.obuffer.append(data)

    def handle_close(self):
        if hasattr(self, 'Close'):
            self.Close()
        asynchat.async_chat.handle_close(self)
        print "channel closed %s:%s" % self.addr


class Server(asyncore.dispatcher):
    ChannelType = Channel

    def __init__(self, localaddr=('localhost',1234)):
        asyncore.dispatcher.__init__(self) # init of parent class
        self.channels = []  # channels connected to the server

        # set up the socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
        self.set_reuse_addr()
        self.bind(localaddr)
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        self.channels.append(self.ChannelType(conn, addr, self))
        print "Accepting connection from %s:%s" % addr
        if hasattr(self, "accept_connection"):
            self.accept_connection(self.channels[-1])

    def bcast(self, msg):
        for c in self.channels:
            c.Send(msg)

    def pump(self):
        for c in self.channels:
            c.pump()
        asyncore.poll()



if __name__=='__main__':
    server = Server()
    while 1:
        server.pump()
        print server.channels
        sleep(0.5)
