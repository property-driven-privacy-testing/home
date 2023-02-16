from generate import Generate
from device import Device
import os
from record import Record
from fuzzing import Fuzzing


class PropertyTester(object):
    instance = None
    def __init__(self,device_serial_1,
        device_serial_2,
        root_path,
        app_path,
        choice,
        testcase_count,
        start_testcase,
        event_num,
        max_time,
        rule_name):
        
        PropertyTester.instance = self
        self.app_path = app_path
        self.root_path = root_path
        self.device_serial_1, = device_serial_1,
        self.device_serial_2, = device_serial_2,
        self.choice = choice
        self.testcase_count = testcase_count
        self.start_testcase = start_testcase
        self.event_num = event_num
        self.max_time = max_time
        self.rule_name = rule_name

    def start(self):
        if self.choice=="0":
            self.screenshot(self.device_serial_1)
        elif self.choice=="1":
            self.record = Record(self.root_path,self.device_serial_1,self.device_serial_2,self.app_path,self.rule_name)
            self.record.start()
        elif self.choice=="2":
            self.record = Record(self.root_path,self.device_serial_1,self.device_serial_2,self.app_path,self.rule_name)
            self.record.check()
        elif self.choice=="3" or self.choice=="4" or self.choice=="5":
            self.fuzzing = Fuzzing(self.device_serial_1,self.device_serial_2,self.root_path,self.app_path,self.testcase_count,self.event_num,self.max_time,self.start_testcase,self.rule_name)
            self.fuzzing.start(self.choice)
        elif self.choice=="6":
            self.generate = Generate(self.root_path,self.app_path,self.rule_name)
            self.generate.start()
        
    def screenshot(self,device_serial):
        if not os.path.exists(self.root_path+"output/"):
            os.makedirs(self.root_path+"output/")
        device = Device(device_serial,)
        device.connect()
        device.use.screenshot(self.root_path+"output/"+device_serial+".png")
        xml = device.use.dump_hierarchy()
        f = open(self.root_path+"output/"+device_serial+".xml",'w',encoding='utf-8')
        f.write(xml)

    def stop(self):
        self.enabled = False
