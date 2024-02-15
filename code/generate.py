from util import Util
from property import State
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
            for proposition in self.data["control_propositions"]:
                controllableproposition = now_state.controllableproposition.copy()
                if proposition not in controllableproposition: 
                    
                    controllableproposition.append(proposition)
                    backproposition = "not "+proposition
                    flag=""
                    for pair in self.mutually_exclusive_pairs:
                        if pair[0] == proposition and pair[1] in controllableproposition:
                            controllableproposition.remove(pair[1])
                            backproposition=""
                        if pair[1] == proposition and pair[0] in controllableproposition:
                            flag = "continue"
                        # if pair[1] == proposition and pair[0] in controllableproposition:
                        #     controllableproposition.remove(pair[0])
                        #     backproposition=pair[0]
                    if flag == "continue":
                        continue
                    controllableproposition.sort()
                    checkstate = self.checkrepeat(self.statelist,controllableproposition)
                    if checkstate == None:
                        num = num + 1
                        state = State("S"+str(num),controllableproposition.copy())
                        self.statelist.append(state)
                        temporary.append(state)
                        line0 = state.name+"[label=\""+','.join(controllableproposition)+"\"];"
                        line1 =  now_state.name+"->"+state.name+"[label=\""+proposition.replace("P","P")+"\"]"
                        line2 =  state.name+"->"+now_state.name+"[label=\""+backproposition+"\"]"
                        f_edge.write(line0+"\n")
                        if self.checkcannotreach(proposition, now_state.controllableproposition.copy()):
                            f_edge.write(line1+"\n")
                        if self.checkcannotreach(backproposition, state.controllableproposition.copy()) and backproposition!="":
                            f_edge.write(line2+"\n")
                        f_edge.flush()
                    else:
                        line1 =  now_state.name+"->"+checkstate.name+"[label=\""+proposition.replace("P","P")+"\"]"
                        line2 =  checkstate.name+"->"+now_state.name+"[label=\""+backproposition+"\"]"
                        if self.checkcannotreach(proposition, now_state.controllableproposition.copy()):
                            f_edge.write(line1+"\n")
                        if self.checkcannotreach(backproposition, state.controllableproposition.copy()) and backproposition!="":
                            f_edge.write(line2+"\n")
                        f_edge.flush()
        print("end")
        f_edge.write("}")
        f_edge.flush()
        f_edge.close()
    
    def checkcannotreach(self, proposition, controllableproposition):
        for pair in self.data["can_not_reach_pairs"]:
            if "not " in pair[0]:
                pair0 = pair[0].split(" ")
                if pair0[1] not in controllableproposition and pair[1] == proposition:
                    return False
            if pair[0] in controllableproposition and pair[1] == proposition:
                return False
        return True
        
    def checkrepeat(self,statelist,controllableproposition):
        for state in statelist:
            if state.controllableproposition == controllableproposition:
                return state
        return None