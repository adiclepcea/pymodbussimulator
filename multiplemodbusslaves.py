'''multiplemodbusslaves contains the implementation for
a simulator faking multiple modbus slaves'''
import yaml
import sys
import serial
import serial.rs485
import modbusreader
import Queue
import random
from time import sleep
import logging

VALUE_RANDOM = "random_generated"
VALUE_FIXED = "fixed"
VALUE_READ = "read"

TYPE_HOLDING = "holding"
TYPE_INPUT = "input"
TYPE_COIL = "coil"
TYPE_INPUT_DISCRETE = "input_discrete"

REGISTRY_TYPES = {}
REGISTRY_TYPES[1] = TYPE_COIL
REGISTRY_TYPES[2] = TYPE_INPUT
REGISTRY_TYPES[3] = TYPE_HOLDING
REGISTRY_TYPES[4] = TYPE_INPUT_DISCRETE

def generate_random_value(min_value, max_value):
    '''generate a random value between min_value and max_value'''
    return random.randint(min_value, max_value)

class Connection(object):
    '''Connection class defines a serial connection'''
    def __init__(self, speed, port):
        self.speed = speed
        self.port = port
class Registry(object):
    '''Registry class defines a Registry inside a modbus slave'''
    def __init__(self, config_dict):
        self.location = config_dict["location"]
        self.max = config_dict["max"]
        self.min = config_dict["min"]
        self.type = config_dict["type"]
        self.value = config_dict["value"]

class NoSuchRegistryError(Exception):
    '''NoSuchRegistryError is an error generated when a registry
    with an unmatched address or type was called by the modbus master'''
    def __init__(self, address, location, reg_type):
        Exception.__init__(self)
        self.address = address
        self.location = location
        self.type = reg_type
    def __str__(self):
        return repr(\
        "There is no matching registry for slave {} \
        at location {} with type {}".format(\
        self.address, self.location, self.type))

class Slave(object):
    '''Slave class defines a modbus slave'''
    def __init__(self, config_dict):
        self.address = config_dict["address"]
        self.description = config_dict["description"]
        self.registries = []
        for registry_config in config_dict["registries"]:
            self.registries.append(Registry(registry_config))

    def write_registry(self, package):
        '''write_registry is a function to write values in the package to
        the registries '''
        #a successful write single registry should return the initial package.
        #for now we do nothing with this, so we consider it a success
        return package


    def respond_to_request(self, package):
        '''respond_to_request is a the function that based on the request in
        package will return either a response containing the requested values
        or the corresponding error response'''
        if package[0] != self.address:
            print "Invalid address for me. I'm {} and request address is {}".\
                format(self.address, package[0])
            return None
        request_type = 0
        try:
            request_type = package[1]
            #we do not implement write functions,
            #so we only mock a write and return the confirm package
            if request_type == 0x06 or request_type == 0x05:
                return self.write_registry(package)
            location_to_read = package[2] * 256 + package[3]
            length_to_read = package[4] * 256 + package[5]
            values = self.ask_values(REGISTRY_TYPES[request_type], \
                location_to_read, length_to_read)
            package = []
            package.append(self.address)
            package.append(request_type)
            print package
            bytes_to_follow = 0
            #for coils and discrete inputs we need to
            #calculate the value to send
            if request_type == 1 or request_type == 2:
                bytes_to_follow = len(values)/8
                if len(values) % 8 > 0:
                    bytes_to_follow += 1
                package.append(bytes_to_follow)
                for i in xrange(0, len(values), 8):
                    result = 0
                    for j in range(min(7, len(values) - i - 1), -1, -1):
                        result = (result << 1) + \
                            (1 if values[8 * (i / 8) + j] else 0)
                    print result
                    package.append(result)
            #for registers and inputs we put 2 bytes for register
            elif request_type == 3 or request_type == 4:
                bytes_to_follow = len(values) * 2
                package.append(bytes_to_follow)
                for value in values:
                    package.append(value / 256)
                    package.append(value % 256)

            return package
        except NoSuchRegistryError as ex:
            print ex
            package = []
            package.append(self.address)
            package.append(request_type | 0b10000000)
            package.append(0x02) #error code for Illegal Data Address
            return package


    #this only works if the registries are passed in ascending order in config
    def ask_values(self, reg_type, location, length):
        '''ask_values reads the values in the registries as they were asked
        by the modbus master, by type and number(length) required starting
        at a certain location'''
        loc = location
        values = []
        #our maximum location was surpassed - raise an error
        if location+length >= 65535 or location + length > \
            self.registries[len(self.registries)-1].location+1:
            raise NoSuchRegistryError(self.address, loc, reg_type)
        #is there a registry here
        if location < self.registries[0].location:
            raise NoSuchRegistryError(self.address, loc, reg_type)
        #search for first location
        start = 0
        for reg in self.registries:
            if reg.location == location:
                break
            else:
                start = start + 1
        #identify the values
        for i in range(start, len(self.registries)):
            reg = self.registries[i]
            if reg.location == loc:
                if reg.type == reg_type:
                    #we add the corresponding value
                    #todo - move this in corresponding methods
                    if reg.value == VALUE_FIXED:
                        values.append(reg.max)
                    elif reg.value == VALUE_RANDOM:
                        values.append(generate_random_value(reg.min, \
                            reg.max))
                    elif reg.value == VALUE_READ:
                         #todo - change to read the value from somewhere
                        values.append(11)
                else:
                    #if the register is not the valid type, we raise an error
                    raise NoSuchRegistryError(self.address, loc, reg_type)
            elif len(values) > 0:
                raise NoSuchRegistryError(self.address, loc, reg_type)

            loc = loc+1
            if loc == location + length and len(values) > 0:
                return values
        raise NoSuchRegistryError(self.address, loc, reg_type)


