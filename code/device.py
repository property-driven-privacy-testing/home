import os
import subprocess
import uiautomator2 as u2

class Device(object):

    def __init__(self, device_serial):
        self.device_serial=device_serial
        self.now_logcat = ""
        self.screen = None
        self.nowscreenshotpath = ""
    
    def connect(self):
        self.use = u2.connect(self.device_serial)
        self.use.implicitly_wait(5.0)
    
    def stop_app(self,app):
        self.use.press("back")
        self.use.app_stop(app.package_name)

    def clear_app(self,app):
        self.use.app_clear(app.package_name)
        self.use.app_stop(app.package_name)
        if app.package_name == "com.ichi2.anki":
            self.use.shell(["su"])
            self.use.shell(["rm","-r","/storage/emulated/0/AnkiDroid"])
    
    def update_screen(self,screen,nowscreenshotpath):
        self.last_screen = self.screen
        self.screen = screen
        self.nowscreenshotpath = nowscreenshotpath

    def get_current_app(self):
        self.current_app=self.use.app_current()['package']
        return self.current_app
    
    def start_app(self,app):
        # self.use.app_start(app.package_name)
        print("adb"+"-s"+self.device_serial+"shell"+"am"+"start"+"-n"+app.package_name+"/"+app.main_activity)
        subprocess.run(["adb","-s",self.device_serial,"shell","am","start","-n",app.package_name+"/"+app.main_activity], stdout=subprocess.PIPE)
        import time
        time.sleep(1)
        return True

    def update_logcat(self,logcat_lines):
        self.last_logcat = self.now_logcat
        self.now_logcat = logcat_lines

    def drag(self,text):
        positions = text.split(",")
        self.use.drag(int(positions[0]),int(positions[1]),int(positions[2]),int(positions[3]))

    def close_keyboard(self):
        # subprocess.run(["adb","-s",self.device_serial,"shell","input","keyevent","111"], stdout=subprocess.PIPE)
        if "emulator" in self.device_serial:
            self.use.shell(["input","keyevent","111"])
        else:
            self.use.press("back")

    def add_file(self,resource_path,resource,path):
        subprocess.run(["adb","-s",self.device_serial,"logcat","-c"], stdout=subprocess.PIPE)
        subprocess.run(["adb","-s",self.device_serial,"push",resource_path+"/"+resource,path], stdout=subprocess.PIPE)

    def log_crash(self,path):
        print("adb -s "+self.device_serial+" logcat -b crash >"+path)
        os.popen("adb -s "+self.device_serial+" logcat -b crash >"+path)

    def clear_log(self):
        print("adb -s "+self.device_serial+" logcat -c")
        self.use.shell(["logcat","-c"])

    def install_app(self,app):
        print(app)
        subprocess.run(["adb","-s",self.device_serial,"install",app], stdout=subprocess.PIPE)
    
    def click(self,view):
        try:
            if view.text !="" and view.resourceId !="":
                self.use(resourceId=view.resourceId,text=view.text).click()
            elif view.text !="" and view.className !="":
                try:
                    self.use(className=view.className,text=view.text).click()
                except Exception as ex:
                    self.use(className=view.className,textContains=view.text).click()
            elif view.text !="" and view.instance !=0:
                self.use(instance=view.instance,text=view.text).click()
            elif view.text !="":
                try:
                    self.use(text=view.text).click()
                except Exception as ex:
                    self.use(textContains=view.text).click()
            elif view.description !="":
                try:
                    self.use(description=view.description).click()
                except Exception as ex:
                    self.use(descriptionContains=view.description).click()
            elif view.resourceId !="" and view.instance!="":
                self.use(resourceId=view.resourceId,instance=view.instance).click()
            elif view.resourceId !="":
                self.use(resourceId=view.resourceId).click()
            elif view.xpath !="":
                self.use.xpath(view.xpath).click()
            elif view.x!=-1 and view.y!=-1:
                self.use.click(view.x ,view.y)
            elif view.className!="" and view.instance!="":
                self.use(className=view.className,instance=view.instance).click()
            else:
                self.use(className=view.className).click()
            return True
        except Exception as ex:
            print(ex)
            return False

    def longclick(self,view):
        try:
            if view.text !="" and view.resourceId !="":
                self.use(resourceId=view.resourceId,text=view.text).long_click()
            elif view.text !="" and view.className !="":
                self.use(className=view.className,text=view.text).long_click()
            elif view.text !="":
                try:
                    self.use(text=view.text).long_click()
                except Exception as ex:
                    self.use(textContains=view.text).long_click()
            elif view.description !="":
                try:
                    self.use(description=view.description).long_click()
                except Exception as ex:
                    self.use(descriptionContains=view.description).long_click()
            elif view.resourceId !="" and view.instance!="":
                self.use(resourceId=view.resourceId,instance=view.instance).long_click()
            elif view.resourceId !="":
                self.use(resourceId=view.resourceId).long_click()
            elif view.xpath !="":
                self.use.xpath(view.xpath).long_click()
            elif view.x!=-1 and view.y!=-1:
                self.use.long_click(view.x ,view.y)
            elif view.className!="" and view.instance!="":
                self.use(className=view.className,instance=view.instance).long_click()
            else:
                self.use(className=view.className,packageName=view.package).long_click()
            return True
        except Exception as ex:
            print(ex)
            return False
    
    def edit(self,view,text):
        try:
            if view.text !="" and view.resourceId !="":
                self.use(resourceId=view.resourceId,text=view.text).set_text(text)
            elif view.text !="":
                self.use(text=view.text).set_text(text)
            elif view.description !="":
                self.use(description=view.description).set_text(text)
            elif view.resourceId !="" and view.instance!="":
                self.use(resourceId=view.resourceId,instance=view.instance).set_text(text)
            elif view.resourceId !="":
                self.use(resourceId=view.resourceId).set_text(text)
            elif view.xpath !="":
                self.use.xpath(view.xpath).set_text(text)
            elif view.className!="" and view.instance!="":
                self.use(className=view.className,instance=view.instance).set_text(text)
            else:
                self.use(className=view.className,packageName=view.package).set_text(text)
            return True
        except Exception as ex:
            print(ex)
            return False
        
    def scroll(self,view,action):
        try:
            if action == "scroll_backward":
                print("scroll backward"+"\n")
                if view.resourceId !="" and view.className!="":
                    self.use(className=view.className,resourceId=view.resourceId).scroll.vert.backward(steps=100)
                elif view.resourceId !="" :
                    self.use(resourceId=view.resourceId).scroll.vert.backward(steps=100)
                elif view.className !="" :
                    self.use(className=view.className).scroll.vert.backward(steps=100)
                else:
                    self.use(scrollable=True).scroll.vert.backward(steps=100)
            elif action == "scroll_forward":
                print("scroll forward"+"\n")
                if view.resourceId !="" and view.className!="":
                    self.use(className=view.className,resourceId=view.resourceId).scroll.vert.forward(steps=100)
                elif view.resourceId !="" :
                    self.use(resourceId=view.resourceId).scroll.vert.forward(steps=100)
                elif view.className !="" :
                    self.use(className=view.className).scroll.vert.forward(steps=100)
                else:
                    self.use(scrollable=True).scroll.vert.forward(steps=100)
            elif action == "scroll_right":
                print("scroll right"+"\n")
                if view.resourceId !="" and view.className!="":
                    self.use(className=view.className,resourceId=view.resourceId).scroll.horiz.toEnd(max_swipes=10)
                elif view.resourceId !="" :
                    self.use(resourceId=view.resourceId).scroll.horiz.toEnd(max_swipes=10)
                elif view.className !="" :
                    self.use(className=view.className).scroll.horiz.toEnd(max_swipes=10)
                else:
                    self.use(scrollable=True).scroll.horiz.toEnd(max_swipes=10)
            elif action == "scroll_left":
                print("scroll left"+"\n")
                if view.resourceId !="" and view.className!="":
                    self.use(className=view.className,resourceId=view.resourceId).scroll.horiz.toBeginning(max_swipes=10)
                elif view.resourceId !="" :
                    self.use(resourceId=view.resourceId).scroll.horiz.toBeginning(max_swipes=10)
                elif view.className !="" :
                    self.use(className=view.className).scroll.horiz.toBeginning(max_swipes=10)
                else:
                    self.use(scrollable=True).scroll.horiz.toBeginning(max_swipes=10)
            return True
        except Exception as ex:
            print(ex)
            return False

    def scrollto(self,text):
        nowscreen =self.use.dump_hierarchy()
        lastscreen=""
        while not self.use.exists(textContains=text) and lastscreen != nowscreen:
            import copy
            lastscreen =copy.copy(nowscreen)
            self.use(scrollable=True).scroll.vert.forward()
            nowscreen =self.use.dump_hierarchy()
    
    def rightscrollto(self,widget,text):
        nowscreen =self.use.dump_hierarchy()
        lastscreen=""
        while not self.use.exists(text=text) and lastscreen != nowscreen:
            lastscreen =nowscreen
            nowscreen =self.use.dump_hierarchy()
            if widget == None:
                self.use(scrollable=True).scroll.vert.forward()
            elif widget.resourceId !="":
                self.use(resourceId=widget.resourceId).scroll.horiz.toEnd(max_swipes=10)

