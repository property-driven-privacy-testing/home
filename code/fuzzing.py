from device import Device
from appinfo import App
from executor import Executor
from util import Util
from policy import RandomPolicy
import os
from screen import Screen
import time
from property import Event, Candidate
import re
import time
import random

class Fuzzing(object):
    instance = None
    
    def __init__(self,
                device_serial_1,
                device_serial_2,
                root_path,
                app_path,
                testcase_count,
                event_num,
                max_time,
                start_testcase,
                rule_name,
                tesseract_path):
        Fuzzing.instance = self
        self.rule_name = rule_name
        self.testcase_count = testcase_count
        self.event_num = event_num
        self.device_serial_1 = device_serial_1
        self.device_serial_2 = device_serial_2
        self.root_path = root_path
        self.device1 = Device(device_serial_1)
        self.device2 = Device(device_serial_2)
        self.app = App(app_path)
        self.util = Util(app_path)
        self.executor = Executor(self.app,self.device1,self.device2)
        self.policy_name = "random"
        self.policy =  self.get_policy()
        self.max_time =max_time
        self.start_testcase = start_testcase
        self.start_time = time.time()
        self.store_text = ""
        self.tesseract_path = tesseract_path
        self.history_final_choice =[]

    def get_policy(self):
        if self.policy_name=="random":
            print("Policy: Random")
            policy = RandomPolicy(self.device1,self.app,40,30,40,30,5,5)
        else:
            print("No valid input policy specified. Using policy \"none\".")
            policy = None
        return policy
    
    def save_screen(self,path,event_count,device):
        #get and save screen of device
        device.use.screenshot(path+"/"+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/"+str(event_count)+"_"+device.device_serial+".png")
        self.nowscreenshotpath = path+"/"+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/"+str(event_count)+"_"+device.device_serial+".png"
        xml = device.use.dump_hierarchy()
        f = open(path+"/"+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/"+str(event_count)+"_"+device.device_serial+".xml",'w',encoding='utf-8')
        f.write(xml)
        f = open(path+"/"+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/"+str(event_count)+"_"+device.device_serial+".xml",'r',encoding='utf-8')
        lines=f.readlines()
        f.close()
        screen = Screen(lines)
        device.update_screen(screen,self.nowscreenshotpath)
        
        #record crash
        f = open(path+"/"+self.app.app_name+"screen/"+device.device_serial+"_logcat.txt")
        logcat_lines=f.readlines()
        f.close()
        device.update_logcat(logcat_lines)
        if device.last_logcat!=device.now_logcat:
            for line in device.now_logcat:
                if line not in device.last_logcat:
                    self.f_event.write(line)
                    self.f_event.flush()

    def start(self,choice): 
        print("Start")

        self.proposition_list=self.util.get_proposition(self.root_path+"define/"+self.app.app_name,self.rule_name)

        self.edge_list=self.util.get_edge(self.root_path+"define/"+self.app.app_name,self.rule_name)
        self.state_list = self.util.get_state()
        
        self.automata_list = self.util.get_automata(self.root_path+"define/"+self.app.app_name,self.rule_name)
        self.automata_list_copy = self.automata_list.copy()
        
        self.controllable_proposition = self.util.get_controllableproposition(self.root_path+"define/"+self.app.app_name,self.rule_name)

        self.keyview_list=self.util.get_keyview(self.root_path+"define/"+self.app.app_name,self.rule_name)
        
        self.now_testcase =self.start_testcase
        self.root_path = self.root_path+"output/"
        self.util.create_outputdir(self.root_path)

        #Connect and initialize device
        self.device1.connect()
        self.device1.use.set_orientation("n")
        self.device2.connect()
        self.device2.use.set_orientation("n")
        # self.device1.install_app(self.app.app_path)
        # self.device2.install_app(self.app.app_path)
        self.device1.start_app(self.app)
        self.device2.start_app(self.app)

        #Initialize crash log
        self.f_logcat = open(self.root_path+self.app.app_name+"screen/"+self.device1.device_serial+"_logcat.txt",'w',encoding='utf-8')
        self.f_logcat.close()
        self.device1.log_crash(self.root_path+self.app.app_name+"screen/"+self.device1.device_serial+"_logcat.txt")
        self.f_logcat = open(self.root_path+self.app.app_name+"screen/"+self.device1.device_serial+"_logcat.txt")
        logcat_lines=self.f_logcat.readlines()
        self.f_logcat.close()
        self.device1.update_logcat(logcat_lines)
        self.f_logcat = open(self.root_path+self.app.app_name+"screen/"+self.device2.device_serial+"_logcat.txt",'w',encoding='utf-8')
        self.f_logcat.close()
        self.device2.log_crash(self.root_path+self.app.app_name+"screen/"+self.device2.device_serial+"_logcat.txt")
        self.f_logcat = open(self.root_path+self.app.app_name+"screen/"+self.device2.device_serial+"_logcat.txt")
        logcat_lines=self.f_logcat.readlines()
        self.f_logcat.close()
        self.device2.update_logcat(logcat_lines)

        #Execute different strategies based on user choice
        if choice == "guide":
            self.num = 0
            self.gap_time = 0
            self.start_time = time.time()
            self.automata_driven_testing()
        elif choice == "random":
            self.num = 0
            self.gap_time = 0
            self.start_time = time.time()
            self.random_test()
        elif choice == "mimic":
            self.num = -1
            self.start_time = time.time()
            self.gap_time = 0
            for automata in self.automata_list_copy:
                self.num = self.num +1
                self.automata_list = []
                self.automata_list.append(automata)
                self.simple_automaton_coverage_test()
            for automata in self.automata_list_copy:
                if len(automata.weak_coverage_edges) != len(automata.edges):
                    self.num = self.num +1
                    self.automata_list = []
                    self.automata_list.append(automata)
                    self.simple_automaton_coverage_test()
    
    def generate_floyd(self):
        F: float = float('inf')
        self.floyd = [[F] * len(self.state_list) for i in range(len(self.state_list))]
        self.floyd_path = [[[]] * len(self.state_list) for i in range(len(self.state_list))]
        i=0
        while i < len(self.state_list):
            
            self.floyd[i][i]=0
            self.floyd_path[i][i]=[]
            for edge in self.edge_list:
                if edge.start_state == self.state_list[i]:
                    j=0
                    while j<len(self.state_list):
                        if self.state_list[j] == edge.end_state:
                           self.floyd[i][j]=1
                           self.floyd_path[i][j]=[edge.proposition]
                           break
                        j=j+1
            i=i+1
        k=0
        while k<len(self.state_list):
            i=0
            while i < len(self.state_list):
                j=0
                while j<len(self.state_list):
                    if(self.floyd[i][k]+self.floyd[k][j] < self.floyd[i][j]): 
                        self.floyd[i][j]= self.floyd[i][k]+self.floyd[k][j]
                        self.floyd_path[i][j]= self.floyd_path[i][k].copy()+self.floyd_path[k][j].copy()
                    j=j+1
                i=i+1
            k=k+1

    def statistical_coverage(self):
        all_weak_covered_edge_num = 0
        all_strong_covered_edge_num = 0
        all_edge_num = 0
        all_automata = 0
        covered_automata_num = 0
        self.f_test_info.write("--------------Coverage Info Start--------------"+"\n")
        for automata in self.automata_list_copy:
            all_automata=all_automata+1
            weak_covered_edge_num=0
            strong_covered_edge_num=0
            edge_num=0
            for edge in automata.weak_coverage_edges:
                # self.f_test_info.write(automata.proposition+"\n")
                # self.f_test_info.write("Weak covered edge:"+edge.proposition+"\n")
                weak_covered_edge_num=weak_covered_edge_num+1
            for edge in automata.strong_coverage_edges:
                # self.f_test_info.write(automata.proposition+","+str(automata.APs)+"\n")
                # self.f_test_info.write("Strong covered edge:"+edge.proposition+"\n")
                strong_covered_edge_num=strong_covered_edge_num+1
            for edge in automata.edges:
                if edge not in automata.weak_coverage_edges and edge.start_state not in automata.finish_state:
                    self.f_test_info.write(automata.proposition+", APs:"+str(automata.APs)+", now state:"+automata.now_state+"\n")
                    self.f_test_info.write("Not covered edge:"+edge.proposition+", start state:"+edge.start_state+", end state:"+edge.end_state+"\n")
            edge_num = len(automata.edges)
            if weak_covered_edge_num==edge_num:
                covered_automata_num = covered_automata_num+1
            # self.f_test_info.write("Weak coverage of edge:"+str(weak_covered_edge_num/edge_num)+"\n")
            # self.f_test_info.write("Strong coverage of edge:"+str(strong_covered_edge_num/edge_num)+"\n")
            # self.f_test_info.write("------------------------------------"+"\n")
            all_weak_covered_edge_num = all_weak_covered_edge_num+weak_covered_edge_num
            all_strong_covered_edge_num = all_strong_covered_edge_num+strong_covered_edge_num
            all_edge_num = all_edge_num+edge_num
        self.f_test_info.write("Edge's weak coverage of all automata:"+str(all_weak_covered_edge_num/all_edge_num)+"\n")
        self.f_test_info.write("Edge's strong coverage of all automata:"+str(all_strong_covered_edge_num/all_edge_num)+"\n")
        self.f_test_info.write("Num of automata that all edge have been weak covered:"+str(covered_automata_num/all_automata)+"\n")
        self.f_test_info.write("---------------Coverage Info End---------------"+"\n") 

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
    
    def extract_text_from_image(self,image_path):
        from PIL import Image
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image, lang='eng')
        return extracted_text
    
    def check_condition(self,layout_num,nowproposition,device,randomtext):
        num = 0
        for condition in nowproposition.conditions:
            if int(condition.UI_layout_num) == layout_num and condition.type == "":
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
                if num ==0:
                    self.save_screen(self.root_path,self.now_event,device)
                    num =1
                result = self.findview(device.screen,targetwidget)
                if result == None and condition.relation == "in":
                    if targetwidget.text !="" and targetwidget.description =="" and targetwidget.resourceId =="" and targetwidget.xpath =="":
                        extracted_text = self.extract_text_from_image(device.nowscreenshotpath)
                        if targetwidget.text in extracted_text:
                            return True
                    return False
                elif result != None and condition.relation == "not in":
                    return False
                elif result != None and condition.relation == "store":
                    self.store_text = result.text
        return True

    def execute_and_check_proposition(self,nowproposition):
        self.device1.stop_app(self.app)
        self.device2.stop_app(self.app)
        self.device1.start_app(self.app)
        self.device2.start_app(self.app)

        self.now_event = self.now_event + 1
        self.save_screen(self.root_path,self.now_event,self.device1)
        self.save_screen(self.root_path,self.now_event,self.device2)
        print("Start event:"+str(self.now_event)+", execute and check "+str(nowproposition.name))
        self.f_test_info.write("Start event:"+str(self.now_event)+", execute and check "+str(nowproposition.name)+"\n")
        self.f_test_info.flush()
        layout_num = 0
        randomtext = ""
        for event in nowproposition.events:
            nowwidget = None
            for widget in nowproposition.widgets:
                if widget.name == event.widget:
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
            # self.executor.close(execute_event.device)
            executeresult=self.executor.execute(execute_event,0)
            self.f_event.write(str(self.now_event)+"::"+device.device_serial+"::"+execute_event.action+"::"+execute_event.text+"::"+execute_event.widgettoline()+"\n")
            self.f_event.flush()
            self.now_event = self.now_event + 1
            self.save_screen(self.root_path,self.now_event,device)
            layout_num = layout_num + 1
            if executeresult==False and event.force != False:
                print(event.action+" "+event.widget+"执行失败")
                self.f_test_info.write(str(self.now_event)+" execute fail: "+event.action+" "+event.widget+"\n")
                return 0
            result = self.check_condition(layout_num,nowproposition,device,randomtext)
            if result == False:
                print("End event:"+str(self.now_event)+", execute and check "+str(nowproposition.name))
                self.f_test_info.write("End event:"+str(self.now_event)+", execute and check "+str(nowproposition.name)+"\n"+"Check result:"+"not "+str(nowproposition.name)+"\n")
                return 1
        print("End event:"+str(self.now_event)+", execute and check end")
        self.f_test_info.write("End event:"+str(self.now_event)+", execute and check end"+"\n"+"Check result:"+""+str(nowproposition.name)+"\n")
        return 2

    def check_now_state(self):
        for propositionname in self.controllable_proposition:
            target_proposition = None  
            for proposition in self.proposition_list:
                if proposition.name == propositionname and proposition.type == "check":
                    target_proposition = proposition
                    break
            if target_proposition!=None and target_proposition.name not in self.true_propositions and target_proposition.name not in self.false_propositions:
                trytime = 0
                result = self.execute_and_check_proposition(target_proposition)
                while result == 0 and trytime<1:
                    result = self.execute_and_check_proposition(target_proposition)
                    trytime = trytime + 1
                if result == 0:
                    result = 1
                if result == 2 or (trytime==1 and result ==0):
                    self.true_propositions.append(proposition.name)
                else:
                    self.false_propositions.append(proposition.name)
        for state in  self.state_list:
            flag = True
            for proposition in self.true_propositions:
                if proposition not in state.controllableproposition:
                    flag = False
                    break
            if flag == True and len(state.controllableproposition) == len(self.true_propositions):
                return state
        print("wrong")
    
    def find_shortest_path(self,from_state,to_state):
        i=0
        while i<len(self.state_list)-1:
            if self.state_list[i] == from_state:
                break
            i=i+1
        j=0
        while j<len(self.state_list)-1:
            if self.state_list[j] == to_state:
                break
            j=j+1
        return self.floyd_path[i][j]

    def transition_state(self,now_state,target_proposition):
        for edge in self.edge_list:
            if now_state == edge.start_state and target_proposition.name == edge.proposition:
                # print("Now proposition: "+edge.end_state.name)
                return edge.end_state
        print("find edge wrong")

    def reach_state(self,from_state,to_state):
        target_propositions=[]
        now_state = from_state
        if from_state==to_state:
            return now_state
        target_propositions = self.find_shortest_path(from_state,to_state)
        print("Execute "+str(target_propositions)+" to from "+from_state.name+" to "+to_state.name)
        self.f_test_info.write("Execute "+str(target_propositions)+" to from "+from_state.name+" to "+to_state.name+"\n")
        self.f_test_info.flush()
        for target_proposition_name in target_propositions: 
            target_proposition = None  
            for proposition in self.proposition_list:
                if proposition.name == target_proposition_name and proposition.type == "control":
                    target_proposition = proposition
                    break
            if target_proposition!=None:
                trytime=0
                result = self.execute_and_check_proposition(target_proposition)
                while result == 0 and trytime<1:
                    result = self.execute_and_check_proposition(target_proposition)
                    trytime = trytime + 1
                if result == 2:
                    from_state = now_state
                    now_state=self.transition_state(now_state,target_proposition)
                    if now_state==None:
                        print("wrong")
                    if "not" in target_proposition.name:
                        change_proposition = target_proposition.name.replace("not ","")
                        self.false_propositions.append(change_proposition)
                        self.true_propositions.remove(change_proposition)
                    else:
                        self.true_propositions.append(target_proposition.name)
                        self.false_propositions.remove(target_proposition.name)
                    self.f_test_info.write("now propositions:"+str(self.true_propositions)+"\n")
                    self.f_test_info.write("not propositions:"+str(self.false_propositions)+"\n")
                    print("Now state:"+now_state.name +" "+str(now_state.controllableproposition))
                    self.f_test_info.write("Now state:"+now_state.name+" "+str(now_state.controllableproposition)+"\n")
                    self.f_test_info.flush()
                else:
                    print("Fail while controling proposition "+target_proposition_name)
                    self.f_test_info.write("Fail while controling proposition "+target_proposition_name+"\n")
                    self.f_test_info.flush()
                    if now_state==None:
                        print("wrong")
                    return now_state
            else:
                print("Fail, can not find event trace to control proposition "+target_proposition_name)
                self.f_test_info.write("Fail, can not find event trace to control proposition "+target_proposition_name+"\n")
                self.f_test_info.flush()
                return now_state
        return now_state
    
    def find_incidental_proposition(self,target_proposition):
        incidental_propositions = []
        for proposition in self.proposition_list:
            if proposition.name not in self.false_propositions and proposition.name not in self.true_propositions and proposition.name != target_proposition.name:
                events1 = proposition.events
                events2 = target_proposition.events
                widget1 = proposition.widgets
                widget2 = target_proposition.widgets
                flag = True
                if len(events1) !=len(events2) or len(widget1) !=len(widget2):
                    continue
                i= 0 
                while i< len(events1):
                    if events1[i].widget != events2[i].widget or events1[i].device != events2[i].device or events1[i].text != events2[i].text:
                        flag = False
                        break
                    i=i+1
                i= 0 
                while i< len(widget1):
                    if widget1[i].resourceId != widget2[i].resourceId or widget1[i].text != widget2[i].text or widget1[i].description != widget2[i].description or widget1[i].xpath != widget2[i].xpath:
                        flag = False
                        break
                    i=i+1
                if flag == True:
                    incidental_propositions.append(proposition)
        return incidental_propositions
    
    def execute_and_check_propositions(self,nowproposition,incidental_propositions):
        self.now_event = self.now_event + 1
        print("Start event:"+str(self.now_event)+", execute and check "+str(nowproposition.name))
        self.f_test_info.write("Start event:"+str(self.now_event)+", execute and check "+str(nowproposition.name)+"\n")
        self.f_test_info.flush()
        self.device1.stop_app(self.app)
        self.device2.stop_app(self.app)
        self.device1.start_app(self.app)
        self.device2.start_app(self.app)
        self.save_screen(self.root_path,self.now_event,self.device1)
        self.save_screen(self.root_path,self.now_event,self.device2)
        layout_num = 0
        randomtext = ""
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

            # self.executor.close(execute_event.device)
            executeresult=self.executor.execute(execute_event,0)
            self.f_event.write(str(self.now_event)+"::"+device.device_serial+"::"+execute_event.action+"::"+execute_event.text+"::"+execute_event.widgettoline()+"\n")
            self.f_event.flush()
            self.now_event = self.now_event + 1
            self.save_screen(self.root_path,self.now_event,device)
            layout_num = layout_num + 1
            if executeresult==False and event.force != False:
                print(event.action+" "+event.widget+"执行失败")
                self.f_test_info.write(str(self.now_event)+" execute fail: "+event.action+" "+event.widget+"\n")
                self.f_test_info.write("Check result: not "+nowproposition.name+"\n")
                return 0
            else:
                for incidental_proposition in incidental_propositions:
                    result = self.check_condition(layout_num,incidental_proposition,device,randomtext)
                    if result == False and incidental_proposition.name not in self.false_propositions:
                        self.false_propositions.append(incidental_proposition.name)
                        self.f_test_info.write("Check result: not "+incidental_proposition.name+"\n")
                        print("Check result: not "+incidental_proposition.name)
                result = self.check_condition(layout_num,nowproposition,device,randomtext)
                if result == False and nowproposition.name not in self.false_propositions:
                    self.false_propositions.append(nowproposition.name)
                    self.f_test_info.write("Check result: not "+nowproposition.name+"\n")
                    print("Check result: not "+nowproposition.name)
                    return 1
        if nowproposition.name not in self.true_propositions and nowproposition.name not in self.false_propositions:
            self.true_propositions.append(nowproposition.name)
            self.f_test_info.write("Check result: "+nowproposition.name+"\n")
            print("Check result: "+nowproposition.name)
        for incidental_proposition in incidental_propositions:
            if incidental_proposition.name not in self.false_propositions and incidental_proposition.name not in self.true_propositions:
                self.true_propositions.append(incidental_proposition.name)
                self.f_test_info.write("Check result: "+incidental_proposition.name+"\n")
                print("Check result: "+incidental_proposition.name)
        print("End event:"+str(self.now_event)+", execute and check end")
        self.f_test_info.write("End event:"+str(self.now_event)+", execute and check end"+"\n")
        return 2

    def check_satisfy(self,automata,edge,flag):
        self.f_test_info.write("now propositions:"+str(self.true_propositions)+"\n")
        self.f_test_info.write("not propositions:"+str(self.false_propositions)+"\n")
        self.f_test_info.write("edge:"+edge.proposition+"\n")
        propositions = edge.proposition
        APs = automata.APs
        or_propositions = propositions.split("|")
        or_propositions_flag = False
        for and_propositions in or_propositions:
            and_propositions_flag = True
            proposition_list = and_propositions.split("&")
            proposition_list_controllable = []
            proposition_list_uncontrollable = []
            for proposition in proposition_list:
                if proposition == "t":
                    continue
                if APs[int(proposition.replace("!",""))] in self.controllable_proposition:
                    proposition_list_controllable.append(proposition)
                else:
                    proposition_list_uncontrollable.append(proposition)
            if flag == "strong":
                proposition_list = proposition_list_controllable+proposition_list_uncontrollable
            else:
                proposition_list = proposition_list_controllable
            print(proposition_list)
            for proposition_num in proposition_list:
                notflag = ""
                if "!" in  proposition_num:
                    notflag ="not"
                proposition_num=proposition_num.replace("!","")
                proposition = APs[int(proposition_num)]
                if proposition in self.true_propositions and notflag=="not":
                    and_propositions_flag=False
                    break
                elif proposition in self.false_propositions and notflag=="":
                    and_propositions_flag=False
                    break
                elif proposition not in self.true_propositions and proposition not in self.false_propositions:
                    target_proposition = None
                    for realproposition in self.proposition_list:
                        if realproposition.name == proposition and realproposition.type == "check":
                            target_proposition = realproposition
                    if target_proposition!=None:
                        incidental_propositions=self.find_incidental_proposition(target_proposition)
                        # checkresult=self.execute_and_check_proposition(target_proposition)
                        checkresult=self.execute_and_check_propositions(target_proposition,incidental_propositions)
                        self.f_test_info.flush()
                        trytime = 0
                        while checkresult == 0 and trytime<1:
                            checkresult = self.execute_and_check_propositions(target_proposition,incidental_propositions)
                            trytime = trytime + 1
                        if checkresult==2 and notflag == "not":
                            and_propositions_flag=False
                            break
                        elif checkresult==1 and notflag == "":
                            and_propositions_flag=False
                            break
                        elif checkresult==0 and notflag == "":
                            and_propositions_flag=False
                            self.false_propositions.append(target_proposition.name)
                            break
                    else:
                        self.f_test_info.write("can not find "+proposition+"\n")
                        and_propositions_flag=False
            if and_propositions_flag == True:
                or_propositions_flag = True
                break
        return or_propositions_flag

    def automata_change(self):
        fail_automatas = []
        i=0
        while i < len(self.automata_list):
            automata = self.automata_list[i]
            for edge in automata.edges:
                if edge.start_state == automata.now_state:
                    check_weak = self.check_satisfy(automata,edge,"weak")
                    if check_weak == True:
                        if edge not in automata.weak_coverage_edges:
                            self.automata_list[i].weak_coverage_edges.append(edge)
                            self.f_test_info.write("Add weak coverage:"+self.automata_list[i].proposition+","+edge.proposition+"\n")
                            print("Add weak coverage:"+self.automata_list[i].proposition+","+edge.proposition+"\n")
                        edge.weight = edge.weight/40

                        if edge.start_state!=edge.end_state or edge not in automata.strong_coverage_edges:
                            check_strong=self.check_satisfy(self.automata_list[i],edge,"strong")
                            if check_strong == True:
                                if edge not in automata.strong_coverage_edges:
                                    self.automata_list[i].add_coverage(edge)
                                    self.f_test_info.write("Add strong coverage:"+self.automata_list[i].proposition+","+edge.proposition+"\n")
                                    print("Add strong coverage:"+self.automata_list[i].proposition+","+edge.proposition+"\n")
                                edge.weight = edge.weight/100
                                self.automata_list[i].now_state = edge.end_state
                                print(automata.proposition+" transfer to state"+automata.now_state)
                                self.f_test_info.write(automata.proposition+" transfer to state"+automata.now_state+"\n")
                                if edge.end_state in automata.finish_state and edge.proposition!="t":
                                    fail_automatas.append(automata)
            i=i+1
        return fail_automatas

    def get_adjacent_combinations(self,nowpropositions):
        list = []
        for state in self.state_list:
            diff = 0
            for nowproposition in nowpropositions:
                if nowproposition not in state.controllableproposition:
                    diff=diff+1
            for proposition in state.controllableproposition:
                if proposition not in nowpropositions:
                    diff=diff+1
            if diff ==1:
                list.append(state.controllableproposition)
        return list

    def get_combinations(self):
        list = []
        for state in self.state_list:
            list.append(state.controllableproposition)
        return list

    def check_formula(self,edge,automata):
        APs = automata.APs
        proposition_sets =[]
        propositions = edge.proposition
        if  "t" in propositions:
            return proposition_sets
        or_propositions = propositions.split("|")
        for or_proposition in or_propositions:
            and_propositions = or_proposition.split("&")
            proposition_set = []
            for proposition_num in and_propositions:
                notflag = ""
                if "!" in proposition_num:
                    notflag ="not"
                proposition_num=proposition_num.replace("!","")
                proposition = APs[int(proposition_num)]
                if proposition in self.controllable_proposition and notflag == "not":
                    proposition_set.append("not "+proposition)
                elif proposition in self.controllable_proposition and notflag == "":
                    proposition_set.append(proposition)
            if proposition_set!=[] and proposition_set not in proposition_sets:
                proposition_sets.append(proposition_set)
            elif proposition_set not in proposition_sets:
                proposition_sets.append(proposition_set)
        return proposition_sets

    def check_weak_equivalence(self,combination,edge):
        if len(edge) == 0:
            return True
        for element in edge:
            if "not" in element:
                object = element.replace("not ","")
                if object in combination:
                    return False
            elif element not in combination:
                return False
        return True
    
    def automata_driven_testing(self):
        
        self.now_testcase = -1 
        for automata in self.automata_list:
            automata.now_state = automata.start_state
        self.final_satisfied_candidates = [] 
        self.max_weight = 1 
        self.generate_floyd() 
        
        while True:

            self.now_testcase = self.now_testcase + 1
            if not os.path.exists(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)):
                os.makedirs(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase))
            self.f_test_info = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/test_info.txt",'w',encoding='utf-8')
            self.f_event = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/event_record.txt",'w',encoding='utf-8')
            
            self.f_test_info.write("Now Time:"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n")
            elapsed_time = time.time()-self.start_time-self.gap_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_test_info.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s (do not contain check proposition)".format(hours, minutes, seconds)+"so far\n")
            self.f_test_info.write("The program has run for a total of :"+str(elapsed_time)+" second (do not contain check proposition) so far\n")
            elapsed_time = time.time()-self.start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_test_info.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s ".format(hours, minutes, seconds)+"so far\n")
            self.f_test_info.write("The program has run for a total of :"+str(elapsed_time)+" second so far\n")
            
            self.statistical_coverage()
            self.now_event = 0
            self.true_propositions = []
            self.false_propositions = []
            self.f_test_info.flush()
            
            if self.now_testcase != 0 and self.max_weight<1 and random.randint(0,5)==2:
                for automata in self.automata_list:
                    automata.now_state = automata.start_state
            # elif self.final_satisfied_candidates!=[]:
            else:
                start_check_time = time.time()
                now_state = self.check_now_state()
                self.gap_time = self.gap_time+time.time()-start_check_time
                
                print("------------------------------------------")
                print("Now state:"+now_state.name+" "+str(now_state.controllableproposition))
                self.f_test_info.write("Now state:"+now_state.name+" "+str(now_state.controllableproposition)+"\n")

            if self.final_satisfied_candidates!=[]:
                print("Next propositions:"+str(final_choice))
                self.f_test_info.write("Next propositions:"+str(final_choice)+"\n")
                
                for state in self.state_list:
                    flag = True
                    for proposition in final_choice:
                        if "not" in proposition and proposition.replace("not ","") in state.controllableproposition:
                            flag = False
                            break
                        elif "not" not in proposition and proposition not in state.controllableproposition:
                            flag = False
                            break
                    if flag == True and len(state.controllableproposition) == len(final_choice):
                        next_test_state = state
                        break
                
                now_state = self.reach_state(now_state, next_test_state)
                # if now_state == next_test_state:
                    # for candidate in self.final_satisfied_candidates:
                    #     if candidate.edge not in candidate.automata.weak_coverage_edges:
                    #         candidate.automata.weak_coverage_edges.append(candidate.edge)
                    #         self.f_test_info.write("Add weak coverage:"+candidate.automata.proposition+","+candidate.edge.proposition+","+str(candidate.automata.APs)+"\n")
                    #         print("Add weak coverage:"+candidate.automata.proposition+","+candidate.edge.proposition+"\n")
                        # candidate.edge.weight = candidate.edge.weight/40
                        
            if self.now_testcase != 0 and self.final_satisfied_candidates!=[]:
                print("Now state:"+next_test_state.name+" "+str(now_state.controllableproposition))
                self.f_test_info.write("Now state:"+next_test_state.name+" "+str(now_state.controllableproposition)+"\n")
            if True:
                self.true_propositions = now_state.controllableproposition.copy()
                self.false_propositions = []
                for proposition in self.controllable_proposition:
                    if proposition not in self.true_propositions:
                        self.false_propositions.append(proposition)
                fail_automatas=self.automata_change()
                if len(fail_automatas)>0:
                    for automata in fail_automatas:
                        print("proposition "+automata.proposition+" reach accept state")
                        print("now propositions:"+str(self.true_propositions))
                        print("not propositions:"+str(self.false_propositions))
                        self.f_test_info.write("proposition "+automata.proposition+" reach accept state"+"\n")
                        self.f_test_info.write("now propositions:"+str(self.true_propositions)+"\n")
                        self.f_test_info.write("not propositions:"+str(self.false_propositions)+"\n")
                else:
                    self.f_test_info.write("No automata reach accept state\n")

            self.save_screen(self.root_path,self.now_event,self.device1)
            self.save_screen(self.root_path,self.now_event,self.device2)
            self.device1.start_app(self.app)
            self.device2.start_app(self.app)
            # ran = random.randint(0,10)
            # while ran != 5:
            #     self.random_execute(self.device1)
            #     self.random_execute(self.device2)
            #     ran = random.randint(0,10)
            
            all_candidates = []
            for automata in self.automata_list:
                next_edges = automata.find_next_edges()
                candidates = []
                for edge in next_edges:
                    edge_control_propositions_list = self.check_formula(edge,automata)
                    candidate = Candidate(automata,edge,edge_control_propositions_list)
                    if candidate not in candidates:
                        candidates.append(candidate)
                        self.f_test_info.write("Candidate:"+automata.proposition+","+edge.proposition+","+str(edge_control_propositions_list)+","+str(edge.weight)+"\n")
                all_candidates= all_candidates+candidates
            max_weight = 0
            final_choice = []
            self.final_satisfied_candidates = []
            combinations = self.get_adjacent_combinations(now_state.controllableproposition)
            for combination in combinations:
                candidate_count = 0
                satisfied_candidates = []
                if combination in self.history_final_choice:
                    debuff  = 10
                else:
                    debuff = 1
                for candidate in all_candidates:
                    for edge in candidate.control_propositions:
                        if self.check_weak_equivalence(combination,edge):
                            candidate_count = candidate_count+candidate.edge.weight/debuff
                            satisfied_candidates.append(candidate)
                            if candidate_count>max_weight:
                                final_choice = combination
                                max_weight = candidate_count
                                self.final_satisfied_candidates = satisfied_candidates.copy()
                            break
            for candidate in self.final_satisfied_candidates:
                self.f_test_info.write("Final Candidate:"+candidate.automata.proposition+","+candidate.edge.proposition+","+str(candidate.control_propositions)+","+str(candidate.edge.weight)+"\n")
            self.history_final_choice.append(final_choice)
            self.f_test_info.write("Final choice:"+str(final_choice)+","+str(max_weight)+"\n")
            self.f_test_info.flush()
            for automata in self.automata_list:
                self.f_test_info.write(str(automata.proposition)+":")
                for edge in automata.weak_coverage_edges:
                    self.f_test_info.write(edge.proposition)
                self.f_test_info.write("\n")
            self.f_test_info.flush()

    def simple_automaton_coverage_test(self):
        notend = True
        self.now_testcase = -1 
        for automata in self.automata_list:
            automata.now_state = automata.start_state
        self.final_satisfied_candidates = [] 
        self.max_weight = 1 
        self.generate_floyd() 
        while notend:

            self.now_testcase = self.now_testcase + 1
            if not os.path.exists(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)):
                os.makedirs(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase))
            self.f_test_info = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/test_info.txt",'w',encoding='utf-8')
            self.f_event = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/event_record.txt",'w',encoding='utf-8')
            
            self.f_test_info.write("Now Time:"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n")
            elapsed_time = time.time()-self.start_time-self.gap_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_test_info.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s (do not contain check proposition)".format(hours, minutes, seconds)+"so far\n")
            if hours>12:
                notend =False
            self.f_test_info.write("The program has run for a total of :"+str(elapsed_time)+" second (do not contain check proposition) so far\n")
            elapsed_time = time.time()-self.start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_test_info.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s ".format(hours, minutes, seconds)+"so far\n")
            self.f_test_info.write("The program has run for a total of :"+str(elapsed_time)+" second so far\n")
            
            self.statistical_coverage()
            self.now_event = 0
            self.true_propositions = [] 
            self.false_propositions = [] 
            self.f_test_info.flush()

            if self.now_testcase != 0 and self.final_satisfied_candidates==[]:
                return
            elif self.final_satisfied_candidates!=[]:
                start_check_time = time.time()
                now_state = self.check_now_state()
                self.gap_time = self.gap_time+time.time()-start_check_time
                print("------------------------------------------")
                print("Now state:"+now_state.name+" "+str(now_state.controllableproposition))
                self.f_test_info.write("Now state:"+now_state.name+" "+str(now_state.controllableproposition)+"\n")
                print("Next propositions:"+str(final_choice))
                self.f_test_info.write("Next propositions:"+str(final_choice)+"\n")
                for state in self.state_list:
                    flag = True
                    for proposition in final_choice:
                        if "not" in proposition and proposition.replace("not ","") in state.controllableproposition:
                            flag = False
                            break
                        elif "not" not in proposition and proposition not in state.controllableproposition:
                            flag = False
                            break
                    if flag == True and len(state.controllableproposition) == len(final_choice):
                        next_test_state = state
                        break
                now_state = self.reach_state(now_state, next_test_state)
                if now_state == next_test_state:
                    for candidate in self.final_satisfied_candidates:
                        if candidate.edge not in candidate.automata.weak_coverage_edges:
                            candidate.automata.weak_coverage_edges.append(candidate.edge)
                            self.f_test_info.write("Add weak coverage:"+candidate.automata.proposition+","+candidate.edge.proposition+","+str(candidate.automata.APs)+"\n")
                            print("Add weak coverage:"+candidate.automata.proposition+","+candidate.edge.proposition+"\n")
                        candidate.edge.weight = 0
                else:
                    print("something wrong")

            if self.now_testcase != 0 and self.final_satisfied_candidates!=[]:
                print("Now state:"+next_test_state.name+" "+str(now_state.controllableproposition))
                self.f_test_info.write("Now state:"+next_test_state.name+" "+str(now_state.controllableproposition)+"\n")
                
                fail_automatas=self.automata_change()
                if len(fail_automatas)>0:
                    for automata in fail_automatas:
                        print("proposition "+automata.proposition+" reach accept state")
                        print("now propositions:"+str(self.true_propositions))
                        print("not propositions:"+str(self.false_propositions))
                        self.f_test_info.write("proposition "+automata.proposition+" reach accept state"+"\n")
                        self.f_test_info.write("now propositions:"+str(self.true_propositions)+"\n")
                        self.f_test_info.write("not propositions:"+str(self.false_propositions)+"\n")
                else:
                    self.f_test_info.write("No automata reach accept state\n")
            
            all_candidates = []
            for automata in self.automata_list:
                
                next_edges = automata.find_next_edges_not_covered()
                candidates = []
                for edge in next_edges:
                    edge_control_propositionss = self.check_formula(edge,automata)
                    for control_propositions in edge_control_propositionss:
                        candidate = Candidate(automata,edge,control_propositions)
                        if candidate not in candidates and len(control_propositions)>0:
                            candidates.append(candidate)
                            self.f_test_info.write("Candidate:"+automata.proposition+","+edge.proposition+","+str(control_propositions)+"\n")
                all_candidates= all_candidates+candidates
            self.max_count = 0
            final_choice = []
            self.final_satisfied_candidates = []
            combinations = self.get_combinations()
            for combination in combinations:
                candidate_count = 0
                satisfied_candidates = []
                for candidate in all_candidates:
                    edge = candidate.control_propositions
                    if self.check_weak_equivalence(combination,edge):
                        candidate_count = candidate_count+candidate.edge.weight
                        satisfied_candidates.append(candidate)
                    if candidate_count>self.max_count:
                        final_choice = combination
                        self.max_count = candidate_count
                        self.final_satisfied_candidates = satisfied_candidates.copy()
            for candidate in self.final_satisfied_candidates:
                self.f_test_info.write("Final Candidate:"+candidate.automata.proposition+","+candidate.edge.proposition+","+str(candidate.control_propositions)+"\n")

            self.f_test_info.write("Final choice:"+str(final_choice)+"\n")
            self.f_test_info.flush()
            for automata in self.automata_list:
                self.f_test_info.write(str(automata.proposition)+":")
                for edge in automata.weak_coverage_edges:
                    self.f_test_info.write(edge.proposition)
                self.f_test_info.write("\n")
            self.f_test_info.flush()



    def random_execute(self,device):
        event = self.policy.choice_event(device,self.now_event,False,self.keyview_list)
        execute_result=self.executor.execute_event(device,event,0)
        if execute_result == True:
            if event.action == "edit":
                device.close_keyboard()
            time.sleep(1)
            #Waiting for loading
            waittime = 0
            while waittime<10 and (device.use(className="android.widget.ProgressBar",packageName=self.app.package_name).exists and self.app.package_name!="com.ss.android.lark"):
                time.sleep(1)
                waittime=waittime+1
            #Add the count of events and take a screenshot
            self.now_event = self.now_event + 1
            self.save_screen(self.root_path,self.now_event,device)
            #Record event
            if event.view!=None:
                self.f_event.write(str(self.now_event)+"::"+event.action+"::"+event.text+"::"+event.view.line+"\n")
            else:
                self.f_event.write(str(self.now_event)+"::"+event.action+"\n")
            self.f_event.flush()
        else:
            self.save_screen(self.root_path,self.now_event,device)
            
    def random_test(self):

        self.now_testcase = -1 
        for automata in self.automata_list:
            automata.now_state = automata.start_state
        self.final_satisfied_candidates = [] 
        self.max_weight = 1 
        
        while True:

            self.now_testcase = self.now_testcase + 1
            if not os.path.exists(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)):
                os.makedirs(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase))
            self.f_test_info = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/test_info.txt",'w',encoding='utf-8')
            self.f_event = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/event_record.txt",'w',encoding='utf-8')
            
            self.f_test_info.write("Now Time:"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n")
            elapsed_time = time.time()-self.start_time-self.gap_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_test_info.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s (do not contain check proposition)".format(hours, minutes, seconds)+"so far\n")
            self.f_test_info.write("The program has run for a total of :"+str(elapsed_time)+" second (do not contain check proposition) so far\n")
            elapsed_time = time.time()-self.start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_test_info.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s ".format(hours, minutes, seconds)+"so far\n")
            self.f_test_info.write("The program has run for a total of :"+str(elapsed_time)+" second so far\n")
            
            self.statistical_coverage()
            self.now_event = 0
            self.true_propositions = [] 
            self.false_propositions = [] 
            self.f_test_info.flush()

            self.save_screen(self.root_path,self.now_event,self.device1)
            self.save_screen(self.root_path,self.now_event,self.device2)
            self.device1.start_app(self.app)
            self.device2.start_app(self.app)
            ran = 0
            while ran < 50:
                ran= ran+1
                self.random_execute(self.device1)
                self.random_execute(self.device2)
            
            if random.randint(0,50)==2:
                for automata in self.automata_list:
                    automata.now_state = automata.start_state

            start_check_time = time.time()
            now_state = self.check_now_state()
            self.gap_time = self.gap_time+time.time()-start_check_time
            
            print("------------------------------------------")
            print("Now state:"+now_state.name+" "+str(now_state.controllableproposition))
            self.f_test_info.write("Now state:"+now_state.name+" "+str(now_state.controllableproposition)+"\n")
            
            if self.now_testcase != 0:
                print("Now state:"+now_state.name+" "+str(now_state.controllableproposition))
                self.f_test_info.write("Now state:"+now_state.name+" "+str(now_state.controllableproposition)+"\n")
                self.true_propositions = now_state.controllableproposition.copy()
                self.false_propositions = []
                for proposition in self.controllable_proposition:
                    if proposition not in self.true_propositions:
                        self.false_propositions.append(proposition)
                fail_automatas=self.automata_change()
                if len(fail_automatas)>0:
                    for automata in fail_automatas:
                        print("proposition "+automata.proposition+" reach accept state")
                        print("now propositions:"+str(self.true_propositions))
                        print("not propositions:"+str(self.false_propositions))
                        self.f_test_info.write("proposition "+automata.proposition+" reach accept state"+"\n")
                        self.f_test_info.write("now propositions:"+str(self.true_propositions)+"\n")
                        self.f_test_info.write("not propositions:"+str(self.false_propositions)+"\n")
                else:
                    self.f_test_info.write("No automata reach accept state\n")
            
            