class Configuration(object):
    '''Configuration is a class that contains the details for
    connection and the slaves that this program will simulate'''
    def __init__(self, config_file_name):
        self.slaves = []
        self.connection = None
        yaml_config = yaml.load(file(config_file_name))
        self.load(yaml_config["connection"], yaml_config["slaves"])

    def load(self, connection, slaves):
        '''load is the method that will load the configuration in the
        configuration file into the Configuration class'''
        self.connection = Connection(connection[0]["speed"],\
            connection[0]["port"])
        self.slaves = []
        for slave in slaves:
            self.slaves.append(Slave(slave))


if __name__ == '__main__':
    CONFIG = Configuration("config.yaml")
    sys.stdout.write(\
    'ModBus bus on port {}, speed={}.\nActing as {} slaves.\n'.format(\
    CONFIG.connection.port, CONFIG.connection.speed, len(CONFIG.slaves)))
    sys.stdout.write("Press Ctrl+C to stop\n")

    try:
        SERIAL_COMM = serial.rs485.RS485(\
            CONFIG.connection.port, baudrate=CONFIG.connection.speed, \
            timeout=10)
        SERIAL_COMM.rs485_mode = serial.rs485.RS485Settings(delay_before_tx=0.2)
    except serial.SerialException as ex:
        logging.exception("error openning serial port {0}".format(ex))
        exit(1)

    BUS_QUEUE = Queue.Queue()
    MR = modbusreader.ModBusReader(CONFIG.slaves, BUS_QUEUE)
    while 1:
        if SERIAL_COMM.inWaiting() > 0:
            for c in SERIAL_COMM.read(SERIAL_COMM.inWaiting()):
                BUS_QUEUE.put(ord(c))
            SERIAL_COMM.flushInput()
            SERIAL_COMM.flushOutput()
            if MR.check_for_full_package() == modbusreader.PACKAGE_OK:
                print ''.join(hex(x) for x in MR.response)
                SERIAL_COMM.write(''.join(chr(x) for x in MR.response))
                SERIAL_COMM.flushOutput()

        sleep(0.1)


    SERIAL_COMM.close()
