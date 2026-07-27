import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.graphics import Rectangle, Color, Line
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.app import App

from config import (
    PATH_TEX, PATH_SOUND_1, PATH_SOUND_2,
    load_settings, save_settings, get_theme, THEMES, DEFAULT_SETTINGS
)


class SettingsScreen(FloatLayout):
    """Экран настроек PDA OS"""
    
    def __init__(self, pda_interface, **kwargs):
        super().__init__(**kwargs)
        self.pda = pda_interface
        self.settings = load_settings()
        self._build_ui()
    
    def _build_ui(self):
        theme = get_theme(self.settings.get("theme", "dark_green"))
        
        with self.canvas.before:
            Color(*theme["bg_main"])
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # Верхняя полоса
        with self.canvas.before:
            Color(*theme["bg_top"])
            self.top_rect = Rectangle()
            Color(*theme["accent"])
            self.top_line = Rectangle()
        
        title = Label(
            text="НАСТРОЙКИ",
            font_size='20sp',
            bold=True,
            color=theme["text_bright"],
            size_hint=(1, None),
            height=45,
            pos_hint={'top': 0.98}
        )
        self.add_widget(title)
        
        # Основной контейнер
        main_box = BoxLayout(
            orientation='horizontal',
            size_hint=(0.95, 0.82),
            pos_hint={'center_x': 0.5, 'center_y': 0.46},
            spacing=12
        )
        
        # Левое меню категорий
        self.menu = BoxLayout(
            orientation='vertical',
            size_hint_x=0.28,
            spacing=4,
            padding=(0, 8)
        )
        
        categories = [
            ("ЗВУК", self._show_sound_settings),
            ("ТЕМА", self._show_theme_settings),
            ("ПАРОЛЬ", self._show_password_settings),
            ("GPS", self._show_gps_settings),
            ("СИСТЕМА", self._show_system_settings)
        ]
        
        for cat_name, callback in categories:
            btn = Button(
                text=cat_name,
                size_hint_y=None,
                height=40,
                background_normal='',
                background_color=theme["button_bg"],
                color=theme["text"],
                halign='left',
                valign='middle',
                padding=(12, 5),
                font_size='12sp',
                bold=True
            )
            btn.bind(on_release=callback)
            self.menu.add_widget(btn)
        
        main_box.add_widget(self.menu)
        
        # Правая панель контента
        self.content_panel = BoxLayout(
            orientation='vertical',
            size_hint_x=0.72,
            spacing=8,
            padding=12
        )
        
        with self.content_panel.canvas.before:
            Color(*theme["panel_bg"])
            self.panel_bg = Rectangle(pos=self.content_panel.pos, size=self.content_panel.size)
            Color(*theme["border"])
            self.panel_border = Line(
                rectangle=(self.content_panel.x, self.content_panel.y,
                          self.content_panel.width, self.content_panel.height),
                width=1.5
            )
        
        self.content_panel.bind(pos=self._update_panel, size=self._update_panel)
        
        self.settings_content = BoxLayout(
            orientation='vertical',
            size_hint_y=0.9,
            spacing=8
        )
        self.content_panel.add_widget(self.settings_content)
        
        # Кнопки сохранения
        btn_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=35,
            spacing=8
        )
        
        btn_save = Button(
            text="СОХРАНИТЬ",
            background_normal='',
            background_color=theme["button_active"],
            bold=True,
            font_size='11sp'
        )
        btn_save.bind(on_release=self._save_all_settings)
        btn_box.add_widget(btn_save)
        
        btn_default = Button(
            text="ПО УМОЛЧАНИЮ",
            background_normal='',
            background_color=(0.4, 0.3, 0, 1),
            bold=True,
            font_size='11sp'
        )
        btn_default.bind(on_release=self._reset_settings)
        btn_box.add_widget(btn_default)
        
        self.content_panel.add_widget(btn_box)
        
        main_box.add_widget(self.content_panel)
        self.add_widget(main_box)
        
        self.bind(size=self._do_layout)
        self._show_sound_settings()
    
    def _do_layout(self, *args):
        self.top_rect.pos = (0, self.height - 90)
        self.top_rect.size = (self.width, 90)
        self.top_line.pos = (0, self.height - 90)
        self.top_line.size = (self.width, 2)
    
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def _update_panel(self, *args):
        self.panel_bg.pos = self.content_panel.pos
        self.panel_bg.size = self.content_panel.size
        self.panel_border.rectangle = (
            self.content_panel.x, self.content_panel.y,
            self.content_panel.width, self.content_panel.height
        )
    
    def _clear_content(self):
        self.settings_content.clear_widgets()
    
    def _get_theme(self):
        return get_theme(self.settings.get("theme", "dark_green"))
    
    # ============ ЗВУК ============
    
    def _show_sound_settings(self, *args):
        self._clear_content()
        theme = self._get_theme()
        
        self.settings_content.add_widget(Label(
            text="НАСТРОЙКА ЗВУКА",
            font_size='15sp',
            bold=True,
            color=theme["text_bright"],
            size_hint_y=None,
            height=30
        ))
        
        sound_toggle_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        sound_toggle_box.add_widget(Label(
            text="Звук:", color=theme["text"], size_hint_x=0.5, halign='right', valign='middle', font_size='13sp'
        ))
        self.sound_switch = Switch(active=self.settings.get("sound_enabled", True), size_hint_x=0.5)
        sound_toggle_box.add_widget(self.sound_switch)
        self.settings_content.add_widget(sound_toggle_box)
        
        vol_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        vol_box.add_widget(Label(
            text="Громкость:", color=theme["text"], size_hint_x=0.3, halign='right', valign='middle', font_size='13sp'
        ))
        self.vol_slider = Slider(min=0, max=100, value=self.settings.get("sound_volume", 0.7) * 100,
                                 size_hint_x=0.5, value_track=True, value_track_color=theme["button_active"])
        self.vol_label = Label(text=f"{int(self.vol_slider.value)}%", color=theme["text_bright"],
                               size_hint_x=0.2, font_size='12sp')
        self.vol_slider.bind(value=lambda s, v: setattr(self.vol_label, 'text', f'{int(v)}%'))
        vol_box.add_widget(self.vol_slider)
        vol_box.add_widget(self.vol_label)
        self.settings_content.add_widget(vol_box)
        
        btn_test = Button(
            text="ТЕСТ ЗВУКА", size_hint_y=None, height=36,
            background_normal='', background_color=theme["button_active"], bold=True, font_size='12sp'
        )
        btn_test.bind(on_release=self._test_sound)
        self.settings_content.add_widget(btn_test)
    
    def _test_sound(self, *args):
        try:
            sound = SoundLoader.load(PATH_SOUND_1)
            if sound:
                sound.volume = self.vol_slider.value / 100
                sound.play()
                self.pda.add_history("Тест звука")
        except:
            pass
    
    # ============ ТЕМА ============
    
    def _show_theme_settings(self, *args):
        self._clear_content()
        theme = self._get_theme()
        
        self.settings_content.add_widget(Label(
            text="ВЫБОР ТЕМЫ", font_size='15sp', bold=True,
            color=theme["text_bright"], size_hint_y=None, height=30
        ))
        
        self.settings_content.add_widget(Label(
            text=f"Текущая: {theme['name']}", color=theme["text"], size_hint_y=None, height=22, font_size='12sp'
        ))
        
        theme_scroll = ScrollView(do_scroll_x=False, size_hint_y=0.7)
        theme_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=6)
        theme_list.bind(minimum_height=theme_list.setter('height'))
        
        for theme_key, theme_data in THEMES.items():
            btn = Button(
                text=theme_data["name"],
                size_hint_y=None,
                height=42,
                background_normal='',
                background_color=theme_data["button_bg"],
                color=theme_data["text_bright"],
                halign='left',
                valign='middle',
                padding=(15, 5),
                font_size='12sp',
                bold=True
            )
            
            if theme_key == self.settings.get("theme", "dark_green"):
                btn.background_color = theme_data["button_active"]
            
            btn.bind(on_release=lambda x, key=theme_key: self._apply_theme(key))
            theme_list.add_widget(btn)
        
        theme_scroll.add_widget(theme_list)
        self.settings_content.add_widget(theme_scroll)
    
    def _apply_theme(self, theme_name):
        self.settings["theme"] = theme_name
        save_settings(self.settings)
        self.pda.add_history(f"Тема изменена. Перезапустите PDA для полного применения.")
        
        # Обновляем свой интерфейс
        self.clear_widgets()
        self._build_ui()
        self._show_theme_settings()
    
    # ============ ПАРОЛЬ ============
    
    def _show_password_settings(self, *args):
        self._clear_content()
        theme = self._get_theme()
        
        self.settings_content.add_widget(Label(
            text="НАСТРОЙКА ПАРОЛЯ", font_size='15sp', bold=True,
            color=theme["text_bright"], size_hint_y=None, height=30
        ))
        
        has_password = bool(self.settings.get("password", ""))
        status_text = "Пароль УСТАНОВЛЕН" if has_password else "Пароль НЕ установлен"
        status_color = theme["text_bright"] if has_password else theme["warning"]
        
        self.settings_content.add_widget(Label(
            text=f"Статус: {status_text}", color=status_color, size_hint_y=None, height=22, font_size='12sp'
        ))
        
        self.settings_content.add_widget(Label(
            text="Текущий пароль:", color=theme["text"], size_hint_y=None, height=18, font_size='11sp'
        ))
        
        self.current_pass = TextInput(
            hint_text="Введите текущий пароль", password=True,
            size_hint_y=None, height=36,
            background_color=(0.1, 0.12, 0.1, 1),
            foreground_color=theme["text"], multiline=False, font_size='13sp'
        )
        self.settings_content.add_widget(self.current_pass)
        
        self.settings_content.add_widget(Label(
            text="Новый пароль:", color=theme["text"], size_hint_y=None, height=18, font_size='11sp'
        ))
        
        self.new_pass = TextInput(
            hint_text="Введите новый пароль", password=True,
            size_hint_y=None, height=36,
            background_color=(0.1, 0.12, 0.1, 1),
            foreground_color=theme["text"], multiline=False, font_size='13sp'
        )
        self.settings_content.add_widget(self.new_pass)
        
        self.settings_content.add_widget(Label(
            text="Подтвердите пароль:", color=theme["text"], size_hint_y=None, height=18, font_size='11sp'
        ))
        
        self.confirm_pass = TextInput(
            hint_text="Повторите новый пароль", password=True,
            size_hint_y=None, height=36,
            background_color=(0.1, 0.12, 0.1, 1),
            foreground_color=theme["text"], multiline=False, font_size='13sp'
        )
        self.settings_content.add_widget(self.confirm_pass)
        
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=36, spacing=8)
        
        btn_change = Button(
            text="СМЕНИТЬ ПАРОЛЬ", background_normal='',
            background_color=theme["button_active"], bold=True, font_size='11sp'
        )
        btn_change.bind(on_release=self._change_password)
        btn_box.add_widget(btn_change)
        
        btn_remove = Button(
            text="УДАЛИТЬ ПАРОЛЬ", background_normal='',
            background_color=theme["error"], bold=True, font_size='11sp'
        )
        btn_remove.bind(on_release=self._remove_password)
        btn_box.add_widget(btn_remove)
        
        self.settings_content.add_widget(btn_box)
        
        self.pass_message = Label(
            text="", color=theme["text"], size_hint_y=None, height=22, font_size='11sp'
        )
        self.settings_content.add_widget(self.pass_message)
    
    def _change_password(self, *args):
        current = self.current_pass.text.strip()
        new = self.new_pass.text.strip()
        confirm = self.confirm_pass.text.strip()
        stored = self.settings.get("password", "")
        
        if stored and current != stored:
            self.pass_message.text = "Неверный текущий пароль!"
            self.pass_message.color = (1, 0, 0, 1)
            return
        
        if not new:
            self.pass_message.text = "Введите новый пароль!"
            self.pass_message.color = (1, 0, 0, 1)
            return
        
        if new != confirm:
            self.pass_message.text = "Пароли не совпадают!"
            self.pass_message.color = (1, 0, 0, 1)
            return
        
        if len(new) < 4:
            self.pass_message.text = "Минимум 4 символа!"
            self.pass_message.color = (1, 0, 0, 1)
            return
        
        self.settings["password"] = new
        self.pass_message.text = "Пароль успешно изменён!"
        self.pass_message.color = (0, 1, 0, 1)
        
        self.current_pass.text = ""
        self.new_pass.text = ""
        self.confirm_pass.text = ""
        self.pda.add_history("Пароль изменён")
    
    def _remove_password(self, *args):
        current = self.current_pass.text.strip()
        stored = self.settings.get("password", "")
        
        if stored and current != stored:
            self.pass_message.text = "Неверный пароль!"
            self.pass_message.color = (1, 0, 0, 1)
            return
        
        self.settings["password"] = ""
        self.pass_message.text = "Пароль удалён!"
        self.pass_message.color = (0, 1, 0, 1)
        
        self.current_pass.text = ""
        self.pda.add_history("Пароль удалён")
    
    # ============ GPS ============
    
    def _show_gps_settings(self, *args):
        self._clear_content()
        theme = self._get_theme()
        
        self.settings_content.add_widget(Label(
            text="НАСТРОЙКА GPS", font_size='15sp', bold=True,
            color=theme["text_bright"], size_hint_y=None, height=30
        ))
        
        self.settings_content.add_widget(Label(
            text="Интервал обновления (сек):", color=theme["text"], size_hint_y=None, height=22, font_size='12sp'
        ))
        
        gps_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        
        self.gps_slider = Slider(min=1, max=10, value=self.settings.get("gps_update_interval", 2),
                                 step=1, size_hint_x=0.6, value_track=True,
                                 value_track_color=theme["button_active"])
        self.gps_label = Label(text=f"{int(self.gps_slider.value)} сек", color=theme["text_bright"],
                               size_hint_x=0.4, font_size='12sp')
        self.gps_slider.bind(value=lambda s, v: setattr(self.gps_label, 'text', f'{int(v)} сек'))
        
        gps_box.add_widget(self.gps_slider)
        gps_box.add_widget(self.gps_label)
        self.settings_content.add_widget(gps_box)
        
        self.settings_content.add_widget(Label(
            text="Меньше = точнее, Больше = экономия батареи",
            color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=30, halign='center', font_size='10sp'
        ))
    
    # ============ СИСТЕМА ============
    
    def _show_system_settings(self, *args):
        self._clear_content()
        theme = self._get_theme()
        
        self.settings_content.add_widget(Label(
            text="СИСТЕМНЫЕ НАСТРОЙКИ", font_size='15sp', bold=True,
            color=theme["text_bright"], size_hint_y=None, height=30
        ))
        
        self.settings_content.add_widget(Label(
            text=f"Кэш карты: {self.settings.get('map_cache_size', 100)} тайлов",
            color=theme["text"], size_hint_y=None, height=22, font_size='12sp'
        ))
        
        cache_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=36, spacing=8)
        
        btn_clear_cache = Button(
            text="ОЧИСТИТЬ КЭШ", background_normal='',
            background_color=(0.6, 0.3, 0, 1), bold=True, font_size='11sp'
        )
        btn_clear_cache.bind(on_release=self._clear_cache)
        cache_box.add_widget(btn_clear_cache)
        
        self.settings_content.add_widget(cache_box)
        
        self.settings_content.add_widget(Label(
            text="Вкладка при запуске:", color=theme["text"], size_hint_y=None, height=22, font_size='12sp'
        ))
        
        tabs = ["КАРТА", "ЗАДАНИЯ", "ИСТОРИЯ", "KillTrack", "КОНТАКТЫ"]
        current_startup = self.settings.get("startup_tab", "КАРТА")
        
        for tab in tabs:
            btn = Button(
                text=tab, size_hint_y=None, height=32,
                background_normal='',
                background_color=theme["button_active"] if tab == current_startup else theme["button_bg"],
                color=theme["text_bright"], bold=(tab == current_startup), font_size='11sp'
            )
            btn.bind(on_release=lambda x, t=tab: self._set_startup_tab(t))
            self.settings_content.add_widget(btn)
        
        self.settings_content.add_widget(Label(
            text=f"PDA OS v2.0\nТема: {theme['name']}\nWiFi: {'Доступен' if __import__('subprocess').check_output(['netsh', 'wlan', 'show', 'interfaces'], text=True, errors='ignore', creationflags=__import__('subprocess').CREATE_NO_WINDOW if os.name == 'nt' else 0) else 'Недоступен'}",
            color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=55, halign='center', font_size='10sp'
        ))
    
    def _clear_cache(self, *args):
        if hasattr(self.pda, 'map_engine'):
            self.pda.map_engine._texture_cache.clear()
            self.pda.add_history("Кэш карты очищен")
    
    def _set_startup_tab(self, tab_name):
        self.settings["startup_tab"] = tab_name
        self.pda.add_history(f"Вкладка запуска: {tab_name}")
        self._show_system_settings()
    
    # ============ СОХРАНЕНИЕ ============
    
    def _save_all_settings(self, *args):
        if hasattr(self, 'sound_switch'):
            self.settings["sound_enabled"] = self.sound_switch.active
        if hasattr(self, 'vol_slider'):
            self.settings["sound_volume"] = self.vol_slider.value / 100
        if hasattr(self, 'gps_slider'):
            self.settings["gps_update_interval"] = int(self.gps_slider.value)
        
        if save_settings(self.settings):
            self.pda.add_history("Настройки сохранены")
            
            self.settings_content.add_widget(Label(
                text="НАСТРОЙКИ СОХРАНЕНЫ!",
                color=(0, 1, 0, 1), size_hint_y=None, height=22, bold=True, font_size='12sp'
            ))
        else:
            self.settings_content.add_widget(Label(
                text="ОШИБКА СОХРАНЕНИЯ!",
                color=(1, 0, 0, 1), size_hint_y=None, height=22, bold=True, font_size='12sp'
            ))
    
    def _reset_settings(self, *args):
        self.settings = DEFAULT_SETTINGS.copy()
        save_settings(self.settings)
        self.clear_widgets()
        self._build_ui()
        self._show_sound_settings()
        self.pda.add_history("Настройки сброшены")