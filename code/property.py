class Path(object):
    def __init__(self, distance,path):
        self.distance = distance
        self.path = path

class Item(object): 
    def __init__(self, key):
        self.key = key
        self.nodes = []
        self.text = ""
        self.link = ""

class Candidate(object):
    def __init__(self,automata,edge,control_propositions):
        self.control_propositions = control_propositions
        for control in self.control_propositions:
            if control == []:
                self.control_propositions.remove(control)
        self.automata = automata
        self.edge = edge

class Rule(object):
    def __init__(self,line):
        self.line = line
        stack = []
        self.rootnode = Item(0)
        stack.append(self.rootnode)
        laststr = line[0]
        i=1
        text = ""
        while i < len(line):
            str = line[i]
            if str == "(":
                item  = Item(laststr)
                stack.append(item)
                text = ""
            elif str == ")":
                item = Item("")
                if stack[len(stack)-1].key == "X":
                    item.key = "X"
                item.text = text
                stack[len(stack)-1].nodes.append(item)
                item=stack.pop()
                stack[len(stack)-1].nodes.append(item)
                text = ""
            elif str == "|":
                item = Item("")
                if stack[len(stack)-1].key == "X":
                    item.key = "X"
                item.text = text
                text = ""
                stack[len(stack)-1].link = "|"
                stack[len(stack)-1].nodes.append(item)
            elif str == "&":
                item = Item("")
                if stack[len(stack)-1].key == "X":
                    item.key = "X"
                item.text = text
                text = ""
                stack[len(stack)-1].link = "&"
                stack[len(stack)-1].nodes.append(item)
            else:
                text = text+str
            i=i+1
            laststr = str

class State(object):

    def __init__(self, name,controllableproposition):
        self.name = name
        self.controllableproposition = controllableproposition

class Automata(object):
    def __init__(self):
        self.edges = []
        self.finish_state = []
        self.start_state = ""
        self.now_state = ""
        self.proposition = ""
        self.APs = []
        self.weak_coverage_edges = []
        self.strong_coverage_edges = []

    def add_finish_state(self,state):
        self.finish_state.append(state)

    def add_edge(self,edge):
        self.edges.append(edge)

    def add_coverage(self,edge):
        if edge not in self.weak_coverage_edges:
            self.weak_coverage_edges.append(edge)
        if edge not in self.strong_coverage_edges:
            self.strong_coverage_edges.append(edge) 

    def find_next_edges(self):
        next_edges = []
        for edge in self.edges:
            if edge.start_state == self.now_state:
                next_edges.append(edge)
        return next_edges
    
    def find_next_edges_not_covered(self):
        next_edges = []
        for edge in self.edges:
            if edge.start_state == self.now_state and edge not in self.weak_coverage_edges:
                next_edges.append(edge)
        return next_edges


class Edge(object):

    def __init__(self, start_state, end_state,proposition):
        self.start_state = start_state
        self.end_state = end_state
        self.proposition = proposition
        self.weight = 1

class Proposition(object):
    
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.events = []
        self.oracles = []
        self.widgets = []
        self.conditions = []
        self.actions = []

    def add_event(self,action,widget,text,force,device):
        event = Event(action,widget,text,force,device)
        self.events.append(event)

    def add_widget(self,UI_layout_num,className,description,name,resourceId,text,xpath,instance):
        if instance =="":
            instance = 0
        else:
            instance = int(instance)
        widget = Widget(UI_layout_num,className,description,name,resourceId,text,xpath,instance)
        self.widgets.append(widget)

    def add_condition(self,UI_layout_num, relation, widget,edge):
        condition = Condition(UI_layout_num, relation, widget,edge)
        self.conditions.append(condition)

class RandomEvent(object):

    def __init__(self, view, action, device, event_count):
        self.view = view
        self.action = action
        self.device = device
        self.text = "None"
        self.count=0
        self.event_count=event_count
        self.force = True
        self.data = ""
    
    def set_device(self,device):
        self.device = device
    
    def set_text(self,text):
        self.text = text
    
    def set_count(self,count):
        self.count = count
    
    def set_force(self,force):
        self.force = force
    
    def print_event(self):
        print("Event start=============================")
        print("Event_count:"+str(self.event_count))
        if self.view is not None:
            print("View_text:"+self.view.line)
        print("Action:"+self.action)
        print("Device:"+self.device.device_serial)
        if self.text is not None:
            print("Text:"+self.text)
        print("Event end=============================")


class Event(object):
    def __init__(self,action,widget,text,force,device):
        self.action = action
        self.widget = widget
        self.text = text
        self.force = force
        self.device = device
    
    def set_text(self,text):
        self.text = text

    def print(self):
        print("Action:"+self.action)
        if self.text !="":
            print("Text:"+self.text)
        if self.widget !=None:  
            self.widget.print()

    def widgettoline(self):
        line="<node NAF=\"#any#\" index=\"index_string\" text=\"text_string\" resource-id=\"resourceId_string\" class=\"className_string\" package=\"#any#\" content-desc=\"description_string\" checkable=\"#any#\" checked=\"#any#\" clickable=\"#any#\" enabled=\"#any#\" focusable=\"#any#\" focused=\"#any#\" scrollable=\"#any#\" long-clickable=\"#any#\" password=\"#any#\" selected=\"#any#\" visible-to-user=\"#any#\" bounds=\"\" />"
        if self.widget==None:
            return line
        line= line.replace("text_string",self.widget.text).replace("resourceId_string",self.widget.resourceId).replace("className_string",self.widget.className).replace("description_string",self.widget.description).replace("index_string",str(self.widget.instance))
        return line
        
class Widget(object):
    def __init__(self,UI_layout_num,className,description,name,resourceId,text,xpath,instance):
        self.UI_layout_num = UI_layout_num
        self.className = className
        self.description = description
        self.name = name
        self.resourceId = resourceId
        self.text = text
        self.xpath = xpath
        self.instance = instance
        self.x = -1
        self.y = -1

    def print(self):
        if self.className != "":
            print("className: "+self.className+", ")
        if self.text != "":
            print("text: "+self.text+", ")
        if self.description != "":
            print("description: "+self.description+", ")
        if self.resourceId != "":
            print("resourceId: "+self.resourceId+", ")
        if self.xpath != "":
            print("xpath: "+self.xpath+", ")
        if self.instance != "":
            print("instance: "+str(self.instance)+", ")

class Condition(object):

    def __init__(self, UI_layout_num, relation, widget, type):
        self.UI_layout_num = UI_layout_num
        self.relation = relation
        self.widget = widget
        self.type = type
