import os
import time
import json
import multiprocessing
from kivy.app import App
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import ButtonBehavior
from kivymd.uix.behaviors import HoverBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.utils import get_color_from_hex
from kivy.uix.label import Label
from kivy.clock import Clock
from functools import partial
from kivy.core.audio import SoundLoader
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRaisedButton, MDRectangleFlatIconButton
from kivymd.uix.label import MDIcon
from kivy.core.window import Window
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import ILeftBody
from kivy.storage.jsonstore import JsonStore
from datetime import datetime

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
KIVY_PATH = os.path.join(DIRECTORY, "appui.kv")
SOUND_PATH = os.path.join(DIRECTORY, "assets/sounds")
DATA_PATH = os.path.join(DIRECTORY, "data.json")
CONGIG_PATH = "/home/kato/.config/safeeyes/safeeyes.json"
QUOTE = [{"name": "Go do 8 pushups!"}]
DATA = JsonStore(DATA_PATH)

BREAK_THEME = "#599A9C"
STUDY_THEME = "#DF645F"

BACKGROUND_BREAK_COLOR = "#468E91"
BACKGROUND_STUDY_COLOR = "#DB524D"

class Background(FloatLayout):
    ColorTheme = StringProperty(BACKGROUND_STUDY_COLOR)
    isStudy = True

    def __init__(self, **kwargs):
        super(). __init__ ()
        self.bind(ColorTheme=self.changebtnTheme)

    def changebtnTheme(self, *args):
        if self.isStudy:
            self.children[0].changeTheme(isStudy=False)
            self.children[1].changeTheme(isStudy=False)
            self.isStudy = False
        else:
            self.children[0].changeTheme(isStudy=True)
            self.children[1].changeTheme(isStudy=True)
            self.isStudy = True

    def restartClock(self, custom=False, *args):
        self.children[-1].restartClock(custom)

    def changeClock(self, Study, Break, LongBreak):
        self.children[-1].changeClock(Study, Break, LongBreak)

    def toggleDialog(self, *args):
        self.children[-1].toggleDialog()

    def changeTheme(self, reversed=False):
        if reversed:
            self.ColorTheme = BACKGROUND_BREAK_COLOR
        else:
            self.ColorTheme = BACKGROUND_STUDY_COLOR

class CustomDialog(MDDialog):
    pass

class customIcon(ILeftBody, MDIcon):
    pass

class Container(BoxLayout):
    widgets = []
    def __init__ (self, **kwargs):
        super(). __init__ ()
        self.widgets = [
            customGraphContainer(icon="clock-outline", text="default", followup="hours focused"),
            customGraphContainer(icon="calendar-today", text="default", followup="days accessed"),
            customGraphContainer(icon="fire", text="default", followup="current streak")
        ]
        self.bl = BoxLayout(orientation="horizontal", spacing="20dp", size_hint_y=None, height="100dp")
        self.add_widget(self.bl)
        for x in self.widgets: 
            self.bl.add_widget(x)

    def convert(self):
        return str(self.totalTime / 60)[0]

    def updateData(self):
        self.days =  str(DATA.get("days")["value"])
        self.streak = str(DATA.get("streak")["value"])
        self.totalTime = int(DATA.get("total_time")["value"])
        hours = self.convert()
        self.data = [hours, self.days, self.streak]
        for x in range(len(self.widgets)):
            self.widgets[x].updateData(self.data[x])

class customGraphContainer(FloatLayout):
    icon = StringProperty()
    text = StringProperty()
    followup = StringProperty()
    def __init__ (self, icon, text, followup, **kwargs):
        super(). __init__ ()
        self.icon = icon
        self.text = text
        self.followup = followup

    def updateData(self, text):
        self.text = text

class settingContent(BoxLayout):
    studyTime = str(DATA.get("study")["time"])
    breakTime = str(DATA.get("break")["time"])
    longbreakTime = str(DATA.get("long_break")["time"])

