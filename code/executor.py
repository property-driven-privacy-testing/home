from pydoc import classname
import time
import subprocess

class Executor(object):

    def __init__(self,app,device1,device2):
        self.app = app
        self.device1 = device1
        self.device2 = device2
        
    def execute(self,event,num):
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
                print("scrollto")
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
                while device.use(className="android.widget.ProgressBar").exists and wait_time<1:
                    wait_time = wait_time+1
                    time.sleep(1)
                time.sleep(1)
                return True
            else:
                return False
        except Exception as ex:
            if num ==0:
                print(ex)
                return self.execute(event,1)
            else:
                print(ex)
                return False
   