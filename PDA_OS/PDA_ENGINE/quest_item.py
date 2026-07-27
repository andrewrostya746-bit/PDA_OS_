import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.uix.modalview import ModalView
from kivy.graphics import Rectangle, Color
from kivy.core.audio import SoundLoader
from kivy.app import App
from config import PATH_SOUND_1, PATH_TEX, get_theme, load_settings


class QuestItem(BoxLayout):
    def __init__(self, title, desc, icon_path, marker_pos, marker_id, **kwargs):
        super().__init__(**kwargs)
        
        settings = load_settings()
        theme = get_theme(settings.get("theme", "dark_green"))
        
        self.marker_pos = marker_pos
        self.marker_id = marker_id
        self.title_text = title
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 75
        self.padding = 10
        self.spacing = 10

        with self.canvas.before:
            Color(*theme["button_bg"])
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(*theme["accent"])
            self.border = Rectangle(pos=self.pos, size=(self.width, 2))
        self.bind(pos=self._update, size=self._update)

        self.icon_view = KivyImage(source=icon_path, size_hint=(None, None),
                                   size=(50, 50), pos_hint={'center_y': 0.5})

        text_container = BoxLayout(orientation='vertical', size_hint_x=1)
        self.title_label = Label(
            text=f"[b]{title.upper()}[/b]", markup=True,
            color=theme["text_bright"], font_size='15sp'
        )
        self.desc_label = Label(
            text=desc, color=theme["text"], font_size='11sp'
        )
        text_container.add_widget(self.title_label)
        text_container.add_widget(self.desc_label)

        self.btn_box = BoxLayout(orientation='horizontal', size_hint_x=None,
                                 width=110, spacing=8, pos_hint={'center_y': 0.5})
        btn_complete = Button(
            text="", 
            background_normal=os.path.join(PATH_TEX, "complete.png"),
            background_color=theme["button_active"]
        )
        btn_failed = Button(
            text="", 
            background_normal=os.path.join(PATH_TEX, "failed.png"),
            background_color=theme["error"]
        )
        btn_complete.bind(on_release=lambda x: self.confirm_action('complete'))
        btn_failed.bind(on_release=lambda x: self.confirm_action('failed'))
        self.btn_box.add_widget(btn_complete)
        self.btn_box.add_widget(btn_failed)

        self.add_widget(self.icon_view)
        self.add_widget(text_container)
        self.add_widget(self.btn_box)

    def _get_pda(self):
        root = App.get_running_app().root
        if not root:
            return None
        if hasattr(root, 'map_engine'):
            return root
        for child in root.children:
            if hasattr(child, 'map_engine'):
                return child
        return None

    def _update(self, *args):
        self.bg.pos, self.bg.size = self.pos, self.size
        self.border.pos = self.pos
        self.border.size = (self.width, 2)

    def confirm_action(self, action_type):
        settings = load_settings()
        theme = get_theme(settings.get("theme", "dark_green"))
        
        view = ModalView(size_hint=(None, None), size=(280, 140),
                         background_color=(0, 0, 0, 0.95))
        box = BoxLayout(orientation='vertical', padding=12, spacing=8)
        box.add_widget(Label(
            text="Изменить статус задания?", font_size='15sp',
            bold=True, color=theme["text_bright"]
        ))

        btn_layout = BoxLayout(spacing=10)
        btn_yes = Button(text="ДА", background_normal='',
                        background_color=theme["button_active"], bold=True, font_size='13sp')
        btn_no = Button(text="НЕТ", background_normal='',
                       background_color=theme["error"], bold=True, font_size='13sp')

        def on_yes(*args):
            pda = self._get_pda()
            if pda and hasattr(pda, 'map_engine'):
                pda.map_engine.remove_marker(self.marker_id)
            try:
                sound = SoundLoader.load(PATH_SOUND_1)
                if sound: sound.play()
            except: pass
            if pda and hasattr(pda, 'add_history'):
                pda.add_history(f"{'Выполнено' if action_type=='complete' else 'Провалено'}: {self.title_text}")
            if pda and hasattr(pda, 'quest_screen'):
                pda.quest_screen.remove_widget(self)
            view.dismiss()

        btn_yes.bind(on_release=on_yes)
        btn_no.bind(on_release=lambda x: view.dismiss())
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        box.add_widget(btn_layout)
        view.add_widget(box)
        view.open()

    def on_touch_down(self, touch):
        if self.btn_box.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            pda = self._get_pda()
            if pda and hasattr(pda, 'switch_to_name') and hasattr(pda, 'map_engine'):
                pda.switch_to_name("КАРТА")
                pda.map_engine.focus_marker(self.marker_pos)
            return True
        return super().on_touch_down(touch)