class Logo(FloatLayout):
    def __init__ (self, **kwargs):
        super(). __init__ ()
        self.logo = customIcon(icon="check-circle")
        self.add_widget(self.logo)


class settingBTN(ButtonBehavior, HoverBehavior, FloatLayout):
    buttonPad = 5
    newTime = [DATA.get("study")["time"], DATA.get("break")["time"], DATA.get("long_break")["time"]]
    ColorTheme = StringProperty(STUDY_THEME)

    def __init__ (self, **kwargs):
        super(). __init__ ()
        self.add_widget(customIcon(icon="cog"))
        self.add_widget(Label(text="Setting", font_size="17sp", pos_hint={"center_x": .6, "center_y":.5}))
        self.content = settingContent()
        self.dialog = MDDialog(
            type="custom",
            content_cls=self.content,
            buttons=[
                MDRaisedButton(
                    text="CANCEL",
                    on_release=self.on_cancel
                ),
                MDRaisedButton(
                    text="OK",
                    on_release=self.process
                ),
            ],
        )
        self.dialog.bind(on_open=self.toggleDialog)
        self.dialog.bind(on_dismiss=self.toggleDialog)

    def on_enter(self):
        Window.set_system_cursor("hand")

    def on_leave(self):
        Window.set_system_cursor("arrow")

    def changeTheme(self, isStudy=True):
        if isStudy:
            self.ColorTheme = STUDY_THEME
        else:
            self.ColorTheme = BREAK_THEME

    def toggleDialog(self, *args):
        self.parent.toggleDialog()

    def on_press(self):
        self.pos[1] -= self.buttonPad
        Window.bind(on_touch_up=self.checkOutpos)

    def on_release(self):
        self.pos[1] += self.buttonPad
        self.dialog.open()

    def on_cancel(self, *args):
        self.dialog.dismiss()

    def checkOutpos(self, *args):
        pos_x, pos_y =(Window.mouse_pos)
        if not (pos_x >= self.pos[0] and pos_x <= self.pos[0] + self.size[0] and pos_y >= self.pos[1] and pos_y <= self.pos[1] + self.size[1]):
            self.pos[1] += self.buttonPad
        Window.unbind(on_touch_up=self.checkOutpos)

    def checkInt(self, *args):
        fields = ["Study", "Break", "LongBreak"]
        testPassed = 0
        for x in fields:
            length = len(str(self.content.ids[x].text).strip())
            if length != 0:
                passed = True
                for y in range(length):
                    try:
                        int(str(self.content.ids[x].text)[y])
                    except:
                        passed = False
                        break
                if passed:
                    self.newTime[testPassed] = int(str(self.content.ids[x].text))
                    testPassed += 1
        if testPassed == 3:
            return True
        else:
            return False

    def writeChangedTime(self):
        DATA.put('study', time=self.newTime[0])
        DATA.put('break', time=self.newTime[1])
        DATA.put('long_break', time=self.newTime[2])

    def process(self, *args):
        if self.checkInt():
            self.parent.changeClock(self.newTime[0], self.newTime[1], self.newTime[2])
            self.parent.restartClock(custom=True)
            self.writeChangedTime()
            self.dialog.dismiss()

