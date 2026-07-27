import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
from kivy.app import App
from config import PATH_TEX, get_theme, load_settings


class LegendRow(BoxLayout):
    def __init__(self, img_name, text, **kwargs):
        super().__init__(**kwargs)
        
        settings = load_settings()
        theme = get_theme(settings.get("theme", "dark_green"))
        
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = 50
        self.spacing = 10
        self.padding = (18, 3, 8, 3)
        self.img_path = os.path.join(PATH_TEX, img_name)
        
        if not os.path.exists(self.img_path):
            alt = self.img_path.replace(".png", ".jpg")
            if os.path.exists(alt):
                self.img_path = alt

        self.icon = KivyImage(source=self.img_path, size_hint=(None, None), size=(35, 35))
        self.label = Label(
            text=text, font_size='13sp', color=theme["text"],
            halign='left', valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        
        self.add_widget(self.icon)
        self.add_widget(self.label)
        self._touch_time = None

    def _get_pda(self):
        root = App.get_running_app().root
        if not root:
            return None
        if hasattr(root, 'select_marker'):
            return root
        for child in root.children:
            if hasattr(child, 'select_marker'):
                return child
        return None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_time = Clock.schedule_once(self._long_press, 0.5)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._touch_time:
            Clock.unschedule(self._touch_time)
        return super().on_touch_up(touch)

    def _long_press(self, dt):
        pda = self._get_pda()
        if pda:
            pda.select_marker(self.img_path, self)