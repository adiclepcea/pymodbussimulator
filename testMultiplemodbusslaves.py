import unittest
import multiplemodbusslaves

class TestSlave(unittest.TestCase):
    def init_slave_for_test(self,value):
        dReg = {}
        dReg["location"] = 10
        dReg["max"] = 122
        dReg["min"] = 0
        dReg["type"] = multiplemodbusslaves.TYPE_HOLDING
        dReg["value"] = value

        dRegCoil = {}
        dRegCoil["location"] = 20
        dRegCoil["max"] = 1
        dRegCoil["min"] = 0
        dRegCoil["type"] = multiplemodbusslaves.TYPE_COIL
        dRegCoil["value"] = value

        dRegCoil1 = {}
        dRegCoil1["location"] = 21
        dRegCoil1["max"] = 0
        dRegCoil1["min"] = 0
        dRegCoil1["type"] = multiplemodbusslaves.TYPE_COIL
        dRegCoil1["value"] = value

        dRegDiscreteInput = {}
        dRegDiscreteInput["location"] = 30
        dRegDiscreteInput["max"] = 1
        dRegDiscreteInput["min"] = 0
        dRegDiscreteInput["type"] = multiplemodbusslaves.TYPE_INPUT
        dRegDiscreteInput["value"] = value

        dSlave = {}
        dSlave["address"] = 10
        dSlave["description"] = "test_slave"
        dSlave["registries"] = []
        dSlave["registries"].append(dReg)
        dSlave["registries"].append(dRegCoil)
        dSlave["registries"].append(dRegCoil1)
        dSlave["registries"].append(dRegDiscreteInput)
        slave = multiplemodbusslaves.Slave(dSlave)
        return slave

    def test_slave_build_from_dict(self):
        slave = self.init_slave_for_test(multiplemodbusslaves.VALUE_FIXED)
        self.assertEqual(slave.address,10)
        self.assertEqual(len(slave.registries),4)
        self.assertEqual(slave.registries[0].location,10)
        self.assertEqual(slave.registries[0].max,122)
        self.assertEqual(slave.registries[0].min,0)
        self.assertEqual(slave.registries[0].type,multiplemodbusslaves.TYPE_HOLDING)

        self.assertEqual(slave.registries[1].value,multiplemodbusslaves.VALUE_FIXED)
        self.assertEqual(slave.registries[1].location,20)
        self.assertEqual(slave.registries[1].max,1)
        self.assertEqual(slave.registries[1].min,0)
        self.assertEqual(slave.registries[1].type,multiplemodbusslaves.TYPE_COIL)
        self.assertEqual(slave.registries[1].value,multiplemodbusslaves.VALUE_FIXED)

        self.assertEqual(slave.registries[2].value,multiplemodbusslaves.VALUE_FIXED)
        self.assertEqual(slave.registries[2].location,21)
        self.assertEqual(slave.registries[2].max,0)
        self.assertEqual(slave.registries[2].min,0)
        self.assertEqual(slave.registries[2].type,multiplemodbusslaves.TYPE_COIL)
        self.assertEqual(slave.registries[2].value,multiplemodbusslaves.VALUE_FIXED)

        self.assertEqual(slave.registries[3].value,multiplemodbusslaves.VALUE_FIXED)
        self.assertEqual(slave.registries[3].location,30)
        self.assertEqual(slave.registries[3].max,1)
        self.assertEqual(slave.registries[3].min,0)
        self.assertEqual(slave.registries[3].type,multiplemodbusslaves.TYPE_INPUT)
        self.assertEqual(slave.registries[3].value,multiplemodbusslaves.VALUE_FIXED)

    def test_slave_ask_values(self):
        '''test_slave_ask_values interogates the values from this slave'''
        slave = self.init_slave_for_test(multiplemodbusslaves.VALUE_FIXED)
        #length is different - should fail
        with self.assertRaises(multiplemodbusslaves.NoSuchRegistryError):
            slave.ask_values(multiplemodbusslaves.TYPE_HOLDING,10,2)
        #location is different - should fail
        with self.assertRaises(multiplemodbusslaves.NoSuchRegistryError):
            slave.ask_values(multiplemodbusslaves.TYPE_HOLDING,101,1)
        #type is different - should fail
        with self.assertRaises(multiplemodbusslaves.NoSuchRegistryError):
            slave.ask_values(multiplemodbusslaves.TYPE_COIL,10,1)
        #everything is ok. should succed
        self.assertEqual(slave.ask_values(multiplemodbusslaves.TYPE_HOLDING,10,1),[122])

        #we add another register with a different type at the next location
        dReg = {}
        dReg["length"] = 1
        dReg["location"] = 11
        dReg["max"] = 1
        dReg["min"] = 1
        dReg["type"] = multiplemodbusslaves.TYPE_COIL
        dReg["value"] = multiplemodbusslaves.VALUE_FIXED
        reg = multiplemodbusslaves.Registry(dReg)
        slave.registries.append(reg)
        #now we should get an error as the registries are not both the same type as the asked one
        with self.assertRaises(multiplemodbusslaves.NoSuchRegistryError):
            slave.ask_values(multiplemodbusslaves.TYPE_HOLDING,10,2)

        #should be ok for the seccond registry only
        self.assertEqual(slave.ask_values(multiplemodbusslaves.TYPE_COIL,11,1),[1])

        #now we fix that
        dReg["type"] = multiplemodbusslaves.TYPE_HOLDING
        reg = multiplemodbusslaves.Registry(dReg)
        slave.registries[1]=reg
        #everything should be ok
        self.assertEqual(slave.ask_values(multiplemodbusslaves.TYPE_HOLDING,10,2),[122,1])

    def test_slave_random_values(self):
        for i in range(1,100):
            slave = self.init_slave_for_test(multiplemodbusslaves.VALUE_FIXED)
            slave.registries[0].value = multiplemodbusslaves.VALUE_RANDOM
            slave.registries[0].min = 1
            slave.registries[0].max = 2
            self.assertIn(slave.ask_values(multiplemodbusslaves.TYPE_HOLDING,10,1),[[1],[2]])

    def test_slave_respond_to_request_coils_and_input(self):
        slave = self.init_slave_for_test(multiplemodbusslaves.VALUE_FIXED)
        #the last two are not important as the crc should already be checked
        #but the address must match
        response = slave.respond_to_request([0x01,0x01,0x00,0x20,0x00,0x02,0xbc,0x01])
        self.assertEqual(response,None)

        #checking for coils
        response = slave.respond_to_request([0x0A,0x01,0x00,0x14,0x00,0x02,0xfc,0xb4])
        self.assertEqual(response,[0x0A,0x01,0x01,0x01])

        slave.registries[2].max = 1
        response = slave.respond_to_request([0x0A,0x01,0x00,0x14,0x00,0x02,0xfc,0xb4])
        self.assertEqual(response,[0x0A,0x01,0x01,0x03])

        #checking for discrete inputs
        response = slave.respond_to_request([0x0A,0x02,0x00,0x1e,0x00,0x01,0x9c,0xb7])
        self.assertEqual(response,[0x0A,0x02,0x01,0x01])


if __name__ == '__main__':
    unittest.main()