class reportBTN(ButtonBehavior, HoverBehavior, FloatLayout):
    buttonPad = 5
    ColorTheme = StringProperty(STUDY_THEME)
    def __init__ (self, **kwargs):
        super(). __init__ ()
        self.add_widget(customIcon(icon="chart-bar"))
        self.add_widget(Label(text="Report", font_size="17sp", pos_hint={"center_x": .6, "center_y":.5}))
        self.content = Container()
        self.dialog = MDDialog(
            type="custom",
            content_cls=self.content,
        )
        self.dialog.bind(on_open=self.toggleDialog)
        self.dialog.bind(on_dismiss=self.toggleDialog)

    def on_enter(self):
        Window.set_system_cursor("hand")

    def on_leave(self):
        Window.set_system_cursor("arrow")

    def toggleDialog(self, *args):
        self.parent.toggleDialog()

    def changeTheme(self, isStudy=True):
        if isStudy:
            self.ColorTheme = STUDY_THEME
        else:
            self.ColorTheme = BREAK_THEME

    def on_press(self):
        self.pos[1] -= self.buttonPad
        Window.bind(on_touch_up=self.checkOutpos)

    def on_release(self):
        self.pos[1] += self.buttonPad
        self.content.updateData()
        self.dialog.open()

    def checkOutpos(self, *args):
        pos_x, pos_y =(Window.mouse_pos)
        if not (pos_x >= self.pos[0] and pos_x <= self.pos[0] + self.size[0] and pos_y >= self.pos[1] and pos_y <= self.pos[1] + self.size[1]):
            self.pos[1] += self.buttonPad
        Window.unbind(on_touch_up=self.checkOutpos)

class skipBTN(ButtonBehavior, HoverBehavior ,MDIcon):
    hidden = BooleanProperty(True)

    def __init__(self, btn, **kwargs):
        super(). __init__()
        self.font_size = "50sp"
        self.btn = btn
        btn.bind(pos=self.update)
        self.dialog = CustomDialog(
            text="[color=#FCFCFC]Are you sure you want to finish the round early? (The remaining time will not be counted in the report.)[/color]",
            buttons=[
                MDRaisedButton(text="CANCEL", on_release=self.closeDialog, text_color=get_color_from_hex("#FCFCFC"), md_bg_color=get_color_from_hex("#242424")),
                MDRaisedButton(text="OK", on_release=self.skip_session, text_color=get_color_from_hex("#242424")),
            ],
        )
        self.dialog.bind(on_open=self.toggleDialog)
        self.dialog.bind(on_dismiss=self.toggleDialog)
        
    def on_enter(self):
        Window.set_system_cursor("hand")

    def on_leave(self):
        Window.set_system_cursor("arrow")

    def toggleDialog(self, *args):
        self.parent.toggleDialog()

    def update(self, *args):
        self.y = self.btn.y + (self.btn.size[1] / 2) - (self.size[1] / 2)
        self.x = self.btn.x + self.btn.size[0] + 20
    
    def closeDialog(self, *args):
        self.dialog.dismiss()

    def skip_session(self, *args):
        self.closeDialog()
        self.parent.skip_session()

    def hideWidget(self):
        if self.hidden == False:
            self.hidden = True
        else:
            self.hidden = False

    def on_release(self):
        self.dialog.open()

class ClockWidget(FloatLayout):
    Text = StringProperty("#1")
    Quote = StringProperty("Time to study!")

    ColorTheme = StringProperty(STUDY_THEME)

    dialogisOpen = BooleanProperty(False) #Literally any dialog that is open

    def __init__(self, **kwargs):
        super(). __init__()
        self.textClock = ClockTextWidget()
        self.startbtn = startBTN(self.textClock)
        self.skipbtn = skipBTN(self.startbtn)
        self.add_widget(self.textClock)
        self.add_widget(self.startbtn)
        self.add_widget(self.skipbtn)

    def restartClock(self, custom=False):
        self.textClock.restartClock(custom)

    def skip_session(self):
        self.textClock.skip_session()
        self.toggleBTNadvanced()

    def hideWidget(self):
        self.skipbtn.hideWidget()

    def toggleDialog(self, *args):
        if self.dialogisOpen:
            self.dialogisOpen = False
        else:
            self.dialogisOpen = True

    def changeLocalTheme(self, reversed=False):
        if reversed:
            self.ColorTheme = BREAK_THEME
        else:
            self.ColorTheme = STUDY_THEME

    def changeClock(self, Study, Break, LongBreak):
        self.textClock.changeClock(Study, Break, LongBreak)

    def toggleBTN(self):
        self.startbtn.changeState()

    def toggleBTNadvanced(self):
        self.startbtn.on_release()

    def assignTime(self):
        self.startbtn.assignTime()

    def updateCycle(self, num, Break=False):
        self.Text = f"#{num}"
        if Break:
            self.Quote = "Time for a break!"
            self.changeLocalTheme(reversed=True)
            self.parent.changeTheme(reversed=True)
        else:
            self.Quote = "Time to study!"
            self.changeLocalTheme(reversed=False)
            self.parent.changeTheme(reversed=False)


