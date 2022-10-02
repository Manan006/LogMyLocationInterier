import kivy
from kivy.properties import StringProperty
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.storage.jsonstore import JsonStore
from kivy.uix.button import Button
import requests
import json
from kivy.clock import mainthread
from plyer import gps
from kivy.utils import platform
## TEMP STUFF. WILL BE ADDED TO CONFIG FILE AT THE TIME OF FINALIZATION
app_url = "https://api.lml.dotcodes.dev"


class MainApp(App):
    gps_location = StringProperty()
    gps_status = StringProperty('Click Start to get GPS location updates')

    def request_android_permissions(self):
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([Permission.ACCESS_COARSE_LOCATION,
                             Permission.ACCESS_FINE_LOCATION], callback)

    def build(self):
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'

        if platform == "android":
            print("gps.py: Android detected. Requesting permissions")
            self.request_android_permissions()

        self.title = 'LogMyLocation'
        self.screen = BoxLayout(orientation ='vertical')
        self.db = JsonStore('data.json')
        if self.db.exists("sessionid"):
            self.logged_in()
        else:
            self.screen.add_widget(Label(text="Username:",halign="center",font_size=50))
            self.username= TextInput(multiline=False, font_size=50)
            self.screen.add_widget(self.username)
            self.screen.add_widget(Label(text="Password:",halign="center",font_size=50))
            self.password= TextInput(multiline=False, font_size=50,password=True)
            self.screen.add_widget(self.password)
            self.login_btn = Button(text ="Login",font_size=50)
            self.login_btn.bind(on_press = self.login_button)
            self.screen.add_widget(self.login_btn)
            self.invalid_credentials=Label(text="Invalid Credentials",halign="center",font_size=30,color="red")
        return self.screen
    
    def start(self,minDistance=1,minTime=180000):
        gps.start(minTime, minDistance)
    def stop(self):
        gps.stop()
    @mainthread
    def on_location(self, **kwargs):
        if not self.db.exists("sessionid"):
            return
        remote.send_location(self.db.get("sessionid")['id'],str({'lat':kwargs['lat'],'lon':kwargs['lon']}))
    @mainthread
    def on_status(self, stype, status):
        self.gps_status = 'type={}\n{}'.format(stype, status)
        print(self.gps_status,"1#2$5^7")

    def on_pause(self):
        gps.stop()
        return True

    def on_resume(self):
        gps.start(1000, 0)
        pass
    def logged_in(self):
        self.screen.clear_widgets()
        self.screen.add_widget(Label(text="Welcome We're logging your location",halign="center",font_size=70))
        self.check_logs_btn = Button(text ="Check Logs",font_size=20)
        self.check_logs_btn.bind(on_press = self.check_logs)
        if platform == "android":
            print("gps.py: Android detected. Requesting permissions")
            self.request_android_permissions()
        try:
            gps.configure(on_location=self.on_location,
                          on_status=self.on_status)
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.gps_status = 'GPS is not implemented for your platform'
        # self.screen.add_widget(self.check_logs_btn)

    def login_button(self, instance):
        username = self.username.text
        password = self.password.text
        data = remote.login(username,password)
        print(data)
        if data[0]:
            self.db.put("sessionid",id=data[1])
            self.logged_in()
        else:
            if self.invalid_credentials not in self.screen.children:
                print(self.screen.children)
                self.screen.add_widget(self.invalid_credentials)
        return self.screen
    
    def check_logs(self,instance):
        self.screen.clear_widgets()
        return self.screen

class remote():
    def login(username,password):
        response= requests.get(app_url+"/login",params={"username":username,"password":password})
        print(response)
        if response.status_code == 200:
            return (True,json.loads(response.content)["sessionid"])
        return (False,json.loads(response.content)["message"])
    def send_location(sessionid,location):
        response= requests.put(app_url+"/send_location",params={"location":location,"sessionid":sessionid})
        print(response)
        if response.status_code == 200:
            return True
        return False

if __name__ == "__main__":
    MainApp().run()
