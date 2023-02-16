import random
from property import Event
class Policy(object):

    def __init__(self,devices,app,emulator_path,android_system):
        
        self.app = app
        self.devices = devices
        self.emulator_path = emulator_path
        self.android_system = android_system
    
    def choice_event(self):
        pass

class RandomPolicy(Policy):
    def __init__(self,device,app,
                pro_click,pro_longclick,pro_scroll,pro_edit,pro_back,pro_home):
        
        self.pro_click = pro_click
        self.pro_longclick = pro_click+pro_longclick
        self.pro_scroll = pro_click+pro_longclick+pro_scroll
        self.pro_edit = pro_click+pro_longclick+pro_scroll+pro_edit
        self.pro_back = pro_click+pro_longclick+pro_scroll+pro_edit+pro_back
        self.pro_home = pro_click+pro_longclick+pro_scroll+pro_edit+pro_back+pro_home
        self.pro_all=pro_click+pro_longclick+pro_scroll+pro_edit+pro_back+pro_home
        self.app = app
        self.device = device
        
    def random_text(self):
        text_style=random.randint(0,8)
        text_length=random.randint(1,5)
        nums=["0","1","2","3","4","5","6","7","8","9"]
        letters=["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
        symbols=[",",".","!","?"]
        i=0
        random_string=""
        print("text_style:"+str(text_style))
        if text_style == 0:
            while i < text_length:
                now_num=nums[random.randint(0,len(nums)-1)]
                random_string=random_string+now_num
                i=i+1
        elif text_style == 1:
            while i < text_length:
                now_letters=letters[random.randint(0,len(nums)-1)]
                random_string=random_string+now_letters
                i=i+1
        elif text_style == 2:
            while i < text_length:
                s_style=random.randint(0,2)
                if s_style==0:
                    now_letters=nums[random.randint(0,len(nums)-1)]
                    random_string=random_string+now_letters
                elif s_style==1:
                    now_letters=letters[random.randint(0,len(letters)-1)]
                    random_string=random_string+now_letters
                elif s_style==2:
                    now_letters=symbols[random.randint(0,len(symbols)-1)]
                    random_string=random_string+now_letters
                i=i+1
        elif text_style == 3:
            country=["London","Paris","New York","Tokyo"]
            countrynum=random.randint(0,4)
            random_string=country[countrynum]
        elif text_style ==4:
            random_string=letters[random.randint(0,len(letters)-1)]
        elif text_style ==5:
            random_string=nums[random.randint(0,len(nums)-1)]
        elif text_style ==6:
            special_text=["www.baidu.com","www.google.com"]
            specialnum=random.randint(0,len(special_text)-1)
            random_string=special_text[specialnum]
        elif text_style ==7:
            random_string="10086"
        if random_string=="":
            random_string=" "
        return random_string

    def choice_event(self,device,event_count):
        event_type = random.randint(0,self.pro_all-1)
        inapplist=[self.app.package_name,"com.lbe.security.miui","com.google.android.packageinstaller","com.google.android.permissioncontroller","com.android.packageinstaller","com.android.permissioncontroller"]
        click_classname_lists=["android.widget.RadioButton","android.view.View","android.widget.ImageView","android.widget.View","android.widget.CheckBox","android.widget.Button","android.widget.Switch","android.widget.ImageButton","android.widget.TextView","android.widget.CheckedTextView","android.widget.TableRow","android.widget.EditText","android.support.v7.widget.ar"]
        click_classname_lists_important=["android.widget.CheckBox","android.widget.Button","android.widget.Switch"]
        click_package_lists=[self.app.package_name,"com.lbe.security.miui","com.google.android.apps.messaging","android","com.android.settings","com.google.android","com.google.android.packageinstaller",
        "com.google.android.inputmethod.latin","com.google.android.permissioncontroller","com.android.packageinstaller","com.android.permissioncontroller"]
        if str(self.device.get_current_app()) not in inapplist:
            backorstart = random.randint(0,5)
            print(self.device.get_current_app()+str(inapplist))
            if backorstart==0:
                event = Event("back",None,"",True,device)
            else:
                event = Event("start",None,"",True,device)
        elif event_type<self.pro_click:
            views=[]
            for view in device.screen.allleafviews:
                if view.className in click_classname_lists_important and view.package in click_package_lists :
                    views.append(view)
                if view.package in click_package_lists:
                    views.append(view)
            if len(views)>0:
                event_view_num = random.randint(0,len(views)-1)
                event_view = views[event_view_num]
                event = Event("click",event_view,"",True,device)
            else:
                print("no widget can be clicked")
                event = self.choice_event(device,event_count)
        elif event_type<self.pro_longclick:
            views=[]
            for view in device.screen.allleafviews:
                if view.className in click_classname_lists_important and view.package in click_package_lists :
                    views.append(view)
                if view.package in click_package_lists:
                    views.append(view)
            if len(views)>0:
                event_view_num = random.randint(0,len(views)-1)
                event_view = views[event_view_num]
                event = Event("longclick",event_view,"",True,device)
            else:
                print("no widget can be longclicked")
                event = self.choice_event(device,event_count)
        elif event_type<self.pro_scroll:
            views=[]
            for view in device.screen.allviews:
                if view.scrollable=="true" and view.package in click_package_lists:
                    views.append(view)
            if len(views)>0:
                event_view_num = random.randint(0,len(views)-1)
                event_view = views[event_view_num]
                direction_list = ["backward","forward","right","left"]
                direction_num = random.randint(0,len(direction_list)-1)
                event = Event("scroll_"+direction_list[direction_num],event_view,"",True,device)
            else:
                print("no widget can be scrolled")
                event = self.choice_event(device,event_count)
        elif event_type<self.pro_edit:
            views=[]
            for view in device.screen.allleafviews:
                if view.className == "android.widget.EditText":
                    views.append(view)
            if len(views)>0:
                event_view_num = random.randint(0,len(views)-1)
                event_view = views[event_view_num]
                text = self.random_text()
                event = Event("edit",event_view,text,True,device)
            else:
                print("no widget can be edited")
                event = self.choice_event(device,event_count)
        elif event_type<self.pro_back:
            event = Event("back",None,"",True,device)
        else:
            event = Event("home",None,"",True,device)
        return event
        