class ClockTextWidget(Label):
    STUDY = [DATA.get("study")["time"], 0]
    BREAK = [DATA.get("break")["time"], 0]
    LONG_BREAK = [DATA.get("long_break")["time"], 0]

    minutes = NumericProperty(STUDY[0])
    seconds = NumericProperty(STUDY[1])
    deltaSec = STUDY[1]

    cycles = 0
    isSTUDY = True
    alarm = SoundLoader.load(os.path.join(SOUND_PATH, "alarm2.mp3"))

    def __init__(self, **kwargs):
        super(). __init__()
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def startClock(self):
        start_time = time.time()
        self.event = Clock.schedule_interval(partial(self.updateClock, start_time), 1)

    def stopClock(self):
        self.event.cancel()

    def updateTotalMins(self):
        total_time = int(DATA.get("total_time")["value"])
        DATA.put("total_time", value=total_time+1)

    def updateClock(self, time_start, *args):
        if self.seconds == 0:
            if self.minutes != 0:
                self.minutes -= 1
                self.seconds = 60
                if self.isSTUDY:
                    self.updateTotalMins()
            else:
                self.stopClock()
                self.restartClock()
                self.parent.toggleBTN()
                return None

        self.seconds = int(self.seconds - 1)
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def changeBreak(self):
        self.minutes = self.BREAK[0]
        self.seconds = self.BREAK[1]
        self.deltaSec = self.BREAK[1]
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def changeLongBreak(self):
        self.minutes = self.LONG_BREAK[0]
        self.seconds = self.LONG_BREAK[1]
        self.deltaSec = self.LONG_BREAK[1]
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def changeStudy(self):
        self.minutes = self.STUDY[0]
        self.seconds = self.STUDY[1]
        self.deltaSec = self.STUDY[1]
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def skip_session(self):
        self.restartClock()

    def changeClock(self, Study, Break, LongBreak):
        self.STUDY[0] = Study
        self.BREAK[0] = Break
        self.LONG_BREAK[0] = LongBreak

    def restartClock(self, custom=False):
        if custom:
            self.parent.assignTime()
            if (self.cycles + 1) % 4 == 0 and self.isSTUDY == False:
                self.changeLongBreak()
            elif not self.isSTUDY:
                self.changeBreak()
            else:
                self.changeStudy()
        else:
            if self.isSTUDY:
                if (self.cycles+1) % 4  == 0:
                    self.changeLongBreak()
                    self.startBreak()
                    self.parent.updateCycle(self.cycles+1, Break=True)
                else:
                    self.changeBreak()
                    self.startBreak()
                    self.parent.updateCycle(self.cycles+1, Break=True)
                self.isSTUDY = False
            else:
                self.isSTUDY = True
                self.changeStudy()
                self.playAlarm()
                self.cycles += 1
                self.parent.updateCycle(self.cycles+1, Break=False)

    def playAlarm(self):
        self.alarm.unload()
        self.alarm = SoundLoader.load(os.path.join(SOUND_PATH, "alarm2.mp3"))
        self.alarm.seek(0)
        self.alarm.play()

    def startBreak(self):
        self.playAlarm()
        with open(CONGIG_PATH, 'r+') as file:
            data = json.load(file)
            data['long_break_duration'] = self.minutes * 60 + self.seconds
            data['long_break_interval'] = 999999
            data['long_breaks'] = QUOTE
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
        app = App.get_running_app()
        app.setupThread(self.showBreak)
        self.breakTimeout()

    def breakTimeout(self):
        Clock.schedule_once(self.killDaemon, (self.minutes * 60 + self.seconds)+10)

    def killDaemon(self, *args):
        os.system("killall safeeyes")

    def showBreak(self):
        self.killDaemon()
        os.system("safeeyes -t")


