import os
import time
import json
import multiprocessing
from kivy.app import App
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import ButtonBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.utils import get_color_from_hex
from kivy.uix.label import Label
from kivy.clock import Clock
from functools import partial
from kivy.core.audio import SoundLoader
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDIcon

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
KIVY_PATH = os.path.join(DIRECTORY, "appui.kv")
SOUND_PATH = os.path.join(DIRECTORY, "assets/sounds")
CONGIG_PATH = "/home/kato/.config/safeeyes/safeeyes.json"
QUOTE = [{"name": "Go do 8 pullups!"}]
STUDY = [0, 2]
BREAK = [10, 0]
LONG_BREAK = [15, 0]
print(DIRECTORY)


class Background(FloatLayout):
    BREAK_COLOR = "#468E91"
    STUDY_COLOR = "#DB524D"
    ColorTheme = StringProperty(STUDY_COLOR)

    def changeTheme(self, reversed=False):
        if reversed:
            self.ColorTheme = self.BREAK_COLOR
        else:
            self.ColorTheme = self.STUDY_COLOR


class skipBTN(ButtonBehavior, MDIcon):
    hidden = BooleanProperty(True)

    def __init__(self, btn, **kwargs):
        super(). __init__()
        self.font_size = "50sp"
        self.btn = btn
        btn.bind(pos=self.update)

    def update(self, *args):
        self.y = self.btn.y + (self.btn.size[1] / 2) - (self.size[1] / 2)
        self.x = self.btn.x + self.btn.size[0] + 20

    def hideWidget(self):
        if self.hidden == False:
            self.hidden = True
        else:
            self.hidden = False

    def on_release(self):
        self.parent.skip_session()


class ClockWidget(FloatLayout):
    Text = StringProperty("#1")
    Quote = StringProperty("Time to study!")
    BREAK_THEME = "#599A9C"
    STUDY_THEME = "#DF645F"
    ColorTheme = StringProperty(STUDY_THEME)

    def __init__(self, **kwargs):
        super(). __init__()
        self.textClock = ClockTextWidget()
        self.startbtn = startBTN(self.textClock)
        self.skipbtn = skipBTN(self.startbtn)
        self.add_widget(self.textClock)
        self.add_widget(self.startbtn)
        self.add_widget(self.skipbtn)

    def skip_session(self):
        self.textClock.skip_session()
        self.toggleBTNadvanced()

    def hideWidget(self):
        self.skipbtn.hideWidget()

    def changeLocalTheme(self, reversed=False):
        if reversed:
            self.ColorTheme = self.BREAK_THEME
        else:
            self.ColorTheme = self.STUDY_THEME

    def toggleBTN(self):
        self.startbtn.changeState()

    def toggleBTNadvanced(self):
        self.startbtn.on_release()

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
    minutes = NumericProperty(STUDY[0])
    seconds = NumericProperty(STUDY[1])
    deltaSec = STUDY[1]
    cycles = 0
    isSTUDY = True

    def __init__(self, **kwargs):
        super(). __init__()
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def startClock(self):
        start_time = time.time()
        self.event = Clock.schedule_interval(
            partial(self.updateClock, start_time), 1)

    def stopClock(self):
        self.event.cancel()

    def updateClock(self, time_start, *args):
        if self.seconds == 0:
            if self.minutes != 0:
                self.minutes -= 1
                self.deltaSec = 59

            else:
                self.stopClock()
                self.restartClock()
                self.parent.toggleBTN()
                return None  # Just to exit the function

        self.seconds = int(self.deltaSec - (time.time() - time_start))
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def changeBreak(self):
        self.minutes = BREAK[0]
        self.seconds = BREAK[1]
        self.deltaSec = BREAK[1]
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def changeLongBreak(self):
        self.minutes = LONG_BREAK[0]
        self.seconds = LONG_BREAK[1]
        self.deltaSec = LONG_BREAK[1]
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def changeStudy(self):
        self.minutes = STUDY[0]
        self.seconds = STUDY[1]
        self.deltaSec = STUDY[1]
        self.text = '%02d:%02d' % (self.minutes, self.seconds)

    def skip_session(self):
        self.restartClock()

    def restartClock(self):
        if self.isSTUDY:
            if self.cycles % 4 == 0 and self.cycles != 0:
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
            self.cycles += 1
            self.parent.updateCycle(self.cycles+1, Break=False)

    def startBreak(self):
        sound = SoundLoader.load(os.path.join(SOUND_PATH, "alarm2.mp3"))
        sound.play()
        with open(CONGIG_PATH, 'r+') as file:
            data = json.load(file)
            data['long_break_duration'] = self.minutes * 60 + self.seconds
            data['long_break_interval'] = 1
            data['long_breaks'] = QUOTE
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
        app = App.get_running_app()
        app.setupThread(self.showBreak)

    def showBreak(self):
        os.system("killall safeeyes")
        os.system("safeeyes -t")


class CustomLabel(Label):
    Text = StringProperty("START")

    def __init__(self, **kwargs):
        super(). __init__()
        # self.pos = self.parent.pos

    def changeText(self, *args):
        if self.Text == "START":
            self.Text = "STOP"
        else:
            self.Text = "START"


class startBTN(ButtonBehavior, FloatLayout):
    buttonPad = 10
    buttonPressed = False
    buttonPadRemote = NumericProperty(buttonPad)
    buttonText = StringProperty("START")

    def __init__(self, clock):
        super(). __init__()
        self.clock = clock
        self.label = CustomLabel()
        self.ids.buttonText.add_widget(self.label)

    def on_press(self):
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

    def on_release(self):
        if not self.buttonPressed:
            self.changeState(reversed=True)
            self.clock.startClock()
        else:
            self.changeState()
            self.clock.stopClock()
        btnsound = SoundLoader.load(os.path.join(SOUND_PATH, "button.mp3"))
        btnsound.play()


class MainApp(MDApp):
    threads = []

    def setupThread(self, func):
        thread = multiprocessing.Process(target=func)
        thread.start()
        self.threads.append(thread)

    def on_stop(self):
        for i in self.threads:
            i.terminate()
        os.system("killall safeeyes")

    def build(self):
        return Builder.load_file(KIVY_PATH)


if __name__ == "__main__":
    MainApp().run()
