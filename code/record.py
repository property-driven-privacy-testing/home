import os, signal, time
import subprocess
import pyperclip
from util import Util
from device import Device
import demjson
from appinfo import App
from property import Event
import random
from executor import Executor
from screen import Screen
import re

class Record(object):
    instance = None
    def __init__(self,root_path,device_serial_1,device_serial_2,app_path,rule_name):
        Record.instance = self
        self.root_path=root_path
        self.device1 = Device(device_serial_1)
        self.device2 = Device(device_serial_2)
        self.app = App(app_path)
        self.util = Util(app_path)
        self.executor = Executor(self.app,self.device1,self.device2)
        self.rule_name = rule_name

    def  findkeyword(self,key,keyword):
        num1=key.find(keyword+"=")
        returnkey = key[num1+len(keyword)+2:len(key)]
        num2=returnkey.find("\"")
        if num2>-1:
            returnkey = returnkey[0:num2]
        return returnkey

    def check(self):
        print("Check Record")
        self.root_path=self.root_path+"define/"+self.app.app_name
        self.property_list=self.util.get_property(self.root_path,self.rule_name)
        
        self.device1.connect()
        self.device1.use.set_orientation("n")
        self.device2.connect()
        self.device2.use.set_orientation("n")
        self.device1.install_app(self.app.app_path)
        self.device2.install_app(self.app.app_path)

        while True:
            nowproperty = None
            name = input("Please enter the name of property, enter 'end' to stop:")
            if name == "end":
                break
            type = input("Please enter the type of property:")
            for property in self.property_list:
                if name == property.name and type == property.type:
                    nowproperty = property
                    flag = ""
                elif name == "not "+property.name and type == property.type:
                        nowproperty = property
                        flag = "not"
            if nowproperty==None:
                print("no this property")
                continue
            self.device2.stop_app(self.app)
            self.device1.stop_app(self.app)
            self.device2.start_app(self.app)
            self.device1.start_app(self.app)
            time.sleep(1)
            now_layout = 0
            for event in nowproperty.events:
                for widget in nowproperty.widgets:
                    if widget.name == event.widget:
                        nowwidget = widget
                if event.device == "2":
                    device = self.device2
                else:
                    device = self.device1
                execute_event = Event(event.action,nowwidget,event.text,event.force,device)
                if event.text == "random":
                    execute_event.set_text(self.random_text())
                nowwidget.print()
                executeresult=self.executor.execute(execute_event,0)
                if executeresult==False and event.force != False:
                    print(event.action+" "+event.widget+"fail")
                else:
                    device.use.screenshot(self.root_path+"/test.png")
                    xml = device.use.dump_hierarchy()
                    f = open(self.root_path+"/test.xml",'w',encoding='utf-8')
                    f.write(xml)
                    f = open(self.root_path+"/test.xml",'r',encoding='utf-8')
                    lines=f.readlines()
                    f.close()
                    screen = Screen(lines)
                    device.update_screen(screen)
                    now_layout=now_layout+1
                    result = self.check_property(now_layout,nowproperty,device.screen,flag)
                    if result == False:
                        print(str(nowproperty.name)+" fail")
                    
                        

    def check_property(self,layout_num,nowproperty,screen,flag):
        for condition in nowproperty.conditions:
            type = condition.type.split("::")
            if int(condition.UI_layout_num) == layout_num and type[0] == flag.strip():
                for widget in nowproperty.widgets:
                    if widget.name == condition.widget:
                        targetwidget = widget
                        break
                result = self.findview(screen,targetwidget)
                if result == False and condition.relation == "in":
                    return False
                elif result == True and condition.relation == "not in":
                    return False
        return True

    def findview(self,screen,targetwidget):
        for view in screen.allviews:
            if targetwidget.className !="" and view.className!=targetwidget.className:
                continue
            elif targetwidget.description !="" and targetwidget.description not in view.description:
                continue
            elif targetwidget.resourceId !="" and view.resourceId!=targetwidget.resourceId:
                continue
            elif targetwidget.text !="" and targetwidget.text not in view.text:
                continue
            elif targetwidget.xpath !="":
                result = self.checkxpath(view,targetwidget.xpath)
                if result == False:
                    continue
            return True
        return False

    def checkxpath(self,view,xpath):
        strinfo = re.compile('\[[0-9]*]')
        xpath = strinfo.sub('', xpath)
        num1 = xpath.find("//*[@resource-id=\"")
        xpath = xpath[num1+18:len(xpath)]
        num2 = xpath.find("\"]")
        resourceID = xpath[0:num2]
        xpath = xpath[num2+3:len(xpath)]

        xpathlist = xpath.split("/")
        now_classname = xpathlist[len(xpathlist)-1]
        if now_classname!=view.className:
            return False
        i = len(xpathlist)-2
        while i> 0:
            if xpathlist[1]!= view.father[len(view.father)-i].className:
                return False
            i=i-1
        if resourceID != view.father[len(view.father)-len(xpathlist)].resourceId:
            return False
        return True

    def start(self):
        print("Record start")
        self.root_path=self.root_path+"define/"
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)
        self.root_path=self.root_path+self.app.app_name
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)

        #Connect device and initialize
        self.device1.connect()
        # self.device1.install_app(self.app.app_path)
        self.device1.use.set_orientation("n")
        # self.device1.clear_app(self.app)
        self.device1.start_app(self.app)

        #Open the weditor to record the script
        process = subprocess.Popen(["python","-m","weditor"])
        processId = process.pid
        time.sleep(5)
        endstr = input("Please use the editor to record the script. After the recording is successful, please copy the script code, and then enter 1 in terminal to stop:")
        while endstr != "1":
            endstr = input("Please use the editor to record the script. After the recording is successful, please copy the script code, and then enter 1 in terminal to stop")
        try:
            os.kill(processId, signal.SIGTERM)
        except Exception:
            print("kill fail")

        #Parsing the recording script of weditor to obtain property
        events = []
        views = []
        conditions = []
        dd=pyperclip.paste()
        lines = dd.split("\n")
        num = 0
        for line in lines:
            if line.strip()!="":
                returnvalue=self.get_info(line,num)
                if returnvalue!=None:
                    num=num+1
                    views.append(returnvalue[0])
                    events.append(returnvalue[1])
        
        #Get and generate additional information
        type = input("Please enter the type of property:")
        name = input("Please enter the name of property:")
        conditionsnum = input("Please enter the number of conditions:")
        i = 1
        while i < int(conditionsnum)+1:
            widget = {"name":"check_widget_"+str(i),"UI_layout_num":"","text":"","resource-id":"","class":"","content-desc":"","xpath":"","instance": ""}
            views.append(widget)
            condition = {"UI_layout_num": "","relation": "","type": "","widget": "check_widget_"+str(i)}
            conditions.append(condition)
            i=i+1
            
            
        #Generate json file based on information
        data = {"widgets": views,"events":events,"name":name,"type":type,"conditions":conditions,"fragments":[]}
        json = demjson.encode(data)
        print(json)
        f = open(self.root_path+"/test.json",'w',encoding='utf-8')
        f.write(json)
        f.flush()
        f.close()
        if not os.path.exists(self.root_path+"/test.json"):
            f = open(self.root_path+"/test.json",'w',encoding='utf-8')
            aifs = {"properties":[]}
            json = demjson.encode(aifs)
            f.write(json)
            f.flush()
            f.close()


    def get_info(self,line,num):
        print("line:"+line)
        resourceId=""
        text=""
        description=""
        xpath=""
        instance=""
        action="#any#"
        className=""
        edittext=""
        if "xpath" in line:
            num1=line.find("xpath(")
            returnkey = line[num1+7:len(line)]
            num2=returnkey.find("\').")
            if num2>-1:
                returnkey = returnkey[0:num2]
            xpath = returnkey
        else:
            keys = line.split("\",")
            for key in keys:
                if "resourceId" in key:
                    keyword = "resourceId"
                    returnkey = self.findkeyword(key,keyword)
                    resourceId = returnkey
                elif "className" in key:
                    keyword = "className"
                    returnkey = self.findkeyword(key,keyword)
                    className = returnkey
                elif "text" in key:
                    keyword = "text"
                    returnkey = self.findkeyword(key,keyword)
                    text = returnkey
                elif "description" in key:
                    keyword = "description"
                    returnkey = self.findkeyword(key,keyword)
                    description = returnkey
                elif "xpath" in key:
                    keyword = "xpath"
                    returnkey = self.findkeyword(key,keyword)
                    xpath = returnkey
                elif "instance" in key:
                    keyword = "instance"
                    returnkey = self.findkeyword(key,keyword)
                    instance = returnkey
                
        if "long_click" in line:
            action = "long_click"
        elif "click" in line:
            action = "click"
        elif "set_text" in line:
            action = "edit"
            num1=line.find("set_text(")
            returnkey = line[num1+10:len(line)]
            num2=returnkey.find("\")")
            if num2>-1:
                returnkey = returnkey[0:num2]
            edittext = returnkey
        elif "drag" in line:
            action = "drag"
            num1 = line.find("drag(")
            returnkey = line[num1+5:len(line)]
            num2=returnkey.find(")")
            if num2>-1:
                returnkey = returnkey[0:num2]
            edittext = returnkey
        elif "scroll" in line:
            if "forward" in line and "vert" in line:
                action = "scroll_forward"
            elif "backward" in line and "vert" in line:
                action = "scroll_backward"
            elif "horiz" in line and "toEnd" in line:
                action = "scroll_right"
            else:
                action = "scroll_left"
        elif "send_keys" in line:
            action = "edit"
            num1=line.find("send_keys(")
            returnkey = line[num1+11:len(line)]
            num2=returnkey.find("\",")
            if num2>-1:
                returnkey = returnkey[0:num2]
            edittext = returnkey
            className = "android.widget.EditText"
        elif "press(\"back\")" in line:
            action = "back"
        
            
        print("resourceId:"+resourceId)
        print("text:"+text)
        print("description:"+description)
        print("xpath:"+xpath)
        print("action:"+action)
        print("edittext:"+edittext)
        print("******************")
        widget = {"name":"e"+str(num+1)+"_widget","UI_layout_num":str(num),"text":text,"resource-id":resourceId,"class":className,"content-desc":description,"xpath":xpath,"instance": instance}
        event = {"widget":"e"+str(num+1)+"_widget","action": action,"text": edittext,"force":True,"device":""}
        if action !="#any#":
            returnvalue = (widget,event)
            return returnvalue
        else:
            return None

    def random_text(self):
        text_style=random.randint(0,7)
        text_length=random.randint(1,5)
        nums=["0","1","2","3","4","5","6","7","8","9"]
        letters=["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
        symbols=[",",".","!","?"]
        i=0
        random_string=""
        print("text_style:"+str(text_style))
        if text_style == 0:
            while i < text_length:
                now_num=nums[random.randint(0,len(nums)-1)]
                random_string=random_string+now_num
                i=i+1
        elif text_style == 1:
            while i < text_length:
                now_letters=letters[random.randint(0,len(nums)-1)]
                random_string=random_string+now_letters
                i=i+1
        elif text_style == 2:
            while i < text_length:
                s_style=random.randint(0,2)
                if s_style==0:
                    now_letters=nums[random.randint(0,len(nums)-1)]
                    random_string=random_string+now_letters
                elif s_style==1:
                    now_letters=letters[random.randint(0,len(letters)-1)]
                    random_string=random_string+now_letters
                elif s_style==2:
                    now_letters=symbols[random.randint(0,len(symbols)-1)]
                    random_string=random_string+now_letters
                i=i+1
        elif text_style == 3:
            country=["beijing","BEIJING"]
            countrynum=random.randint(0,1)
            random_string=country[countrynum]
        elif text_style ==4:
            random_string=letters[random.randint(0,len(letters)-1)]+letters[random.randint(0,len(letters)-1)]
        elif text_style ==5:
            random_string=nums[random.randint(0,len(nums)-1)]+nums[random.randint(0,len(nums)-1)]
        elif text_style ==6:
            special_text=["www.baidu.com","www.google.com"]
            specialnum=random.randint(0,len(special_text)-1)
            random_string=special_text[specialnum]
        elif text_style ==7:
            random_string="?10086"
        if random_string=="" or random_string.startswith("?") or random_string.startswith(".") or random_string.startswith("x") or random_string.startswith("X") or random_string.startswith("0") or len(random_string)<3:
            random_string=self.random_text()
        return random_string
    