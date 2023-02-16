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
from threading import Timer
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
                rule_name):
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
        device.update_screen(screen)
        
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
        self.property_list=self.util.get_property(self.root_path+"define/"+self.app.app_name,self.rule_name)
        self.edge_list=self.util.get_edge(self.root_path+"define/"+self.app.app_name,self.rule_name)
        self.stateproperty_list = self.util.get_state()
        self.automata_list = self.util.get_automata(self.root_path+"define/"+self.app.app_name,self.rule_name)
        self.automata_list2 = self.automata_list.copy()
        self.all_controlproperties = self.util.get_allcontrolproperties(self.root_path+"define/"+self.app.app_name,self.rule_name)
        self.now_testcase =self.start_testcase
        self.root_path = self.root_path+"output/"
        self.util.create_outputdir(self.root_path)

        #Connect device and initialize
        self.device1.connect()
        self.device1.use.set_orientation("n")
        self.device2.connect()
        self.device2.use.set_orientation("n")
        self.device1.install_app(self.app.app_path)
        self.device2.install_app(self.app.app_path)
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

        #Execute different test strategies according to user selection
        if choice == "3":
            self.num = 0
            self.gap_time = 0
            self.start_time = time.time()
            self.automata_coverage_test()
        elif choice == "4":
            self.num = 0
            self.gap_time = 0
            self.start_time = time.time()
            self.random_test()
        elif choice == "5":
            self.num = -1
            self.start_time = time.time()
            self.gap_time = 0
            for automata in self.automata_list2:
                self.num = self.num +1
                self.automata_list = []
                self.automata_list.append(automata)
                self.automata_coverage_test()
    def stop(self):
        self.enabled = False
            
    def automata_coverage_test(self):
        notend = True
        self.now_testcase = -1
        for automata in self.automata_list:
            automata.now_state = automata.start_state
        self.final_satisfied_candidates = []
        self.max_count = 1
        self.generate_floyd()
        while notend:
            
            self.now_testcase = self.now_testcase + 1
            if not os.path.exists(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)):
                os.makedirs(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase))
            self.f_property = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/property_record.txt",'w',encoding='utf-8')
            self.f_event = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/event_record.txt",'w',encoding='utf-8')
            self.f_property.write("Now Time:"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n")
            elapsed_time = time.time()-self.start_time-self.gap_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_property.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s (do not contain check property)".format(hours, minutes, seconds)+"so far\n")
            self.f_property.write("The program has run for a total of :"+str(elapsed_time)+" second (do not contain check property) so far\n")
            elapsed_time = time.time()-self.start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_property.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s ".format(hours, minutes, seconds)+"so far\n")
            self.f_property.write("The program has run for a total of :"+str(elapsed_time)+" second so far\n")
            self.statistical_coverage()
            self.now_event = 0
            self.now_properties = []
            self.not_properties = []
            self.f_property.flush()
            
            #change state
            if self.now_testcase != 0 and self.max_count<1 and random.randint(0,10)==5:
                for automata in self.automata_list:
                    automata.now_state = automata.start_state
            elif self.final_satisfied_candidates!=[]:
                start_check_time = time.time()
                now_state = self.check_now_state()
                self.gap_time = self.gap_time+time.time()-start_check_time
                print("------------------------------------------")
                print("Now state:"+now_state.name+" "+str(now_state.controlproperties))
                self.f_property.write("Now state:"+now_state.name+" "+str(now_state.controlproperties)+"\n")
                print("Next properties:"+str(final_choice))
                self.f_property.write("Next properties:"+str(final_choice)+"\n")
                for state in self.stateproperty_list:
                    flag = True
                    for property in final_choice:
                        if "not" in property and property.replace("not ","") in state.controlproperties:
                            flag = False
                            break
                        elif "not" not in property and property not in state.controlproperties:
                            flag = False
                            break
                    if flag == True and len(state.controlproperties) == len(final_choice):
                        next_test_state = state
                        break
                #reach state
                now_state = self.reach_state(now_state, next_test_state)
                if now_state == next_test_state:
                    for candidate in self.final_satisfied_candidates:
                        if candidate.edge not in candidate.automata.weak_coverge_edges:
                            candidate.automata.weak_coverge_edges.append(candidate.edge)
                            self.f_property.write("Add weak coverge:"+candidate.automata.property+","+candidate.edge.property+","+str(candidate.automata.APs)+"\n")
                            print("Add weak coverge:"+candidate.automata.property+","+candidate.edge.property+"\n")
                        candidate.edge.weight = candidate.edge.weight/40
                        
            #check properties
            if self.now_testcase != 0 and self.final_satisfied_candidates!=[]:
                print("Now state:"+next_test_state.name+" "+str(now_state.controlproperties))
                self.f_property.write("Now state:"+next_test_state.name+" "+str(now_state.controlproperties)+"\n")
                self.now_properties = now_state.controlproperties.copy()
                self.not_properties = []
                for property in self.all_controlproperties:
                    if property not in self.now_properties:
                        self.not_properties.append(property)
                #detect bugs
                fail_automatas=self.automata_change()
                if len(fail_automatas)>0:
                    for automata in fail_automatas:
                        print("Property "+automata.property+" reach accept state")
                        print("now properties:"+str(self.now_properties))
                        print("not properties:"+str(self.not_properties))
                        self.f_property.write("Property "+automata.property+" reach accept state"+"\n")
                        self.f_property.write("now properties:"+str(self.now_properties)+"\n")
                        self.f_property.write("not properties:"+str(self.not_properties)+"\n")
                else:
                    self.f_property.write("No automata reach accept state\n")
            
            #select next state
            all_candidates = []
            for automata in self.automata_list:
                next_edges = automata.find_next_edges()
                candidates = []
                for edge in next_edges:
                    edge_control_propertiess = self.check_formula(edge,automata)
                    for control_properties in edge_control_propertiess:
                        candidate = Candidate(automata,edge,control_properties)
                        if candidate not in candidates and len(control_properties)>0:
                            candidates.append(candidate)
                            self.f_property.write("Candidate:"+automata.property+","+edge.property+","+str(control_properties)+"\n")
                all_candidates= all_candidates+candidates

            max_count = 0
            final_choice = []
            self.final_satisfied_candidates = []
            combinations = self.get_combinations()
            for combination in combinations:
                candidate_count = 0
                satisfied_candidates = []
                for candidate in all_candidates:
                    edge = candidate.control_properties
                    if self.check_weak_equivalence(combination,edge):
                        candidate_count = candidate_count+candidate.edge.weight
                        satisfied_candidates.append(candidate)
                    if candidate_count>max_count:
                        final_choice = combination
                        max_count = candidate_count
                        self.final_satisfied_candidates = satisfied_candidates.copy()
            for candidate in self.final_satisfied_candidates:
                self.f_property.write("Final Candidate:"+candidate.automata.property+","+candidate.edge.property+","+str(candidate.control_properties)+"\n")

            self.f_property.write("Final choice:"+str(final_choice)+"\n")
            self.f_property.flush()
            for automata in self.automata_list:
                self.f_property.write(str(automata.property)+":")
                for edge in automata.weak_coverge_edges:
                    self.f_property.write(edge.property)
                self.f_property.write("\n")
            self.f_property.flush()

    def statistical_coverage(self):
        all_weak_covered_edge_num = 0
        all_strong_covered_edge_num = 0
        all_edge_num = 0
        all_automata = 0
        covered_automata_num = 0
        self.f_property.write("--------------Coverage Info Start--------------"+"\n")
        for automata in self.automata_list2:
            all_automata=all_automata+1
            weak_covered_edge_num=0
            strong_covered_edge_num=0
            edge_num=0
            for edge in automata.weak_coverge_edges:
                # self.f_property.write(automata.property+"\n")
                # self.f_property.write("Weak covered edge:"+edge.property+"\n")
                weak_covered_edge_num=weak_covered_edge_num+1
            for edge in automata.strong_coverge_edges:
                # self.f_property.write(automata.property+","+str(automata.APs)+"\n")
                # self.f_property.write("Strong covered edge:"+edge.property+"\n")
                strong_covered_edge_num=strong_covered_edge_num+1
            for edge in automata.edges:
                if edge not in automata.weak_coverge_edges and edge.start_state not in automata.finish_state:
                    self.f_property.write(automata.property+", APs:"+str(automata.APs)+", now state:"+automata.now_state+"\n")
                    self.f_property.write("Not covered edge:"+edge.property+", start state:"+edge.start_state+", end state:"+edge.end_state+"\n")
            edge_num = len(automata.edges)
            if weak_covered_edge_num==edge_num:
                covered_automata_num = covered_automata_num+1
            # self.f_property.write("Weak coverage of edge:"+str(weak_covered_edge_num/edge_num)+"\n")
            # self.f_property.write("Strong coverage of edge:"+str(strong_covered_edge_num/edge_num)+"\n")
            # self.f_property.write("------------------------------------"+"\n")
            all_weak_covered_edge_num = all_weak_covered_edge_num+weak_covered_edge_num
            all_strong_covered_edge_num = all_strong_covered_edge_num+strong_covered_edge_num
            all_edge_num = all_edge_num+edge_num
        self.f_property.write("Edge's weak coverage of all automata:"+str(all_weak_covered_edge_num/all_edge_num)+"\n")
        self.f_property.write("Edge's strong coverage of all automata:"+str(all_strong_covered_edge_num/all_edge_num)+"\n")
        self.f_property.write("Num of automata that all edge have been weak covered:"+str(covered_automata_num/all_automata)+"\n")
        self.f_property.write("---------------Coverage Info End---------------"+"\n") 

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

    def get_combinations(self):
        list = []
        for state in self.stateproperty_list:
            list.append(state.controlproperties)
        return list

    def check_formula(self,edge,automata):
        APs = automata.APs
        property_sets =[]
        properties = edge.property
        if  "t" in properties:
            return property_sets
        or_properties = properties.split("|")
        for or_property in or_properties:
            and_properties = or_property.split("&")
            property_set = []
            for property_num in and_properties:
                notflag = ""
                if "!" in property_num:
                    notflag ="not"
                property_num=property_num.replace("!","")
                property = APs[int(property_num)]
                if property in self.all_controlproperties and notflag == "not":
                    property_set.append("not "+property)
                elif property in self.all_controlproperties and notflag == "":
                    property_set.append(property)
            if property_set!=[] and property_set not in property_sets:
                property_sets.append(property_set)
            elif property_set not in property_sets:
                property_sets.append(property_set)
        return property_sets

    def check_now_state(self):
        for propertyname in self.all_controlproperties:
            target_property = None  
            for property in self.property_list:
                if property.name == propertyname and property.type == "check":
                    target_property = property
                    break
            if target_property!=None and target_property.name not in self.now_properties and target_property.name not in self.not_properties:
                result = self.execute_and_check_property(target_property)
                if result == True:
                    self.now_properties.append(property.name)
                else:
                    self.not_properties.append(property.name)
        for state in  self.stateproperty_list:
            flag = True
            for property in self.now_properties:
                if property not in state.controlproperties:
                    flag = False
                    break
            if flag == True and len(state.controlproperties) == len(self.now_properties):
                return state
        print("wrong")
                    
    def automata_change(self):
        fail_automatas = []
        i=0
        while i < len(self.automata_list):
            automata = self.automata_list[i]
            for edge in automata.edges:
                if edge.start_state == automata.now_state:
                    check_strong=self.check_satisfy(self.automata_list[i],edge,"strong")
                    if check_strong == True:
                        self.automata_list[i].add_coverge(edge)
                        self.f_property.write("Add strong coverge:"+self.automata_list[i].property+","+edge.property+"\n")
                        print("Add strong coverge:"+self.automata_list[i].property+","+edge.property+"\n")
                        self.automata_list[i].now_state = edge.end_state
                        print(automata.property+" transfer to state"+automata.now_state)
                        self.f_property.write(automata.property+" transfer to state"+automata.now_state+"\n")
                        if edge.end_state in automata.finish_state:
                            fail_automatas.append(automata)
                    
            i=i+1
        return fail_automatas

    def check_satisfy(self,automata,edge,flag):
        properties = edge.property
        APs = automata.APs
        or_properties = properties.split("|")
        or_properties_flag = False
        for and_properties in or_properties:
            and_properties_flag = True
            property_list = and_properties.split("&")
            property_list_pre = []
            property_list_post = []
            for property in property_list:
                if property == "t":
                    continue
                if APs[int(property.replace("!",""))] in self.all_controlproperties:
                    property_list_pre.append(property)
                else:
                    property_list_post.append(property)
            if flag == "strong":
                property_list = property_list_pre+property_list_post
            else:
                property_list = property_list_pre
            print(property_list)
            for property_num in property_list:
                notflag = ""
                if "!" in  property_num:
                    notflag ="not"
                property_num=property_num.replace("!","")
                property = APs[int(property_num)]
                if property in self.now_properties and notflag=="not":
                    and_properties_flag=False
                    break
                elif property in self.not_properties and notflag=="":
                    and_properties_flag=False
                    break
                elif property not in self.now_properties and property not in self.not_properties:
                    target_property = None
                    for realproperty in self.property_list:
                        if realproperty.name == property and realproperty.type == "check":
                            target_property = realproperty
                    if target_property!=None:
                        incidental_properties=self.find_incidental_property(target_property)
                        checkresult=self.execute_and_check_properties(target_property,incidental_properties)
                        self.f_property.flush()
                        if checkresult==True and notflag == "not":
                            and_properties_flag=False
                            break
                        elif checkresult==False and notflag == "":
                            and_properties_flag=False
                            break
                    else:
                        self.f_property.write("can not find "+property+"\n")
                        and_properties_flag=False
            if and_properties_flag == True:
                or_properties_flag = True
                break
        return or_properties_flag

    def execute_and_check_properties(self,nowproperty,incidental_properties):
        self.now_event = self.now_event + 1
        print("Start event:"+str(self.now_event)+", execute and check "+str(nowproperty.name))
        self.f_property.write("Start event:"+str(self.now_event)+", execute and check "+str(nowproperty.name)+"\n")
        self.f_property.flush()
        self.device1.stop_app(self.app)
        self.device2.stop_app(self.app)
        self.device1.start_app(self.app)
        self.device2.start_app(self.app)
        self.save_screen(self.root_path,self.now_event,self.device1)
        self.save_screen(self.root_path,self.now_event,self.device2)
        layout_num = 0
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
                execute_event.set_text(self.policy.random_text())
            nowwidget.print()
            executeresult=self.executor.execute(execute_event,0)
            self.f_event.write(str(self.now_event)+"::"+device.device_serial+"::"+execute_event.action+"::"+execute_event.text+"::"+execute_event.widgettoline()+"\n")
            self.f_event.flush()
            self.now_event = self.now_event + 1
            self.save_screen(self.root_path,self.now_event,device)
            layout_num = layout_num + 1
            if executeresult==False and event.force != False:
                print(event.action+" "+event.widget+"fail")
                self.f_property.write("Execute fail: "+event.action+" "+event.widget+"\n")
                return False
            else:
                for incidental_property in incidental_properties:
                    result = self.check_property(layout_num,incidental_property,device)
                    if result == False and incidental_property.name not in self.not_properties:
                        self.not_properties.append(incidental_property.name)
                        self.f_property.write("Check result: not "+incidental_property.name+"\n")
                        print("Check result: not "+incidental_property.name)
                result = self.check_property(layout_num,nowproperty,device)
                if result == False and nowproperty.name not in self.not_properties:
                    self.not_properties.append(nowproperty.name)
                    self.f_property.write("Check result: not "+nowproperty.name+"\n")
                    print("Check result: not "+nowproperty.name)
                    return False
        if nowproperty.name not in self.now_properties and nowproperty.name not in self.not_properties:
            self.now_properties.append(nowproperty.name)
            self.f_property.write("Check result: "+nowproperty.name+"\n")
            print("Check result: "+nowproperty.name)
        for incidental_property in incidental_properties:
            if incidental_property.name not in self.not_properties and incidental_property.name not in self.now_properties:
                self.now_properties.append(incidental_property.name)
                self.f_property.write("Check result: "+incidental_property.name+"\n")
                print("Check result: "+incidental_property.name)
        print("End event:"+str(self.now_event)+", execute and check end")
        self.f_property.write("End event:"+str(self.now_event)+", execute and check end"+"\n")
        return True

    def find_incidental_property(self,target_property):
        incidental_properties = []
        for property in self.property_list:
            if property.name not in self.not_properties and property.name not in self.now_properties and property.name != target_property.name:
                events1 = property.events
                events2 = target_property.events
                flag = True
                if len(events1) !=len(events2):
                    continue
                i= 0 
                while i< len(events1):
                    if events1[i].widget != events2[i].widget or events1[i].device != events2[i].device or events1[i].text != events2[i].text:
                        flag = False
                        break
                    i=i+1
                if flag == True:
                    incidental_properties.append(property)
        return incidental_properties

    def reach_state(self,from_state,to_state):
        target_properties=[]
        now_state = from_state
        if from_state==to_state:
            return now_state
        target_properties = self.find_shortest_path(from_state,to_state)
        print("Execute "+str(target_properties)+" to from "+from_state.name+" to "+to_state.name)
        self.f_property.write("Execute "+str(target_properties)+" to from "+from_state.name+" to "+to_state.name+"\n")
        self.f_property.flush()
        for existproperty in target_properties: 
            target_property = None  
            for property in self.property_list:
                if property.name == existproperty and property.type == "control":
                    target_property = property
                    break
            if target_property!=None:
                trytime=0
                result = self.execute_and_check_property(target_property)
                while result == False and trytime<2:
                    result = self.execute_and_check_property(target_property)
                    trytime = trytime + 1
                if result == True :
                    from_state = now_state
                    now_state=self.transition_state(now_state,target_property)
                    print("Now state:"+now_state.name +" "+str(now_state.controlproperties))
                    self.f_property.write("Now state:"+now_state.name+" "+str(now_state.controlproperties)+"\n")
                    self.f_property.flush()
                    if now_state==None:
                        print("wrong")
                else:
                    print("Fail while executing control property "+existproperty)
                    self.f_property.write("Fail while executing control property "+existproperty+"\n")
                    self.f_property.flush()
                    if now_state==None:
                        print("wrong")
                    return now_state
            else:
                print("Fail, can not find control property "+existproperty)
                self.f_property.write("Can not find check property "+existproperty+"\n")
                self.f_property.flush()
                return now_state
        return now_state
    
    def find_shortest_path(self,from_state,to_state):
        i=0
        while i<len(self.stateproperty_list)-1:
            if self.stateproperty_list[i] == from_state:
                break
            i=i+1
        j=0
        while j<len(self.stateproperty_list)-1:
            if self.stateproperty_list[j] == to_state:
                break
            j=j+1
        return self.floyd_path[i][j]
    
    def generate_floyd(self):
        F: float = float('inf')
        self.floyd = [[F] * len(self.stateproperty_list) for i in range(len(self.stateproperty_list))]
        self.floyd_path = [[[]] * len(self.stateproperty_list) for i in range(len(self.stateproperty_list))]
        i=0
        while i < len(self.stateproperty_list):
            
            self.floyd[i][i]=0
            self.floyd_path[i][i]=[]
            for edge in self.edge_list:
                if edge.start_state == self.stateproperty_list[i]:
                    j=0
                    while j<len(self.stateproperty_list):
                        if self.stateproperty_list[j] == edge.end_state:
                           self.floyd[i][j]=1
                           self.floyd_path[i][j]=[edge.property]
                           break
                        j=j+1
            i=i+1
        k=0
        while k<len(self.stateproperty_list):
            i=0
            while i < len(self.stateproperty_list):
                j=0
                while j<len(self.stateproperty_list):
                    if(self.floyd[i][k]+self.floyd[k][j] < self.floyd[i][j]): 
                        self.floyd[i][j]= self.floyd[i][k]+self.floyd[k][j]
                        self.floyd_path[i][j]= self.floyd_path[i][k].copy()+self.floyd_path[k][j].copy()
                    j=j+1
                i=i+1
            k=k+1

    def transition_state(self,now_state,target_property):
        for edge in self.edge_list:
            if now_state == edge.start_state and target_property.name == edge.property:
                return edge.end_state
        print("find edge wrong")

    def execute_and_check_property(self,nowproperty):
        # return True
        self.f_property.flush()
        self.device1.stop_app(self.app)
        self.device2.stop_app(self.app)
        self.device1.start_app(self.app)
        self.device2.start_app(self.app)
        self.now_event = self.now_event + 1
        self.save_screen(self.root_path,self.now_event,self.device1)
        self.save_screen(self.root_path,self.now_event,self.device2)
        print("Start event:"+str(self.now_event)+", execute and check "+str(nowproperty.name))
        self.f_property.write("Start event:"+str(self.now_event)+", execute and check "+str(nowproperty.name)+"\n")
        layout_num = 0
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
                execute_event.set_text(self.policy.random_text())
            nowwidget.print()
            executeresult=self.executor.execute(execute_event,0)
            self.f_event.write(str(self.now_event)+"::"+device.device_serial+"::"+execute_event.action+"::"+execute_event.text+"::"+execute_event.widgettoline()+"\n")
            self.f_event.flush()
            self.now_event = self.now_event + 1
            self.save_screen(self.root_path,self.now_event,device)
            layout_num = layout_num + 1
            if executeresult==False and event.force != False:
                print(event.action+" "+event.widget+"执行失败")
                self.f_property.write("Execute fail: "+event.action+" "+event.widget+"\n")
                return False
            result = self.check_property(layout_num,nowproperty,device)
            if result == False:
                print("End event:"+str(self.now_event)+", execute and check "+str(nowproperty.name))
                self.f_property.write("End event:"+str(self.now_event)+", execute and check "+str(nowproperty.name)+"\n"+"Check result:"+"not "+str(nowproperty.name)+"\n")
                return False
        print("End event:"+str(self.now_event)+", execute and check end")
        self.f_property.write("End event:"+str(self.now_event)+", execute and check end"+"\n"+"Check result:"+""+str(nowproperty.name)+"\n")
        return True

    def check_property(self,layout_num,nowproperty,device):
        num = 0
        for condition in nowproperty.conditions:
            if int(condition.UI_layout_num) == layout_num and condition.type == "":
                for widget in nowproperty.widgets:
                    if widget.name == condition.widget:
                        targetwidget = widget
                        break
                if num ==0:
                    self.save_screen(self.root_path,self.now_event,device)
                    num =1
                result = self.findview(device.screen,targetwidget)
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
    
    def simple_automaton_coverage_test(self):
        notend = True
        self.now_testcase = -1
        for automata in self.automata_list:
            automata.now_state = automata.start_state
        self.final_satisfied_candidates = []
        self.generate_floyd()
        while notend:
            
            self.now_testcase = self.now_testcase + 1
            if not os.path.exists(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)):
                os.makedirs(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase))
            self.f_property = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/property_record.txt",'w',encoding='utf-8')
            self.f_event = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/event_record.txt",'w',encoding='utf-8')
            self.f_property.write("Now Time:"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n")
            elapsed_time = time.time()-self.start_time-self.gap_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_property.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s (do not contain check property)".format(hours, minutes, seconds)+"so far\n")
            self.f_property.write("The program has run for a total of :"+str(elapsed_time)+" second (do not contain check property) so far\n")
            elapsed_time = time.time()-self.start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_property.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s ".format(hours, minutes, seconds)+"so far\n")
            self.f_property.write("The program has run for a total of :"+str(elapsed_time)+" second so far\n")
            self.statistical_coverage()
            self.now_event = 0
            self.now_properties = []
            self.not_properties = []
            self.f_property.flush()
            if self.now_testcase != 0 and self.final_satisfied_candidates==[]:
                return
            elif self.final_satisfied_candidates!=[]:
                start_check_time = time.time()
                now_state = self.check_now_state()
                self.gap_time = self.gap_time+time.time()-start_check_time
                print("------------------------------------------")
                print("Now state:"+now_state.name+" "+str(now_state.controlproperties))
                self.f_property.write("Now state:"+now_state.name+" "+str(now_state.controlproperties)+"\n")
                print("Next properties:"+str(final_choice))
                self.f_property.write("Next properties:"+str(final_choice)+"\n")
                for state in self.stateproperty_list:
                    flag = True
                    for property in final_choice:
                        if "not" in property and property.replace("not ","") in state.controlproperties:
                            flag = False
                            break
                        elif "not" not in property and property not in state.controlproperties:
                            flag = False
                            break
                    if flag == True and len(state.controlproperties) == len(final_choice):
                        next_test_state = state
                        break
                now_state = self.reach_state(now_state, next_test_state)
                if now_state == next_test_state:
                    for candidate in self.final_satisfied_candidates:
                        if candidate.edge not in candidate.automata.weak_coverge_edges:
                            candidate.automata.weak_coverge_edges.append(candidate.edge)
                            self.f_property.write("Add weak coverge:"+candidate.automata.property+","+candidate.edge.property+","+str(candidate.automata.APs)+"\n")
                            print("Add weak coverge:"+candidate.automata.property+","+candidate.edge.property+"\n")
                        candidate.edge.weight = candidate.edge.weight/40

            if self.now_testcase != 0 and self.final_satisfied_candidates!=[]:
                print("Now state:"+next_test_state.name+" "+str(now_state.controlproperties))
                self.f_property.write("Now state:"+next_test_state.name+" "+str(now_state.controlproperties)+"\n")
                self.now_properties = now_state.controlproperties.copy()
                self.not_properties = []
                for property in self.all_controlproperties:
                    if property not in self.now_properties:
                        self.not_properties.append(property)
                fail_automatas=self.automata_change()
                if len(fail_automatas)>0:
                    for automata in fail_automatas:
                        print("Property "+automata.property+" reach accept state")
                        print("now properties:"+str(self.now_properties))
                        print("not properties:"+str(self.not_properties))
                        self.f_property.write("Property "+automata.property+" reach accept state"+"\n")
                        self.f_property.write("now properties:"+str(self.now_properties)+"\n")
                        self.f_property.write("not properties:"+str(self.not_properties)+"\n")
                else:
                    self.f_property.write("No automata reach accept state\n")
            
            all_candidates = []
            for automata in self.automata_list:
                next_edges = automata.find_next_edges_not_covered()
                candidates = []
                for edge in next_edges:
                    edge_control_propertiess = self.check_formula(edge,automata)
                    for control_properties in edge_control_propertiess:
                        candidate = Candidate(automata,edge,control_properties)
                        if candidate not in candidates and len(control_properties)>0:
                            candidates.append(candidate)
                            self.f_property.write("Candidate:"+automata.property+","+edge.property+","+str(control_properties)+"\n")
                all_candidates= all_candidates+candidates
            self.max_count = 0
            final_choice = []
            self.final_satisfied_candidates = []
            combinations = self.get_combinations()
            for combination in combinations:
                candidate_count = 0
                satisfied_candidates = []
                for candidate in all_candidates:
                    edge = candidate.control_properties
                    if self.check_weak_equivalence(combination,edge):
                        candidate_count = candidate_count+candidate.edge.weight
                        satisfied_candidates.append(candidate)
                    if candidate_count>self.max_count:
                        final_choice = combination
                        self.max_count = candidate_count
                        self.final_satisfied_candidates = satisfied_candidates.copy()
            for candidate in self.final_satisfied_candidates:
                self.f_property.write("Final Candidate:"+candidate.automata.property+","+candidate.edge.property+","+str(candidate.control_properties)+"\n")

            self.f_property.write("Final choice:"+str(final_choice)+"\n")
            self.f_property.flush()
            for automata in self.automata_list:
                self.f_property.write(str(automata.property)+":")
                for edge in automata.weak_coverge_edges:
                    self.f_property.write(edge.property)
                self.f_property.write("\n")
            self.f_property.flush()


    def random_test(self):
        notend = True
        self.now_testcase = -1
        for automata in self.automata_list:
            automata.now_state = automata.start_state
        self.final_satisfied_candidates = []
        self.generate_floyd()
        
        self.timer = Timer(0, self.stop)
        self.timer.start()
        self.start_time = time.time()
        while notend:
            
            self.now_testcase = self.now_testcase + 1
            if not os.path.exists(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)):
                os.makedirs(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase))
            self.f_property = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/property_record.txt",'w',encoding='utf-8')
            self.f_event = open(self.root_path+self.app.app_name+"screen/"+str(self.num)+str(self.now_testcase)+"/event_record.txt",'w',encoding='utf-8')
            self.f_property.write("Now Time:"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"\n")
            elapsed_time = time.time()-self.start_time-self.gap_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_property.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s (do not contain check property)".format(hours, minutes, seconds)+"so far\n")
            self.f_property.write("The program has run for a total of :"+str(elapsed_time)+" second (do not contain check property) so far\n")
            elapsed_time = time.time()-self.start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.f_property.write("The program has run for a total of :{:.0f} h {:.0f} m {:.2f} s ".format(hours, minutes, seconds)+"so far\n")
            self.f_property.write("The program has run for a total of :"+str(time.time()-self.start_time)+" second so far\n")
            self.statistical_coverage()
            self.now_event = 0
            if self.now_testcase != 0:
                self.now_properties = []
                self.not_properties = []
            else:
                self.now_properties = []
                self.not_properties = []
            self.f_property.flush()
            
            if self.final_satisfied_candidates!=[]:
                start_check_time = time.time()
                now_state = self.check_now_state()
                self.gap_time = self.gap_time+time.time()-start_check_time
                next_test_state = now_state
                print("------------------------------------------")
                print("Now state:"+now_state.name+" "+str(now_state.controlproperties))
                self.f_property.write("Now state:"+now_state.name+" "+str(now_state.controlproperties)+"\n")
                print("Next properties:"+str(final_choice))
                self.f_property.write("Next properties:"+str(final_choice)+"\n")
                for state in self.stateproperty_list:
                    flag = True
                    for property in final_choice:
                        if "not" in property and property.replace("not ","") in state.controlproperties:
                            flag = False
                            break
                        elif "not" not in property and property not in state.controlproperties:
                            flag = False
                            break
                    if flag == True and len(state.controlproperties) == len(final_choice):
                        next_test_state = state
                        break
                now_state = self.reach_state(now_state, next_test_state)
                if now_state == next_test_state:
                    for candidate in self.final_satisfied_candidates:
                        if candidate.edge not in candidate.automata.weak_coverge_edges:
                            candidate.automata.weak_coverge_edges.append(candidate.edge)
                            self.f_property.write("Add weak coverge:"+candidate.automata.property+","+candidate.edge.property+","+str(candidate.automata.APs)+"\n")
                            print("Add weak coverge:"+candidate.automata.property+","+candidate.edge.property+"\n")
                        candidate.edge.weight = candidate.edge.weight/40
            
            if self.now_testcase != 0:
                print("Now state:"+next_test_state.name+" "+str(now_state.controlproperties))
                self.f_property.write("Now state:"+next_test_state.name+" "+str(now_state.controlproperties)+"\n")
                self.now_properties = now_state.controlproperties.copy()
                self.not_properties = []
                for property in self.all_controlproperties:
                    if property not in self.now_properties:
                        self.not_properties.append(property)
                fail_automatas=self.automata_change()
                if len(fail_automatas)>0:
                    for automata in fail_automatas:
                        print("Property "+automata.property+" reach accept state")
                        print("now properties:"+str(self.now_properties))
                        print("not properties:"+str(self.not_properties))
                        self.f_property.write("Property "+automata.property+" reach accept state"+"\n")
                        self.f_property.write("now properties:"+str(self.now_properties)+"\n")
                        self.f_property.write("not properties:"+str(self.not_properties)+"\n")
                else:
                    self.f_property.write("No automata reach accept state\n")
            
            all_candidates = []
            for automata in self.automata_list:
                next_edges = automata.final_satisfied_candidates()
                candidates = []
                for edge in next_edges:
                    edge_control_propertiess = self.check_formula(edge,automata)
                    for control_properties in edge_control_propertiess:
                        candidate = Candidate(automata,edge,control_properties)
                        if candidate not in candidates and len(control_properties)>0:
                            candidates.append(candidate)
                            self.f_property.write("Candidate:"+automata.property+","+edge.property+","+str(control_properties)+"\n")
                all_candidates= all_candidates+candidates
            final_choice = []
            self.final_satisfied_candidates = []
            combinations = self.get_combinations()
            import random
            comnum = random.randint(0,len(combinations)-1)
            combination = combinations[comnum]
            candidate_count = 0
            satisfied_candidates = []
            for candidate in all_candidates:
                edge = candidate.control_properties
                if self.check_weak_equivalence(combination,edge):
                    candidate_count = candidate_count+1
                    satisfied_candidates.append(candidate)
                final_choice = combination
                self.final_satisfied_candidates = satisfied_candidates.copy()
            for candidate in self.final_satisfied_candidates:
                self.f_property.write("Final Candidate:"+candidate.automata.property+","+candidate.edge.property+","+str(candidate.control_properties)+"\n")

            self.f_property.write("Final choice:"+str(final_choice)+"\n")
            self.f_property.flush()
            for automata in self.automata_list:
                self.f_property.write(str(automata.property)+":")
                for edge in automata.weak_coverge_edges:
                    self.f_property.write(edge.property)
                self.f_property.write("\n")
            self.f_property.flush()
    

