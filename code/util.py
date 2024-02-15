import os
import json
from tkinter import NO
from property import Proposition,Edge,State,Automata
from appinfo import App

class Util(object):

    def __init__(self, app_path):
        self.app = App(app_path)
    
    def create_outputdir(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path+self.app.app_name+"screen"):
            os.makedirs(path+self.app.app_name+"screen")

    def get_edge(self,root_path,rule_name):
        edge_list = []
        self.state_list = []
        state = State("S0",[])
        self.state_list.append(state)
        with open(os.path.join(root_path+"/"+rule_name+"edge.gv"), 'r') as f:
            lines = f.readlines()
        for line in lines:
            if "{" in line or "}" in line:
                continue
            elif "->" not in line:
                num1=line.find("[label")
                num2=line.find("\"]")
                state_name = line[0:num1]
                propositions = line[num1+8:num2]
                propositionlist = propositions.split(",")
                state = State(state_name,propositionlist)
                self.state_list.append(state)
            else:
                num1=line.find("->")
                start_state_name = line[0:num1]
                num2=line.find("[label")
                end_state_name = line[num1+2:num2]
                num3=line.find("\"]")
                proposition = line[num2+8:num3]
                start_state = None
                end_state = None
                for state in self.state_list:
                    if state.name == start_state_name:
                        start_state = state
                    elif state.name == end_state_name:
                        end_state = state
                edge = Edge(start_state, end_state, proposition)
                edge_list.append(edge)
        return edge_list
    
    def get_controllableproposition(self,root_path,rule_name):  
        control_propositions = []  
        with open(os.path.join(root_path+"/"+rule_name+"rule.json"), 'r') as f:
            self.data = json.load(f)
        for line in self.data["control_propositions"]:
            control_propositions.append(line)
        return control_propositions

    def get_automata(self,root_path,rule_name):
        with open(os.path.join(root_path+"/"+rule_name+"automata.txt"), 'r') as f:
            lines = f.readlines()
        automata_list = []
        for line in lines:
            if "--START--" in line:
                startflag = False
                automata = Automata()
            elif "Property: " in line:
                automata.proposition = line.replace("\n","")
            elif "--END--" in line:
                startflag =False
                automata_list.append(automata)
            elif "Start: " in line:
                start_state = line[line.find("Start: ")+7:line.find("\n")]
                automata.start_state = start_state
            elif "AP:" in line:
                APs =[]
                while "\"" in line:
                    line = line[line.find("\"")+1:len(line)]
                    AP = line[0:line.find("\"")]
                    line = line[line.find("\"")+1:len(line)]
                    APs.append(AP)
                automata.APs = APs
            elif "State: " in line:
                start_state = line[line.find("State: ")+7:line.find("State: ")+8]
                startflag = True
                if "{" in line and "}" in line:
                    automata.add_finish_state(start_state)
            elif startflag == True:
                proposition = line[line.find("[")+1:line.find("]")]
                endstate = line[line.find("]")+2:line.find("\n")]
                edge = Edge(start_state, endstate, proposition)
                automata.add_edge(edge)
        return automata_list

    def get_keyview(self,root_path,rule_name):
        keyview_list = []
        with open(os.path.join(root_path+"/"+rule_name+"keyview.json"), 'r') as f:
            data = json.load(f)
        for nowview in data['keyviews']:
            print(nowview['view'])
            from screen import View 
            view = View(nowview['view'],[])
            keyview_list.append(view)
        return keyview_list
        
    def get_state(self):
        return self.state_list

    def replace_text(self,text):
        if text == "A_name":
            returntext = "test333444"
        elif text == "B_name":
            returntext = "test444333"
        elif text == "A_ID":
            returntext = "test333444"
        elif text == "B_ID":
            returntext = "test444333"
        return returntext
    
    def get_proposition(self,root_path,rule_name):
        proposition_list = []
        with open(os.path.join(root_path+"/"+rule_name+"proposition.json"), 'r') as f:
            data = json.load(f)
        for newproposition in data['propositions']: 
            print(newproposition['name']+"::"+newproposition['type']) 
            proposition = Proposition(newproposition['name'],newproposition['type'])
            for fragment in newproposition['fragments']:
                for provide_fragment in data['fragments']:
                    this_args = []
                    for arg in fragment['args']:
                        this_arg = self.replace_text(arg)
                        this_args.append(this_arg)
                    if provide_fragment['name'] == fragment['name']:
                        for event in provide_fragment['events']:
                            proposition.add_event(event['action'],provide_fragment['name']+"_"+event['widget'],self.replace_text(event['text'].replace("args[1]",this_args[1])),event['force'],this_args[0])
                        for widget in provide_fragment['widgets']:
                            text = self.replace_text(widget['text'].replace("args[1]",this_args[1]))
                            contentdesc = self.replace_text(widget['content-desc'].replace("args[1]",this_args[1]))
                            proposition.add_widget(widget['UI_layout_num'],widget['class'],contentdesc,provide_fragment['name']+"_"+widget['name'],widget['resource-id'],text,widget['xpath'],widget['instance'])
            for event in newproposition['events']:
                text = self.replace_text(event['text'])
                proposition.add_event(event['action'],event['widget'],text,event['force'],event['device'])
            for widget in newproposition['widgets']:
                text = self.replace_text(widget['text'])
                proposition.add_widget(widget['UI_layout_num'],widget['class'],widget['content-desc'],widget['name'],widget['resource-id'],text,widget['xpath'],widget['instance'])
            for condition in newproposition['conditions']:
                proposition.add_condition(condition['UI_layout_num'],condition['relation'],condition['widget'],condition['type'])
            proposition_list.append(proposition)
            
        return proposition_list

    def draw_event(self,event,path):
        from cv2 import cv2
        image = cv2.imread(path)
        if event.widget !=None:
            if event.action == "click":
                cv2.rectangle(image, (int(event.widget.xmin), int(event.widget.ymin)), (int(event.widget.xmax), int(event.widget.ymax)), (0, 0, 255), 5)  
            elif event.action == "longclick":
                cv2.rectangle(image, (int(event.widget.xmin), int(event.widget.ymin)), (int(event.widget.xmax), int(event.widget.ymax)), (0, 225, 255), 5) 
            elif event.action == "edit":
                cv2.rectangle(image, (int(event.widget.xmin), int(event.widget.ymin)), (int(event.widget.xmax), int(event.widget.ymax)), (225, 0, 255), 5)
            elif "scroll" in event.action:
                cv2.rectangle(image, (int(event.widget.xmin), int(event.widget.ymin)), (int(event.widget.xmax), int(event.widget.ymax)), (225, 255, 0), 5)
            else:
                cv2.rectangle(image, (int(event.widget.xmin), int(event.widget.ymin)), (int(event.widget.xmax), int(event.widget.ymax)), (225, 225, 255), 5)
        else:
            if event.action == "wrong":
                cv2.rectangle(image, (0,0), (1430, 2550), (0, 225, 255), 20)
            else:
                cv2.putText(image,event.action, (100,300), cv2.FONT_HERSHEY_SIMPLEX, 5,(0, 0, 255), 1, cv2.LINE_AA)
        image=cv2.resize(image, (288, 640))
        cv2.imwrite(path, image)
    