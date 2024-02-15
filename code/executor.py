import time
import subprocess

class Executor(object):

    def __init__(self,app,device1,device2):
        self.app = app
        self.device1 = device1
        self.device2 = device2
    
    def close(self,device):
        inapplist=[self.app.package_name,"com.lbe.security.miui","com.google.android.packageinstaller","com.google.android.permissioncontroller","com.android.packageinstaller","com.android.permissioncontroller"]
        if str(device.get_current_app()) not in inapplist:
            import random
            backorstart = random.randint(0,3)
            print(device.get_current_app()+str(inapplist))
            if backorstart==0:
                device.use.press("back")
            else:
                device.start_app(self.app)
    
    def execute_event(self,device,event,num):
        try:
            print("------------------")
            if event.action == "click":
                print("click"+event.view.line+"\n")
                device.click(event.view)
            elif event.action == "longclick":
                print("longclick"+event.view.line+"\n")
                device.longclick(event.view)
            elif event.action == "edit":
                print("edit"+event.view.line+"\n")
                device.edit(event.view,event.text)
            elif event.action == "drag":
                print("drag"+event.text+"\n")
                device.drag(event.text)
            elif event.action == "back":
                print("back"+"\n")
                device.use.press("back")
            elif event.action == "home":
                device.use.press("home")
                print("home"+"\n") 
            elif event.action == "naturalscreen":
                print("naturalscreen"+"\n")
                device.use.set_orientation("n")
            elif event.action == "leftscreen":
                print("leftscreen"+"\n")
                device.use.set_orientation("l")
            elif event.action == "start":
                if event.data=="":
                    print("start"+"\n")
                    device.stop_app(self.app)
                    device.start_app(self.app)
                else:
                    subprocess.run(["adb","-s",device.device_serial,"shell","am","start","-n",event.data], stdout=subprocess.PIPE)
            elif event.action == "stop":
                print("stop")
                device.stop_app(self.app)
            elif event.action == "clear":
                print("clear")
                device.clear_app(self.app)
            elif event.action == "sleep":
                print("sleep")
                time.sleep(int(event.text))
            elif event.action == "scrollto":
                print("scrollto::"+event.text)
                device.scrollto(event.text)
            elif "scroll" in event.action:
                device.scroll(event.view,event.action)
            print(device.device_serial+":end execute\n")
            return True
        except Exception as ex:
            if num ==0:
                print(ex)
                return self.execute_event(device,event,1)
            else:
                print(ex)
                return False

    def execute(self,event,num):
        # self.close()
        device = event.device
        try:
            execute = False
            print("------------------")
            if event.action == "click":
                print("click"+"\n")
                execute = device.click(event.widget)
            elif event.action == "longclick":
                print("longclick"+"\n")
                execute = device.longclick(event.widget)
            elif event.action == "edit":
                print("edit"+"\n")
                execute = device.edit(event.widget,event.text)
            elif event.action == "back":
                print("back"+"\n")
                device.use.press("back")
                execute = True
            elif event.action == "home":
                device.use.press("home")
                print("home"+"\n") 
                execute = True
            elif event.action == "naturalscreen":
                print("naturalscreen"+"\n")
                device.use.set_orientation("n")
                execute = True
            elif event.action == "leftscreen":
                print("leftscreen"+"\n")
                device.use.set_orientation("l")
                execute = True
            elif event.action == "start":
                device.stop_app(self.app)
                device.start_app(self.app)
                execute = True
            elif event.action == "stop":
                print("stop")
                device.stop_app(self.app)
                execute = True
            elif event.action == "clear":
                print("clear")
                device.clear_app(self.app)
                execute = True
            elif event.action == "sleep":
                print("sleep")
                time.sleep(int(event.text))
                execute = True
            elif event.action == "scrollto":
                print("scrollto::"+event.text)
                device.scrollto(event.text)
                execute = True
            elif event.action == "rightscrollto":
                print("rightscrollto")
                device.rightscrollto(event.widget,event.text)
                execute = True
            elif "scroll" in event.action:
                execute = device.scroll(event.widget,event.action)
            if execute == True:
                print(device.device_serial+":end execute\n")
                wait_time = 0
                while device.use(className="android.widget.ProgressBar").exists and wait_time<5:
                    wait_time = wait_time+1
                    time.sleep(1)
                time.sleep(1)
                return True
            else:
                if num ==0:
                    self.close(device)
                    return self.execute(event,1)
                else:
                    return False
        except Exception as ex:
            if num ==0:
                print(ex)
                self.close(device)
                return self.execute(event,1)
            else:
                print(ex)
                return False
   