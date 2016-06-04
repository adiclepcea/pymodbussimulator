import unittest
import modbusreader
import multiplemodbusslaves
import Queue

class TestModbusReader(unittest.TestCase):
    def init_slave_for_test(self,value):
        dReg = {}
        dReg["length"] = 1
        dReg["location"] = 1
        dReg["max"] = 122
        dReg["min"] = 0
        dReg["type"] = multiplemodbusslaves.TYPE_HOLDING
        dReg["value"] = value

        dSlave = {}
        dSlave["address"] = 1
        dSlave["description"] = "test_slave"
        dSlave["registries"] = []
        dSlave["registries"].append(dReg)
        slave = multiplemodbusslaves.Slave(dSlave)
        return slave
    def test_crc(self):
        mr = modbusreader.ModBusReader(None,None)
        st = [0x01,0x04,0x00,0x01,0x00,0x02]
        crc = modbusreader.crc16(st)
        self.assertEqual(crc,0x0b20)

        st = [0x11,0x03,0x00,0x6B,0x00,0x03]
        crc = modbusreader.crc16(st)
        self.assertEqual(crc%256,0x76)
        self.assertEqual(crc/256,0x87)

    def test_package_recognition(self):
        slave = self.init_slave_for_test(multiplemodbusslaves.VALUE_FIXED)
        q = Queue.Queue()
        mr = modbusreader.ModBusReader([slave],q)
        q.put(0x10)
        self.assertEqual(mr.check_for_full_package(),modbusreader.NO_FULL_PACKAGE_AVAILABLE)
        q.get()
        q.put(0x00)#just for test
        q.put(0x01)#address 1
        q.put(0x03)#read holding registers
        q.put(0x00)
        q.put(0x01)#start at address 1
        q.put(0x00)
        q.put(0x01)#read only one register
        q.put(0xd5)#crc byte 2
        q.put(0xca)#crc byte 1
        self.assertEqual(mr.check_for_full_package(),modbusreader.PACKAGE_OK)

        q.put(0x01)#address 1
        q.put(0x03)#read holding registers
        q.put(0x00)
        q.put(0x01)#start at address 1
        q.put(0x00)
        q.put(0x01)#read only one register
        q.put(0xd5)#crc byte 2
        q.put(0xc1)#wrong crc byte 1
        self.assertEqual(mr.check_for_full_package(),modbusreader.INCORRECT_CRC)

        slave.address = 2
        mr = modbusreader.ModBusReader([slave],q)
        q.put(0x01)#address 1 - not set now
        q.put(0x03)#read holding registers
        q.put(0x00)
        q.put(0x01)#start at address 1
        q.put(0x00)
        q.put(0x01)#read only one register
        q.put(0xd5)#crc byte 2
        q.put(0xca)#crc byte 1
        self.assertEqual(mr.check_for_full_package(),modbusreader.NO_SLAVE_MATCH)

    def test_package_response(self):
        slave = self.init_slave_for_test(multiplemodbusslaves.VALUE_FIXED)
        q = Queue.Queue()
        mr = modbusreader.ModBusReader([slave],q)
        q.put(0x01)#address 1
        q.put(0x03)#read holding registers
        q.put(0x00)
        q.put(0x01)#start at address 1
        q.put(0x00)
        q.put(0x01)#read only one register
        q.put(0xd5)#crc byte 2
        q.put(0xca)#crc byte 1
        self.assertEqual(mr.check_for_full_package(),modbusreader.PACKAGE_OK)
        r = mr.response
        self.assertEqual(len(r),7)
        self.assertEqual(r[6],167)




if __name__ == '__main__':
    unittest.main()
