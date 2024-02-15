import os, signal, time
import subprocess
import pyperclip
from util import Util
from device import Device
import demjson
from appinfo import App
from property import Event
from executor import Executor
from screen import Screen
import re
from policy import RandomPolicy


class Record(object):
    instance = None
    def __init__(self,root_path,device_serial_1,device_serial_2,app_path,rule_name,tesseract_path):
        Record.instance = self
        self.root_path=root_path
        self.device1 = Device(device_serial_1)
        self.device2 = Device(device_serial_2)
        self.app = App(app_path)
        self.util = Util(app_path)
        self.executor = Executor(self.app,self.device1,self.device2)
        self.rule_name = rule_name
        self.policy = RandomPolicy(self.device1,self.app,40,30,40,30,5,5)
        self.store_text = ""
        self.tesseract_path = tesseract_path

    def findkeyword(self,key,keyword):
        num1=key.find(keyword+"=")
        returnkey = key[num1+len(keyword)+2:len(key)]
        num2=returnkey.find("\"")
        if num2>-1:
            returnkey = returnkey[0:num2]
        return returnkey
    
    def screenshot(self,device):
        device.use.screenshot(self.root_path+"/test.png")
        xml = device.use.dump_hierarchy()
        f = open(self.root_path+"/test.xml",'w',encoding='utf-8')
        f.write(xml)
        f = open(self.root_path+"/test.xml",'r',encoding='utf-8')
        lines=f.readlines()
        f.close()
        screen = Screen(lines)
        device.update_screen(screen,self.root_path+"/test.png")

    def check(self):
        print("Check Record")
        self.root_path=self.root_path+"define/"+self.app.app_name
        self.proposition_list=self.util.get_proposition(self.root_path,self.rule_name)
        
        #Connect device and initialize
        self.device1.connect()
        self.device1.use.set_orientation("n")
        self.device2.connect()
        self.device2.use.set_orientation("n")
        

        #Given propositions to verify
        while True:
            nowproposition = None
            name = input("Please enter the name of proposition, enter 'end' to stop:")
            if name == "end":
                break
            type = input("Please enter the type of proposition:")
            for proposition in self.proposition_list:
                if name == proposition.name and type == proposition.type:
                    nowproposition = proposition
                    flag = ""
            if nowproposition==None:
                print("No matching proposition name")
                continue
            self.device2.stop_app(self.app)
            self.device1.stop_app(self.app)
            self.device2.start_app(self.app)
            self.device1.start_app(self.app)
            self.screenshot(self.device2)
            self.screenshot(self.device1)
            time.sleep(1)
            now_layout = 0
            randomtext=""
            for event in nowproposition.events:
                nowwidget = None
                for widget in nowproposition.widgets:
                    if widget.name == event.widget and ("special" not in widget.name or event.text in widget.text or event.text in widget.resourceId):
                        nowwidget = widget
                        nowwidget.print()
                if event.device == "2":
                    device = self.device2
                else:
                    device = self.device1
                execute_event = Event(event.action,nowwidget,event.text,event.force,device)
                if event.text == "random":
                    randomtext = self.policy.random_text()
                    execute_event.set_text(randomtext)
                executeresult=self.executor.execute(execute_event,0)
                if executeresult==False and event.force != False:
                    print(event.action+" "+event.widget+"execute fail")
                    now_layout=now_layout+1
                else:
                    self.screenshot(device)
                    now_layout=now_layout+1
                    self.check_condition(now_layout,nowproposition,device,flag,randomtext)

    def extract_text_from_image(self,image_path):
        from PIL import Image
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image, lang='eng')
        return extracted_text
                    
    def check_condition(self,layout_num,nowproposition,device,flag,randomtext):
        for condition in nowproposition.conditions:
            type = condition.type.split("::")
            if int(condition.UI_layout_num) == layout_num and type[0] == flag.strip():
                for widget in nowproposition.widgets:
                    if widget.name == condition.widget:
                        import copy
                        targetwidget = copy.copy(widget)
                        if targetwidget.text == "store::random":
                            targetwidget.text= randomtext
                        if targetwidget.text == "store::store":
                            targetwidget.text= self.store_text
                        if targetwidget.description == "store::random":
                            targetwidget.description= randomtext
                        break
                result = self.findview(device.screen,targetwidget)
                if result == None and condition.relation == "in":
                    if targetwidget.text !="" and targetwidget.description =="":
                        extracted_text = self.extract_text_from_image(device.nowscreenshotpath)
                        if targetwidget.text in extracted_text:
                            print(str(nowproposition.name)+" check result: true")
                            return True
                    print(str(nowproposition.name)+" check result: false")
                    return False
                elif result != None and condition.relation == "not in":
                    print(str(nowproposition.name)+" check result: false")
                    return False
                elif result != None and condition.relation == "store":
                    self.store_text = result.text
                else:
                    print(str(nowproposition.name)+" check result: true")
        return True

    def findview(self,screen,targetwidget):
        for view in screen.allviews:
            import unicodedata
            text2 = unicodedata.normalize('NFKC', view.text)
            text2 = ''.join(c for c in text2 if c.isalnum())
            if targetwidget.resourceId !="" and view.resourceId==targetwidget.resourceId:
                print()
            if targetwidget.className !="" and view.className!=targetwidget.className:
                continue
            elif targetwidget.description !="" and targetwidget.description not in view.description:
                continue
            elif targetwidget.resourceId !="" and view.resourceId!=targetwidget.resourceId:
                continue
            elif targetwidget.text !="" and (targetwidget.text not in view.text and targetwidget.text not in text2):
                continue
            elif targetwidget.xpath !="" and "::" not in targetwidget.xpath:
                result = self.checkxpath(view,targetwidget.xpath)
                if result == False:
                    continue
            elif targetwidget.xpath !="" and "::" in targetwidget.xpath:
                items = targetwidget.xpath.split("**")
                flag = True
                for item in items: 
                    attribute = item.split("::")
                    if attribute[0]=="checked" and view.checked!=attribute[1]:
                        flag = False
                    if attribute[0]=="enabled" and view.enabled!=attribute[1]:
                        flag = False
                    if attribute[0]=="ymin" and view.ymin!=attribute[1]:
                        flag = False
                    if attribute[0]=="xmin" and view.xmin!=attribute[1]:
                        flag = False
                if flag == False:
                    continue
            return view
        return None
    
    def string_to_unicode(self,string):
        unicode_string=""
        for char in string:
            unicode_char = "\\u" + format(ord(char), "x").zfill(4)
            unicode_string += unicode_char
        return unicode_string

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
    
    def start(self,choice):
        print("Record start")
        self.root_path=self.root_path+"define/"
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)
        self.root_path=self.root_path+self.app.app_name
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)

        #Connect device and initialize
        self.device1.connect()
        self.device1.install_app(self.app.app_path)
        self.device1.use.set_orientation("n")
        # self.device1.clear_app(self.app)
        self.device1.start_app(self.app)

        if choice == "record p":
            self.record_prpposition()
        elif choice == "record f":
            self.record_fragment()

    def record_fragment(self):
        #Open the weditor to record the script
        process = subprocess.Popen(["python","-m","weditor"])
        processId = process.pid
        # time.sleep(5)
        endstr = input("请使用weditor录制片段的步骤，录制成功后请复制脚本代码，然后在terminal中输入1停止:")
        while endstr != "1":
            endstr = input("请使用weditor录制片段的步骤，录制成功后请复1制脚本代码，然后在terminal中输入1停止:")
        try:
            os.kill(processId, signal.SIGTERM)
        except Exception:
            print("kill fail")

        #Parsing the recording script of weditor to obtain proposition
        events = []
        views = []
        dd=pyperclip.paste()
        lines = dd.split("\n")
        num = 0
        for line in lines:
            if line.strip()!="":
                returnvalue=self.get_info(line,num,"f")
                if returnvalue!=None:
                    num=num+1
                    views.append(returnvalue[0])
                    events.append(returnvalue[1])

        #Get and generate additional information
        name = input("Please enter the name of fragment:")
        #Generate json file based on information

        import json
        data = {"widgets": views,"events":events,"name":name}
        text = json.dumps(data)
        print(text)
        f = open(self.root_path+"/test.json",'w',encoding='utf-8')
        f.write(text)
        f.flush()
        f.close()
        if not os.path.exists(self.root_path+"/"+self.rule_name+"proposition.json"):
            f = open(self.root_path+"/"+self.rule_name+"proposition.json",'w',encoding='utf-8')
            aifs = {"propositions":[],"fragments":[]}
            text = json.dumps(aifs)
            f.write(text)
            f.flush()
            f.close()

    def record_prpposition(self):
        
        #Open the weditor to record the script
        process = subprocess.Popen(["python","-m","weditor"])
        processId = process.pid
        # time.sleep(5)
        endstr = input("Please use the weditor to record the steps for the proposition. After successful recording, please copy the script code and enter 1 in the terminal to stop:")
        while endstr != "1":
            endstr = input("Please use the weditor to record the steps for the proposition. After successful recording, please copy the script code and enter 1 in the terminal to stop:")
        try:
            os.kill(processId, signal.SIGTERM)
        except Exception:
            print("kill fail")

        #Parsing the recording script of weditor to obtain proposition
        events = []
        views = []
        conditions = []
        fragments = []
        dd=pyperclip.paste()
        lines = dd.split("\n")
        num = 0
        for line in lines:
            if line.strip()!="":
                returnvalue=self.get_info(line,num,"p")
                if returnvalue!=None:
                    num=num+1
                    views.append(returnvalue[0])
                    events.append(returnvalue[1])
        
        #Get and generate additional information
        type = input("Please enter the type of proposition:")
        name = input("Please enter the name of proposition:")
        print("---------------------------------")
        conditionsnum = input("Please enter the number of conditions:")
        i = 1
        while i < int(conditionsnum)+1:
            check_text = input("Please enter the text of check widget:")
            check_description = input("Please enter the description of check widget:")
            widget = {"name":"check_widget_"+str(i),"UI_layout_num":"","text":check_text,"resource-id":"","class":"","content-desc":check_description,"xpath":"","instance": ""}
            views.append(widget)
            UI_layout_num = input("Please enter the UI_layout_num of condition:")
            relation = input("Please enter the relation of condition (\"in\" or \"not in\":")
            condition = {"UI_layout_num": UI_layout_num,"relation": relation,"type": "","widget": "check_widget_"+str(i)}
            conditions.append(condition)
            i=i+1
        print("---------------------------------")
        fragmentsnum = input("Please enter the number of refrence fragment:")

        i = 0
        while i < int(fragmentsnum):
            order_num = i
            frag_name = input("Please enter the name of the reference fragment:")
            frag_argsnum = input("Please enter the number of the args:")
            frag_args = []
            j = 1
            while j < int(frag_argsnum)+1:
                arg = input("Please enter "+str(j)+" arg:")
                frag_args.append(arg)
                j=j+1
            fragment = {"order_num": order_num,"name": frag_name,"args": frag_args}
            fragments.append(fragment)
            i=i+1
        import json
        
        #Generate json file based on information
        data = {"widgets": views,"events":events,"name":name,"type":type,"conditions":conditions,"fragments":fragments}
        json = json.dumps(data)
        print(json)
        f = open(self.root_path+"/test.json",'w',encoding='utf-8')
        f.write(json)
        f.flush()
        f.close()
        if not os.path.exists(self.root_path+"/test.json"):
            f = open(self.root_path+"/test.json",'w',encoding='utf-8')
            aifs = {"propositions":[]}
            json = json.dumps(aifs)
            f.write(json)
            f.flush()
            f.close()


    def get_info(self,line,num,flag):
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
            action = "longclick"
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
        if flag == "f":
            event = {"widget":"e"+str(num+1)+"_widget","action": action,"text": edittext,"force":True,"device":"args[0]"}
        if action !="#any#":
            returnvalue = (widget,event)
            return returnvalue
        else:
            return None
    