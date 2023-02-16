from util import Util
from property import State, Rule
import os
import json
from appinfo import App

class Generate(object):

    def __init__(self,root_path,app_path,rule_name):
        self.root_path = root_path
        self.util = Util(app_path)
        self.app = App(app_path)
        self.statelist = []
        self.mutually_exclusive_pairs = []
        self.rule_name = rule_name
        
        self.get_rule()
        
    def get_rule(self):    
        with open(os.path.join(self.root_path+"define/"+self.app.app_name+"/"+self.rule_name+"rule.json"), 'r') as f:
            self.data = json.load(f)
        for pairs in self.data["mutually_exclusive_pairs"]:
            if len(pairs) == 2:
                self.mutually_exclusive_pairs.append(pairs)
            else:
                for p1 in pairs:
                    for p2 in pairs:
                        if p1 != p2:
                            pair = [p1,p2]
                            pair.sort()
                            if pair not in self.mutually_exclusive_pairs:
                                self.mutually_exclusive_pairs.append(pair)

    def start(self):
        self.generate_edge()
    
    def generate_edge(self):
        f_edge = open(self.root_path+"define/"+self.app.app_name+"/"+self.rule_name+"edge.gv",'w',encoding='utf-8')
        f_edge.write("digraph startgame {\n")
        temporary = []
        num = 0
        state = State("S"+str(num),[])
        self.statelist.append(state) 
        temporary.append(state) 
        while len(temporary)>0:
            now_state = temporary.pop()
            for property in self.data["control_properties"]:
                controlproperties = now_state.controlproperties.copy()
                if property not in controlproperties: 
                    
                    controlproperties.append(property)
                    backproperty = "not "+property
                    for pair in self.mutually_exclusive_pairs:
                        if pair[0] == property and pair[1] in controlproperties:
                            controlproperties.remove(pair[1])
                            backproperty = pair[1]
                        elif pair[1] == property and pair[0] in controlproperties:
                            controlproperties.remove(pair[0])
                            backproperty = pair[0]
                    controlproperties.sort()
                    checkstate = self.checkrepeat(self.statelist,controlproperties)
                    if checkstate == None:
                        num = num + 1
                        state = State("S"+str(num),controlproperties.copy())
                        self.statelist.append(state)
                        temporary.append(state)
                        line0 = state.name+"[label=\""+','.join(controlproperties)+"\"];"
                        line1 =  now_state.name+"->"+state.name+"[label=\""+property.replace("P","P")+"\"]"
                        line2 =  state.name+"->"+now_state.name+"[label=\""+backproperty+"\"]"
                        f_edge.write(line0+"\n")
                        if self.checkcannotreach(property, now_state.controlproperties.copy()):
                            f_edge.write(line1+"\n")
                        if self.checkcannotreach(backproperty, state.controlproperties.copy()):
                            f_edge.write(line2+"\n")
                        f_edge.flush()
                    else:
                        line1 =  now_state.name+"->"+checkstate.name+"[label=\""+property.replace("P","P")+"\"]"
                        line2 =  checkstate.name+"->"+now_state.name+"[label=\""+backproperty+"\"]"
                        if self.checkcannotreach(property, now_state.controlproperties.copy()):
                            f_edge.write(line1+"\n")
                        if self.checkcannotreach(backproperty, state.controlproperties.copy()):
                            f_edge.write(line2+"\n")
                        f_edge.flush()
        print("end")
        f_edge.write("}")
        f_edge.flush()
        f_edge.close()
    
    def checkcannotreach(self, property, controlproperties):
        for pair in self.data["can_not_reach_pairs"]:
            if pair[0] in controlproperties and pair[1] == property:
                return False
        return True
        
    def checkrepeat(self,statelist,controlproperties):
        for state in statelist:
            if state.controlproperties == controlproperties:
                return state
        return None