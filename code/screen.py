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

    def print(self):
        if self.line != "":
            print("line: "+self.line)


class Screen(object):

    def __init__(self, lines):
        self.lines = lines
        self.text = ""
        self.allviews = [] 
        self.allleafviews=self.get_view()

    def get_view(self):
        allleafviews=[] 
        self.father_stack=[]
        for line in self.lines:
            self.text = self.text + line
            if '<node ' in line :
                view=View(line,self.father_stack.copy())
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

    