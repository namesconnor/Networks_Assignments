import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)

    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)


## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths
    dst_S_length = 5
    prot_S_length = 1

    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise ('%s: unknown prot_S option: %s' % (self, self.prot_S))
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0: NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length: NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise ('%s: unknown prot_S field: %s' % (self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length:]
        return self(dst, prot_S, data_S)


## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False  # for thread termination

    ## called when printing the object
    def __str__(self):
        return self.addr

    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out')  # send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


## Implements a multi-interface router
class Router:

    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False  # for thread termination
        self.name = name
        self.count = 0
        # create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        # save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D  # {neighbor: {interface: cost}}
        # TODO: set up the routing table for connected hosts
        self.rt_tbl_D = {}  # {destination: {router: cost}}
        i = 0
        for neighbor, interface in cost_D.items():
            self.rt_tbl_D.update({neighbor: {self.name: interface}})
            # self.rt_tbl_D.update({neighbor:{self.}})
        print('%s: Initialized routing table' % self)
        self.print_routes()

    ## Print routing table
    def print_routes(self):
        # TODO: print the routes as a two dimensional table
        print(self.rt_tbl_D)
        print("╒══════╤══════╤══════╤══════╤══════╕");
        print("│ RA   │   H1 │   H2 │   RA │   RB │");
        print("╞══════╪══════╪══════╪══════╪══════╡")
        secondLine = ['-', '-', '-', '-', '-']
        for key in self.rt_tbl_D:
            for type in self.rt_tbl_D[key]:
                if (type == "RA"):
                    secondLine[0] = "RA";
                    if (key == "H1"):
                        secondLine[1] = str(list(self.rt_tbl_D[key][type].values())[0]);
                    if (key == "H2"):
                        secondLine[2] = str(list(self.rt_tbl_D[key][type].values())[0]);
                    if (key == "RA"):
                        secondLine[3] = str(list(self.rt_tbl_D[key][type].values())[0]);
                    if (key == "RB"):
                        secondLine[4] = str(list(self.rt_tbl_D[key][type].values())[0]);
                if (type == "RB"):
                    secondLine[0] = "RB";
                    if (key == "H1"):
                        secondLine[1] = str(list(self.rt_tbl_D[key][type].values())[0]);
                    if (key == "H2"):
                        secondLine[2] = str(list(self.rt_tbl_D[key][type].values())[0]);
                    if (key == "RA"):
                        secondLine[3] = str(list(self.rt_tbl_D[key][type].values())[0]);
                    if (key == "RB"):
                        secondLine[4] = str(list(self.rt_tbl_D[key][type].values())[0]);
        print("│ " + secondLine[0] + "   │    " + secondLine[1] + " │    " + secondLine[2] + " │    " + secondLine[
            3] + " │    " + secondLine[4] + " │")

    ## called when printing the object
    def __str__(self):
        return self.name

    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            # get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            # if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p, i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1
            print('')
            data = NetworkPacket.from_byte_S(p.__str__())
            destination = data.dst
            nextStop = list(self.rt_tbl_D.get(destination))[0]

            if nextStop == self.name:
                interface = list(self.rt_tbl_D.get(destination)[self.name])[0]
            else:
                interface = list(self.rt_tbl_D.get(nextStop)[self.name])[0]

            self.intf_L[interface].put(p.to_byte_S(), "out", True)
            print('%s: forwarding packet "%s" from interface %d to %d' % \
                  (self, p, i, interface))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # TODO: Send out a routing table update
        # create a routing table update packet
        routingMessage = EncodedMessage(self.name, self.rt_tbl_D)
        p = NetworkPacket(0, 'control', routingMessage.get_byte_S())
        try:
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        print('%s: Received routing update %s from interface %d' % (self, p, i))
        print("UPDATES TO TABLE: ", p.data_S)
        decodedTable = p.data_S[2:];
        table = eval(decodedTable)
        needsResponse = not (table == self.rt_tbl_D)

        decodedName = p.data_S[:2];

        table_keys = list(table.keys());

        if needsResponse:
            for host, cost in table.items():
                if host in self.rt_tbl_D.keys():
                    break
                portCost = list(list(cost.values())[0].values())[0]
                portInt = list(list(cost.values())[0].keys())[0]
                # huck those bitches in so that all the fucking routers are in
                if (host in self.rt_tbl_D.keys()):
                    print()
                else:
                    self.rt_tbl_D.update({host: cost})
            # now check the fucking costs i guess
            for host, cost in table.items():
                if host in self.rt_tbl_D.keys():
                    break
                portCost = list(list(cost.values())[0].values())[0]
                newcost = portCost + list(list(self.rt_tbl_D[host].values())[0].values())[0]
                currentcost = list(list(self.rt_tbl_D[host].values())[0].values())[0];
                if (decodedName not in self.rt_tbl_D[host].keys()):
                    self.rt_tbl_D[host][decodedName] = newcost
                else:
                    if (newcost < currentcost):
                        self.rt_tbl_D[host][decodedName] = newcost
            print("DONE")
            print(self.rt_tbl_D)
            print('')
            self.send_routes(i)
        else:
            print("no updates")
            print('')

    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return


class EncodedMessage:
    def __init__(self, name, table):
        self.name = name
        self.table = table

    @classmethod
    def from_byte_S(self, byte_S):
        # extract the fields
        name_decoded = byte_S[len(self.name):]
        table_decoded = byte_S[:len(self.table)]
        return self(name_decoded, table_decoded)

    def get_byte_S(self):
        # convert sequence number of a byte field of seq_num_S_length bytes
        name_byte = str(self.name).zfill(len(self.name))
        table_byte = str(self.table).zfill(len(self.table))
        return name_byte + table_byte