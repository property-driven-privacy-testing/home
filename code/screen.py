class View(object):

    def __init__(self,line,father):
        self.line = line
        self.father = father 
        self.findkey()
        self.children = []
    
    def add_child(self,child):
        self.children.append(child)

    def findkey(self):
        self.x = -1
        self.y = -1
        self.index=self.get_attribute('index=')
        self.text=self.get_attribute('text=')
        self.resourceId=self.get_attribute('resource-id=')
        self.className=self.get_attribute('class=')
        self.package=self.get_attribute('package=')
        self.description=self.get_attribute('content-desc=')
        self.checkable=self.get_attribute('checkable=')
        self.checked=self.get_attribute('checked=')
        self.clickable=self.get_attribute('clickable=')
        self.enabled=self.get_attribute('enabled=')
        self.focusable=self.get_attribute('focusable=')
        self.focused=self.get_attribute('focused=')
        self.scrollable=self.get_attribute('scrollable=')
        self.longClickable=self.get_attribute('long-clickable=')
        self.password=self.get_attribute('password=')
        self.selected=self.get_attribute('selected=')
        self.visibleToUser=self.get_attribute('visible-to-user=')
        self.bounds=self.get_attribute('bounds=')
        self.get_bounds_value()
        self.instance = ""
        self.xpath = ""

    def get_attribute(self,keywords):
        line=self.line
        attributenum=line.find(keywords)
        line=line[attributenum+len(keywords)+1:len(line)-1]
        marksnum=line.find('\"')
        attribute=line[0:marksnum]
        return attribute

    def get_bounds_value(self):
        num1=self.bounds.find(",")
        self.xmin=self.bounds[1:num1]
        num2=self.bounds.find("]")
        self.ymin=self.bounds[num1+1:num2]
        line=self.bounds[num2+1:len(self.bounds)]
        num1=line.find(",")
        self.xmax=line[1:num1]
        num2=line.find("]")
        self.ymax=line[num1+1:num2]
        if self.xmax!= "" and self.xmin!="" and self.ymax!= "" and self.ymin!="":
            self.x = (int(self.xmin)+int(self.xmax)) /2
            self.y = (int(self.ymin)+int(self.ymax)) /2
    
    def same(self,view):
        if self.className !="#any#" and view.className !="#any#" and self.className != view.className:
            return False
        if self.resourceId !="#any#" and view.resourceId !="#any#" and self.resourceId != view.resourceId:
            return False
        if self.package !="#any#" and view.package !="#any#" and self.package != view.package:
            return False
        if self.selected !="#any#" and view.selected !="#any#" and self.selected != view.selected:
            return False
        if self.description !="#any#" and view.description !="#any#" and self.description != view.description:
            return False
        if self.focused !="#any#" and view.focused !="#any#" and self.focused != view.focused:
            return False
        if self.enabled !="#any#" and view.enabled !="#any#" and self.enabled != view.enabled:
            return False
        if self.clickable !="#any#" and view.clickable !="#any#" and self.clickable != view.clickable:
            return False
        if self.checked !="#any#" and view.checked !="#any#" and self.checked != view.checked:
            return False
        if self.checkable !="#any#" and view.checkable !="#any#" and self.checkable != view.checkable:
            return False
        if self.text !="#any#" and view.text !="#any#" and self.text != view.text:
            return False
        if self.visibleToUser !="#any#" and view.visibleToUser !="#any#" and self.visibleToUser != view.visibleToUser:
            return False
        if self.password !="#any#" and view.password !="#any#" and self.password != view.password:
            return False
        if self.longClickable !="#any#" and view.longClickable !="#any#" and self.longClickable != view.longClickable:
            return False
        if self.scrollable !="#any#" and view.scrollable !="#any#" and self.scrollable != view.scrollable:
            return False
        if self.bounds !="#any#" and view.bounds !="#any#" and self.bounds !="" and view.bounds !="" and self.bounds != view.bounds:
            return False
        return True
    
    def notin(self,viewlist):
        for now_view in viewlist:
            if self.same(now_view):
                return False
        return True

    def print(self):
        if self.line != "":
            print("line: "+self.line)


class Screen(object):

    def __init__(self, lines):
        self.lines = lines
        self.text = ""
        self.allviews = [] 
        self.allleafviews=self.get_view() 

    def findviewinstance(self,now_layout, resourceId, className, text):
        view=None
        instance = 0
        for line in now_layout:
            if "<node" not in line:
                continue
            view = View(line,[])
            if resourceId!=None and resourceId == view.resourceId:
                if view.text == text:
                    return str(instance)
                else:
                    instance = instance+1
            elif className!=None and className == view.className:
                if view.text == text:
                    return str(instance)
                else:
                    instance = instance+1
            else:
                continue
        return ""

    def get_view(self):
        allleafviews=[] 
        self.father_stack=[]
        for line in self.lines:
            self.text = self.text + line
            if '<node ' in line :
                view=View(line,self.father_stack.copy())
                view.instance = self.findviewinstance(self.lines,view.resourceId,view.className,view.text)
                self.allviews.append(view)
                if len(self.father_stack)>0:
                    self.father_stack[len(self.father_stack)-1].add_child(view)
                self.father_stack.append(view)
                if '/>' in line:
                    allleafviews.append(view)
                    self.father_stack.pop()
            if '</node>' in line:
                self.father_stack.pop()
        allleafviews.sort(key = lambda x: x.line, reverse=False)
        return allleafviews

    