class CustomLabel(Label):
    Text = StringProperty("[b]START[/b]")

    def __init__(self, **kwargs):
        super(). __init__()
        # self.pos = self.parent.pos

    def changeText(self, *args):
        if self.Text == "[b]START[/b]":
            self.Text = "[b]STOP[/b]"
        else:
            self.Text = "[b]START[/b]"


class startBTN(ButtonBehavior, HoverBehavior, FloatLayout):
    buttonPad = 10
    buttonPressed = False
    buttonPadRemote = NumericProperty(buttonPad)
    buttonText = StringProperty("START")
    btnsound = SoundLoader.load(os.path.join(SOUND_PATH, "button.mp3"))
    def __init__(self, clock):
        super(). __init__()
        self.clock = clock
        self.label = CustomLabel()
        self.ids.buttonText.add_widget(self.label)
        
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
    
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if not self.parent.dialogisOpen:
            if keycode[1] == 'spacebar':
                self.on_release()

    def checkOutpos(self, *args):
        if not self.buttonPressed:
            pos_x, pos_y =(Window.mouse_pos)
            if not (pos_x >= self.pos[0] and pos_x <= self.pos[0] + self.size[0] and pos_y >= self.pos[1] and pos_y <= self.pos[1] + self.size[1]):
                self.buttonPadRemote = self.buttonPad
        Window.unbind(on_touch_up=self.checkOutpos)

    def on_enter(self):
        Window.set_system_cursor("hand")

    def on_leave(self):
        Window.set_system_cursor("arrow")

    def on_press(self):
        Window.bind(on_touch_up=self.checkOutpos)
        self.buttonPadRemote = 0

    def changeState(self, reversed=False, *args):
        if not reversed:
            self.buttonPressed = False
            self.buttonPadRemote = self.buttonPad
            self.label.changeText()
            self.parent.hideWidget()
        else:
            self.buttonPressed = True
            self.buttonPadRemote = 0
            self.label.changeText()
            self.parent.hideWidget()

    def assignTime(self):
        if self.buttonPressed:
            self.changeState()
            self.clock.stopClock()
        self.btnsound.unload()
        self.btnsound = SoundLoader.load(os.path.join(SOUND_PATH, "button.mp3"))
        self.btnsound.seek(0)
        self.btnsound.play()

    def on_release(self):
        if not self.buttonPressed:
            self.changeState(reversed=True)
            self.clock.startClock()
        else:
            self.changeState()
            self.clock.stopClock()
        self.btnsound.unload()
        self.btnsound = SoundLoader.load(os.path.join(SOUND_PATH, "button.mp3"))
        self.btnsound.seek(0)
        self.btnsound.play()


class MainApp(MDApp):
    threads = []

    def setupThread(self, func):
        thread = multiprocessing.Process(target=func)
        thread.start()
        self.threads.append(thread)

    def on_start(self):
        now = str(datetime.today().strftime('%Y-%m-%d'))
        Pass = str(DATA.get("yesterday")["value"])
        days = int(DATA.get("days")["value"])
        streak = int(DATA.get("streak")["value"])
        if now != Pass:
            DATA.put("days", value=days+1)
            try:
                dis = int(now[0:1]) - int(Pass[0:1])
                if dis == 1:
                    DATA.put("streak", value=streak+1)
                else:
                    DATA.put("streak", value=0)
            except:
                pass
        DATA.put("yesterday", value=now)

    def on_stop(self):
        for i in self.threads:
            i.terminate()
        os.system("killall safeeyes")

    def build(self):
        return Builder.load_file(KIVY_PATH)


if __name__ == "__main__":
    MainApp().run()
