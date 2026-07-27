import time
import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.stencilview import StencilView
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.graphics import Rectangle, Color, Line
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.app import App

from config import (
    PATH_TEX, PATH_SOUND_1, PATH_SOUND_2, PATH_ARROW, PATH_CHANGE,
    load_settings, save_settings, get_theme, save_app_data, load_app_data
)
from map_display import MapDisplay
from quest_item import QuestItem
from legend_row import LegendRow
from killtrack import KillTrackScreen
from settings import SettingsScreen
from contacts import ContactsScreen, ContactSelectPanel


class FilterToggle(BoxLayout):
    def __init__(self, label_text, filter_attr, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40
        self.spacing = 8
        self.filter_attr = filter_attr
        self.lbl = Label(text=label_text, color=(0, 0.9, 0, 1), font_size='13sp',
                         halign='left', valign='middle', size_hint_x=0.6)
        self.btn_yes = Button(text="ДА", background_color=(0, 0.5, 0, 1), bold=True, size_hint_x=0.2, font_size='11sp')
        self.btn_no = Button(text="НЕТ", background_color=(0.3, 0.1, 0.1, 1), bold=True, size_hint_x=0.2, font_size='11sp')
        self.btn_yes.bind(on_release=self.set_yes)
        self.btn_no.bind(on_release=self.set_no)
        self.add_widget(self.lbl)
        self.add_widget(self.btn_yes)
        self.add_widget(self.btn_no)

    def _get_pda(self):
        try:
            root = App.get_running_app().root
            if hasattr(root, 'map_engine'): return root
            for child in root.children:
                if hasattr(child, 'map_engine'): return child
        except: pass
        return None

    def set_yes(self, *args):
        pda = self._get_pda()
        if pda:
            setattr(pda.map_engine, self.filter_attr, True)
            self._update_buttons()
            pda.map_engine.refresh_markers()

    def set_no(self, *args):
        pda = self._get_pda()
        if pda:
            setattr(pda.map_engine, self.filter_attr, False)
            self._update_buttons()
            pda.map_engine.refresh_markers()

    def _update_buttons(self):
        pda = self._get_pda()
        if not pda: return
        is_active = getattr(pda.map_engine, self.filter_attr)
        self.btn_yes.background_color = (0, 0.8, 0, 1) if is_active else (0.2, 0.2, 0.2, 1)
        self.btn_no.background_color = (0.8, 0, 0, 1) if not is_active else (0.2, 0.2, 0.2, 1)


class LoginScreen(FloatLayout):
    def __init__(self, on_success_callback, **kwargs):
        super().__init__(**kwargs)
        self.on_success = on_success_callback
        self.settings = load_settings()
        self.theme = get_theme(self.settings.get("theme", "dark_green"))
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            Color(0, 0, 0, 1)
            Rectangle(pos=self.pos, size=self.size)
        center_box = BoxLayout(orientation='vertical', size_hint=(None, None),
                               size=(350, 280), pos_hint={'center_x': 0.5, 'center_y': 0.5},
                               spacing=15, padding=25)
        center_box.add_widget(Label(text="PDA OS v2.0", font_size='26sp', bold=True,
                                    color=self.theme["text_bright"], size_hint_y=None, height=45))
        center_box.add_widget(Label(text="ВВЕДИТЕ ПАРОЛЬ", font_size='14sp',
                                    color=self.theme["text"], size_hint_y=None, height=25))
        self.password_input = TextInput(password=True, multiline=False, font_size='22sp',
                                        size_hint_y=None, height=45,
                                        background_color=(0.1, 0.12, 0.1, 1),
                                        foreground_color=self.theme["text_bright"],
                                        halign='center', hint_text="****")
        self.password_input.bind(on_text_validate=self.check_password)
        center_box.add_widget(self.password_input)
        btn_enter = Button(text="ВХОД", size_hint_y=None, height=45,
                           background_normal='', background_color=self.theme["button_active"],
                           bold=True, font_size='16sp', color=self.theme["text_bright"])
        btn_enter.bind(on_release=self.check_password)
        center_box.add_widget(btn_enter)
        self.error_label = Label(text="", color=self.theme["error"], size_hint_y=None, height=20, font_size='13sp')
        center_box.add_widget(self.error_label)
        self.add_widget(center_box)
        Clock.schedule_once(lambda dt: setattr(self.password_input, 'focus', True), 0.3)

    def check_password(self, *args):
        if self.password_input.text.strip() == self.settings.get("password", "1111"):
            self.parent.remove_widget(self)
            self.on_success()
        else:
            self.error_label.text = "НЕВЕРНЫЙ ПАРОЛЬ!"
            self.password_input.text = ""
            self.password_input.focus = True


class PDA_Interface(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = load_settings()
        self.theme = get_theme(self.settings.get("theme", "dark_green"))
        self.selected_marker = None
        self.active_row = None
        self.selected_quest_btn = None
        self.placing_quest = False
        self.sb_width = 340
        self.current_tab = self.settings.get("startup_tab", "КАРТА")
        self.sidebar_visible = False
        self.selected_contact_name = ""
        self.selected_contact_mac = ""

        with self.canvas.before:
            Color(*self.theme["bg_main"])
            self.bg_rect = Rectangle(size=Window.size, pos=(0, 0))
            Color(*self.theme["bg_top"])
            self.top_rect = Rectangle()
            Color(*self.theme["accent"])
            self.top_line = Rectangle()

        self.content_container = FloatLayout(size_hint=(1, 1))
        self.add_widget(self.content_container)

        self.map_screen = FloatLayout()
        self.map_area = StencilView(size_hint=(None, None))
        self.map_engine = MapDisplay()
        self.map_area.add_widget(self.map_engine)
        self.map_screen.add_widget(self.map_area)

        self.mgrs_label = Label(text="КУРСОР: ОЖИДАНИЕ...", markup=True,
                                color=self.theme["text"], font_size='12sp',
                                size_hint=(None, None), pos_hint={'x': 0.02, 'y': 0.02})
        self.device_coords_label = Label(text="УСТРОЙСТВО: ОЖИДАНИЕ...", markup=True,
                                         color=self.theme["text"], font_size='12sp',
                                         size_hint=(None, None), pos_hint={'right': 0.98, 'y': 0.02})
        self.map_screen.add_widget(self.mgrs_label)
        self.map_screen.add_widget(self.device_coords_label)

        if os.path.exists(PATH_CHANGE):
            self.btn_filter = Button(size_hint=(None, None), size=(42, 42),
                                     pos_hint={'x': 0.02, 'top': 0.98},
                                     background_normal=PATH_CHANGE, background_color=(0, 0.5, 0, 1))
        else:
            self.btn_filter = Button(text="Ф", size_hint=(None, None), size=(42, 42),
                                     pos_hint={'x': 0.02, 'top': 0.98},
                                     background_normal='', background_color=(0, 0.5, 0, 1),
                                     bold=True, font_size='18sp')
        self.btn_filter.bind(on_release=self.toggle_filter_panel)
        self.map_screen.add_widget(self.btn_filter)

        self.quest_scroll = ScrollView(pos_hint={'top': 0.85}, size_hint=(1, 0.75))
        self.quest_screen = BoxLayout(orientation='vertical', size_hint_y=None, padding=15, spacing=12)
        self.quest_screen.bind(minimum_height=self.quest_screen.setter('height'))
        self.quest_scroll.add_widget(self.quest_screen)

        self.history_screen = ScrollView(pos_hint={'top': 0.85}, size_hint=(1, 0.75))
        self.history_list = BoxLayout(orientation='vertical', size_hint_y=None, padding=15, spacing=8)
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        self.history_screen.add_widget(self.history_list)

        self.killtrack_screen = KillTrackScreen(pda_interface=self)
        self.contacts_screen = ContactsScreen(pda_interface=self)
        self.settings_screen = SettingsScreen(pda_interface=self)

        saved_data = load_app_data()
        if saved_data:
            self._load_saved_data(saved_data)

        self._show_startup_tab()

        self.top_tabs = BoxLayout(size_hint=(None, None), size=(900, 40), spacing=6)
        for name in ["КАРТА", "ЗАДАНИЯ", "ИСТОРИЯ", "KillTrack", "КОНТАКТЫ", "НАСТРОЙКИ"]:
            b = Button(text=name, background_normal='', bold=True, font_size='11sp')
            b.bind(on_release=self.switch_tab)
            self.top_tabs.add_widget(b)
        self.add_widget(self.top_tabs)
        self.update_tab_button_visuals()

        menu_path = os.path.join(PATH_TEX, "menu.png")
        if os.path.exists(menu_path):
            self.btn_menu = Button(size_hint=(None, None), size=(70, 70),
                                   background_normal=menu_path, background_color=(0, 0.5, 0, 1))
        else:
            self.btn_menu = Button(text="МЕНЮ", size_hint=(None, None), size=(70, 70),
                                   background_normal='', background_color=self.theme["button_active"],
                                   bold=True, color=self.theme["text_bright"], font_size='12sp')
        self.btn_menu.bind(on_release=self.handle_main_button)
        self.add_widget(self.btn_menu)

        self._build_sidebar()
        self._build_filter_panel()
        self._build_editor()

        self.bind(size=self._do_layout)
        self._apply_sound_settings()
        Window.bind(on_request_close=self._on_close)

    def _load_saved_data(self, data):
        if data.get('markers'):
            self.map_engine.markers = data['markers']
            self.map_engine.refresh_markers()
        if data.get('quests'):
            for quest in data['quests']:
                item = QuestItem(quest['title'], quest['desc'], quest['icon_path'],
                                 tuple(quest['marker_pos']), quest['marker_id'])
                self.quest_screen.add_widget(item)
        if data.get('history'):
            for entry in data['history']:
                self._add_history_text(entry)
        if data.get('tracked_macs') and hasattr(self, 'killtrack_screen'):
            self.killtrack_screen.tracked_macs = data['tracked_macs']
        if data.get('heatmap_points') and hasattr(self, 'killtrack_screen'):
            self.killtrack_screen.heatmap_points = data['heatmap_points']
        if data.get('markers') or data.get('quests'):
            self.add_history(f"Загружено: {len(data.get('markers', []))} меток, {len(data.get('quests', []))} заданий")

    def _on_close(self, *args):
        self._save_all_data()

    def _save_all_data(self):
        quests = []
        for child in self.quest_screen.children:
            if isinstance(child, QuestItem):
                quests.append({'title': child.title_text, 'desc': child.desc_label.text,
                               'icon_path': child.icon_view.source, 'marker_pos': list(child.marker_pos),
                               'marker_id': child.marker_id})
        history = []
        for child in self.history_list.children:
            if isinstance(child, Label): history.append(child.text)
        tracked_macs = self.killtrack_screen.tracked_macs if hasattr(self, 'killtrack_screen') else []
        heatmap_points = self.killtrack_screen.heatmap_points if hasattr(self, 'killtrack_screen') else []
        save_app_data(self.map_engine.markers, quests, history, tracked_macs, heatmap_points)

    def _show_startup_tab(self):
        self.content_container.clear_widgets()
        startup = self.settings.get("startup_tab", "КАРТА")
        if startup == "КАРТА": self.content_container.add_widget(self.map_screen)
        elif startup == "ЗАДАНИЯ": self.content_container.add_widget(self.quest_scroll)
        elif startup == "ИСТОРИЯ": self.content_container.add_widget(self.history_screen)
        elif startup == "KillTrack": self.content_container.add_widget(self.killtrack_screen)
        elif startup == "КОНТАКТЫ": self.content_container.add_widget(self.contacts_screen)
        elif startup == "НАСТРОЙКИ": self.content_container.add_widget(self.settings_screen)

    def _apply_sound_settings(self):
        self.sound_volume = self.settings.get("sound_volume", 0.7)
        self.sound_enabled = self.settings.get("sound_enabled", True)

    def play_sound(self, sound_path):
        if not self.sound_enabled: return
        try:
            sound = SoundLoader.load(sound_path)
            if sound:
                sound.volume = self.sound_volume
                sound.play()
        except: pass

    def _build_sidebar(self):
        self.sidebar = RelativeLayout(size_hint=(None, None), size=(self.sb_width, Window.height - 120))
        self.sidebar.y = 40
        with self.sidebar.canvas.before:
            Color(0, 0, 0, 0.9)
            self.side_bg = Rectangle(pos=(0, 0), size=self.sidebar.size)
            Color(*self.theme["border"])
            self.side_line = Line(rectangle=(0, 0, self.sidebar.width, self.sidebar.height), width=2)
        self.sidebar.bind(size=self._update_sidebar_canvas)
        self.scroll = ScrollView(size_hint=(1, None), pos_hint={'top': 0.88}, do_scroll_x=False)
        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=(0, 8))
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        legend_data = [
            ("home.png", "Дом"), ("big_location.png", "Город/Село"),
            ("localion.png", "Точка"), ("fishing.png", "Рыбацкое место"),
            ("common_shron.png", "Обычный тайник"), ("yellow_shron.png", "Редкий хабар"),
            ("red_shron.png", "Засекреченный хабар"), ("neizvestno.png", "Неотведаная локацыя"),
            ("shelter.png", "Бомбоубежище")
        ]
        for img, txt in legend_data:
            self.list_container.add_widget(LegendRow(img, txt))
        self.scroll.add_widget(self.list_container)
        self.sidebar.add_widget(self.scroll)
        self.sidebar.add_widget(Label(text="МАРКЕРЫ ТАКТИКИ", font_size='18sp', bold=True,
                                      color=self.theme["text"], size_hint=(1, None), height=50,
                                      pos_hint={'top': 0.98}))
        self.btn_close = Button(text="X", size_hint=(None, None), size=(40, 40),
                                pos_hint={'right': 0.98, 'top': 0.98},
                                background_normal='', background_color=(0.6, 0, 0, 1), bold=True, font_size='14sp')
        self.btn_close.bind(on_release=self.toggle_sidebar)
        self.sidebar.add_widget(self.btn_close)
        self.add_widget(self.sidebar)

    def _build_filter_panel(self):
        self.filter_panel = BoxLayout(orientation='vertical', size_hint=(None, None),
                                      size=(310, 280), padding=12, spacing=8)
        with self.filter_panel.canvas.before:
            Color(0, 0, 0, 0.92)
            self.filter_bg = Rectangle(pos=self.filter_panel.pos, size=self.filter_panel.size)
            Color(*self.theme["border"])
            self.filter_border = Line(rectangle=(self.filter_panel.x, self.filter_panel.y,
                                                 self.filter_panel.width, self.filter_panel.height), width=2)
        self.filter_panel.bind(pos=self._update_filter_canvas, size=self._update_filter_canvas)
        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        header_box.add_widget(Label(text="ФИЛЬТР КАРТЫ", font_size='16sp', bold=True, color=self.theme["text"]))
        btn_close_filter = Button(text="X", size_hint=(None, None), size=(35, 35),
                                  background_normal='', background_color=(0.6, 0, 0, 1), bold=True)
        btn_close_filter.bind(on_release=self.toggle_filter_panel)
        header_box.add_widget(btn_close_filter)
        self.filter_panel.add_widget(header_box)
        self.filter_panel.add_widget(FilterToggle("ЛОКАЦИИ", "filter_locations"))
        self.filter_panel.add_widget(FilterToggle("ПОПУТНЫЕ ЗАДАНИЯ", "filter_side_quests"))
        self.filter_panel.add_widget(FilterToggle("КЛЮЧЕВЫЕ МЕТКИ", "filter_key_markers"))
        self.filter_panel.add_widget(FilterToggle("ТАЙНИКИ", "filter_stashes"))

    def _update_filter_canvas(self, *args):
        self.filter_bg.pos = self.filter_panel.pos
        self.filter_bg.size = self.filter_panel.size
        self.filter_border.rectangle = (self.filter_panel.x, self.filter_panel.y,
                                        self.filter_panel.width, self.filter_panel.height)

    def toggle_filter_panel(self, *args):
        if self.filter_panel in self.map_screen.children:
            self.map_screen.remove_widget(self.filter_panel)
        else:
            self.filter_panel.pos = (self.width * 0.02, self.height * 0.52)
            self.map_screen.add_widget(self.filter_panel)

    def _update_sidebar_canvas(self, *args):
        self.side_bg.size = self.sidebar.size
        self.side_line.rectangle = (0, 0, self.sidebar.width, self.sidebar.height)

    def _add_history_text(self, text):
        self.history_list.add_widget(Label(text=text, markup=True, size_hint_y=None, height=30,
                                           font_size='13sp', halign='left'))

    def add_history(self, text):
        t = time.strftime("%H:%M:%S")
        self.history_list.add_widget(Label(text=f"[color=00ff00][{t}][/color] {text}",
                                           markup=True, size_hint_y=None, height=30,
                                           font_size='13sp', halign='left'))
        self._save_all_data()

    def select_marker(self, texture_path, row_widget):
        self.cancel_selection()
        self.selected_marker = texture_path
        self.active_row = row_widget
        with row_widget.canvas.after:
            Color(*self.theme["text_bright"])
            row_widget.sel_border = Line(rectangle=(row_widget.x, row_widget.y, row_widget.width, row_widget.height), width=2)
        self.toggle_sidebar()

    def cancel_selection(self):
        if self.active_row: self.active_row.canvas.after.clear()
        self.selected_marker = None
        self.active_row = None

    def select_quest_type(self, path, btn):
        self.selected_marker = path
        self.selected_quest_btn = btn
        self.btn_m.canvas.after.clear()
        self.btn_nm.canvas.after.clear()
        with btn.canvas.after:
            Color(*self.theme["text_bright"])
            Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=2)

    def _show_contact_select(self, *args):
        def on_contact_selected(name, mac):
            self.selected_contact_name = name
            self.selected_contact_mac = mac
            if name:
                self.selected_contact_label.text = f"Привязан контакт: {name}"
            else:
                self.selected_contact_label.text = "Без привязки к контакту"

        panel = ContactSelectPanel(on_contact_selected=on_contact_selected)
        panel.pos = (self.width - 360, self.height * 0.15)
        self.add_widget(panel)

    def save_quest(self, *args):
        if not self.selected_marker:
            self.select_quest_type(os.path.join(PATH_TEX, "main_quest.png"), self.btn_m)
        self.placing_quest = True
        self.toggle_editor()
        self.switch_to_name("КАРТА")

    def finalize_quest_creation(self, marker_id, marker_pos):
        title = self.in_name.text.strip() or "Контракт"
        desc = self.in_desc.text.strip() or "Детали отсутствуют."

        if self.selected_contact_name:
            desc += f"\n\nЦель: {self.selected_contact_name}"
            if self.selected_contact_mac:
                desc += f"\nMAC: {self.selected_contact_mac}"

        for m in self.map_engine.markers:
            if m['id'] == marker_id:
                m['quest_title'] = title
                m['quest_desc'] = desc
                break

        self.play_sound(PATH_SOUND_2)

        item = QuestItem(title, desc, self.selected_marker, marker_pos, marker_id)
        self.quest_screen.add_widget(item)
        self.add_history(f"Новое задание: {title}")

        if self.selected_contact_name:
            self.add_history(f"Цель задания: {self.selected_contact_name}")

        self.in_name.text = ""
        self.in_desc.text = ""
        self.selected_contact_label.text = ""
        self.selected_contact_name = ""
        self.selected_contact_mac = ""
        self.btn_m.canvas.after.clear()
        self.btn_nm.canvas.after.clear()
        self.selected_quest_btn = None
        self.selected_marker = None
        self.placing_quest = False

        Clock.schedule_once(lambda dt: self.switch_to_name("ЗАДАНИЯ"), 0.1)

    def handle_main_button(self, *args):
        if self.current_tab == "КАРТА":
            self.toggle_sidebar()
        elif self.current_tab == "ЗАДАНИЯ":
            self.toggle_editor()
        elif self.current_tab == "КОНТАКТЫ":
            if hasattr(self, 'contacts_screen'):
                self.contacts_screen._show_scan_results()
        else:
            self.toggle_sidebar()

    def switch_to_name(self, name):
        for b in self.top_tabs.children:
            if b.text == name: self.switch_tab(b)

    def switch_tab(self, btn):
        if btn.text == self.current_tab and len(self.content_container.children) > 0: return
        if hasattr(self, 'map_engine'): self.map_engine.hide_tooltip()
        self.content_container.clear_widgets()
        self.current_tab = btn.text
        if btn.text == "КАРТА": self.content_container.add_widget(self.map_screen)
        elif btn.text == "ЗАДАНИЯ": self.content_container.add_widget(self.quest_scroll)
        elif btn.text == "ИСТОРИЯ": self.content_container.add_widget(self.history_screen)
        elif btn.text == "KillTrack": self.content_container.add_widget(self.killtrack_screen)
        elif btn.text == "КОНТАКТЫ": self.content_container.add_widget(self.contacts_screen)
        elif btn.text == "НАСТРОЙКИ": self.content_container.add_widget(self.settings_screen)
        self.update_tab_button_visuals()

    def update_tab_button_visuals(self):
        for b in self.top_tabs.children:
            if b.text == self.current_tab:
                b.background_color = self.theme["button_active"]
                b.color = self.theme["text_bright"]
            else:
                b.background_color = self.theme["button_bg"]
                b.color = self.theme["text"]

    def toggle_sidebar(self, *args):
        self.sidebar_visible = not self.sidebar_visible
        target_x = (self.width - self.sb_width) if self.sidebar_visible else self.width
        Animation.stop_all(self.sidebar)
        Animation(x=target_x, duration=0.2, t='out_quad').start(self.sidebar)

    def toggle_editor(self, *a):
        if self.editor.parent: self.remove_widget(self.editor)
        else: self.add_widget(self.editor)

    def _do_layout(self, *args):
        self.map_area.size = (self.width - 80, self.height - 130)
        self.map_area.pos = (40, 40)
        self.map_engine.size = self.map_area.size
        self.map_engine.pos = self.map_area.pos
        if not getattr(self, '_map_initialized', False) and self.width > 100:
            self._map_initialized = True
            Clock.schedule_once(lambda dt: self.map_engine.auto_center_map(), 0.1)
        else:
            self.map_engine.trigger_update()
        self.bg_rect.size = self.size
        self.top_rect.pos = (0, self.height - 90)
        self.top_rect.size = (self.width, 90)
        self.top_line.pos = (0, self.height - 90)
        self.top_line.size = (self.width, 2)
        self.top_tabs.pos = (self.width/2 - 450, self.height - 68)
        self.btn_menu.pos = (self.width - 110, 50)
        self.sidebar.height = self.height - 120
        self.sidebar.y = 40
        self.sidebar.x = (self.width - self.sb_width) if self.sidebar_visible else self.width
        self.scroll.height = self.sidebar.height - 100
        if hasattr(self, 'ed_bg'):
            self.ed_bg.size = self.size
            self.ed_bg.pos = (-self.editor.x, -self.editor.y)

    def _build_editor(self):
        self.editor = FloatLayout(size_hint=(0.75, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with self.editor.canvas.before:
            Color(0, 0, 0, 0.95)
            self.ed_bg = Rectangle(size=Window.size, pos=(-Window.width, -Window.height))
        btn_close_ed = Button(text="X", size_hint=(None, None), size=(50, 50),
                              pos_hint={'right': 0.98, 'top': 0.98},
                              background_normal='', background_color=(0.7, 0, 0, 1), font_size='16sp')
        btn_close_ed.bind(on_release=self.toggle_editor)
        self.editor.add_widget(btn_close_ed)

        ed_box = BoxLayout(orientation='vertical', size_hint=(0.9, 0.85),
                           pos_hint={'center_x': 0.5, 'center_y': 0.48}, spacing=10)

        self.in_name = TextInput(hint_text="Название задания...", size_hint_y=None, height=45,
                                 background_color=(0.1, 0.12, 0.1, 1), foreground_color=(0, 1, 0, 1),
                                 font_size='14sp')
        self.in_desc = TextInput(hint_text="Описание миссии...",
                                 background_color=(0.1, 0.12, 0.1, 1), foreground_color=(0, 0.9, 0, 1),
                                 size_hint_y=0.3)

        type_box = BoxLayout(size_hint_y=None, height=70, spacing=12, padding=(30, 0))

        main_quest_path = os.path.join(PATH_TEX, "main_quest.png")
        side_quest_path = os.path.join(PATH_TEX, "not_main_quest.png")

        if os.path.exists(main_quest_path):
            self.btn_m = Button(background_normal=main_quest_path, size_hint=(None, 1), width=70,
                                background_color=(0, 0.6, 0, 1))
        else:
            self.btn_m = Button(text="ОСН", size_hint=(None, 1), width=70, background_normal='',
                                background_color=(0, 0.6, 0, 1), bold=True, font_size='11sp')

        if os.path.exists(side_quest_path):
            self.btn_nm = Button(background_normal=side_quest_path, size_hint=(None, 1), width=70,
                                 background_color=(0.6, 0.4, 0, 1))
        else:
            self.btn_nm = Button(text="ПОБ", size_hint=(None, 1), width=70, background_normal='',
                                 background_color=(0.6, 0.4, 0, 1), bold=True, font_size='11sp')

        self.btn_m.bind(on_release=lambda x: self.select_quest_type(main_quest_path, self.btn_m))
        self.btn_nm.bind(on_release=lambda x: self.select_quest_type(side_quest_path, self.btn_nm))

        type_box.add_widget(self.btn_m)
        type_box.add_widget(self.btn_nm)

        if os.path.exists(os.path.join(PATH_TEX, "menu.png")):
            self.btn_contact = Button(
                background_normal=os.path.join(PATH_TEX, "menu.png"),
                size_hint=(None, 1),
                width=70,
                background_color=(0, 0.3, 0.5, 1)
            )
        else:
            self.btn_contact = Button(
                text="CONT", size_hint=(None, 1), width=70,
                background_normal='', background_color=(0, 0.3, 0.5, 1),
                bold=True, font_size='10sp', color=(1, 1, 1, 1)
            )
        self.btn_contact.bind(on_release=self._show_contact_select)
        type_box.add_widget(self.btn_contact)

        ed_box.add_widget(self.in_name)
        ed_box.add_widget(self.in_desc)
        ed_box.add_widget(type_box)

        self.selected_contact_label = Label(
            text="", color=(0, 0.9, 0, 1), size_hint_y=None, height=22, font_size='12sp', halign='center'
        )
        ed_box.add_widget(self.selected_contact_label)

        btn_save = Button(text="ПРИНЯТЬ ЗАДАНИЕ", size_hint_y=None, height=55,
                          background_normal='', background_color=(0, 0.5, 0, 1), bold=True,
                          color=(1, 1, 1, 1), font_size='14sp')
        btn_save.bind(on_release=self.save_quest)
        ed_box.add_widget(btn_save)

        self.editor.add_widget(ed_box)