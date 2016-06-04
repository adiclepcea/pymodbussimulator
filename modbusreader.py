'''modbusreader is a module containing functions needed to comunicate with the
Modbus bus.
It will eventually also have writing functionality, but for now is just a
reader.

ModBusReader receives a list of slaves to emulate. Slaves are described
in the multiplemodbusslaves module.
'''

NO_FULL_PACKAGE_AVAILABLE = 1
NO_SLAVE_MATCH = 2
INCORRECT_CRC = 3
PACKAGE_OK = 4

def crc16(req_in):
    '''function to calculate crc - check the package validity'''
    crc = 0xFFFF
    length = len(req_in)
    i = 0
    while i < length:
        j = 0
        #crc = crc ^ ord(reqIn[i])
        crc = crc ^ req_in[i]
        while j < 8:
            if crc & 0x1:
                mask = 0xA001
            else:
                mask = 0x00
            crc = ((crc >> 1) & 0x7FFF) ^ mask
            j += 1
        i += 1
    if crc < 0:
        crc -= 256
    #crc% 256* ; crc / 256 -will provide the pachet order
    return crc

class ModBusReader(object):
    '''ModBusReader reads the bus Queue and
    passes the requests to the slaves it finds in the requests
    if they are betwees the passed "slaves"'''
    def __init__(self, slaves, q):
        self.slaves = slaves
        self.package = []
        self.response = None
        if slaves != None:
            for slave in slaves:
                print "listening on behalf of slave:", slave.address
        self.bus_queue = q

    def evaluate_crc(self, slave):
        '''evaluate_crc evaluetes if a package is complete and valid
        if it is ok, it finds out the response packet from the slave
        and returns PACKAGE_OK, else it returns INCORRECT_CRC'''
        crc = crc16(self.package[:6])
        if crc%256 == self.package[6] and \
            crc/256 == self.package[7]:
            self.response = self.create_response(slave)
            return PACKAGE_OK
        else:
            return INCORRECT_CRC

    def check_for_full_package(self):
        '''checks if there is a full modbus packet in the queue
        this will only work if the first byte in the Queue is the first byte of
        a packet (i.e. the queue does not start with the middle of the packet)
        the requests 15 (Force Multiple Coils) and
        16(Preset Multiple Registers) are not yet supported
        the function eliminates every 0 from the beginning of the queue'''
        while self.bus_queue.qsize() >= 8 and self.bus_queue.queue[0] == 0:
            self.bus_queue.get()
        if self.bus_queue.qsize() >= 8:
            self.package = []
            for _ in range(0, 8):
                self.package.append(self.bus_queue.get())
            #################################################################
            ####    force multiple coils and preset multiple registers   ####
            ####        are not tested yet, as I have no use of them     ####
            #################################################################
            if self.package[1] == 15: #force multiple coils
                number_of_coils_to_write = self.package[4]*256+self.package[5]
                plus_read = number_of_coils_to_write/8
                if number_of_coils_to_write%8 > 0:
                    plus_read += 1
                    #package[6] should be now equal to plus_read
                for _ in range(0, plus_read + 1):
                    #this will block waiting for data
                    self.package.append(self.bus_queue.get())
            if self.package[1] == 16: #preset multiple registers
                plus_read = self.package[4]*256 + self.package[5]
                #package[6] should be now equal to plus_read
                for _ in range(0, plus_read+1):
                    #this will block waiting for data
                    self.package.append(self.bus_queue.get())
            ##################################################################
            ####                    end of untested code                  ####
            ##################################################################
            for slave in self.slaves:
                if slave.address == self.package[0]:
                    return self.evaluate_crc(slave)
            print "i do not know slave:", self.package[0]
            return NO_SLAVE_MATCH
        else:
            return NO_FULL_PACKAGE_AVAILABLE

    def create_response(self, slave):
        '''create_response method askes for a response from the requested slave
        and then adds the crc (validation bytes) to the packet and returns the
        resulted modbus package that can then be transmited'''
        resp = slave.respond_to_request(self.package)
        if resp[1] == 5 or resp[1] == 6:
            return resp
        crc = crc16(resp)
        resp.append(crc%256)
        resp.append(crc/256)
        return resp
