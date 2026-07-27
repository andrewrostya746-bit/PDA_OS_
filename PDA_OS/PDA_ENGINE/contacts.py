import os
import time
import re
import json
import subprocess
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.graphics import Rectangle, Color, Line
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window
from config import PATH_TEX, get_theme, load_settings


def check_wifi_available():
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True, errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return "Состояние" in output or "State" in output
    except:
        return False


def check_bluetooth_available():
    try:
        output = subprocess.check_output(
            ["powershell", "Get-PnpDevice -Class Bluetooth -Status OK"],
            text=True, errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return len(output.strip()) > 0
    except:
        return False


WIFI_AVAILABLE = check_wifi_available()
BT_AVAILABLE = check_bluetooth_available()


class ContactItem(BoxLayout):
    
    def __init__(self, name, device_name, mac_address, contact_id, on_long_press=None, **kwargs):
        super().__init__(**kwargs)
        self.contact_id = contact_id
        self.mac_address = mac_address
        self.name = name
        self.device_name = device_name
        self.on_long_press = on_long_press
        self._long_press_event = None
        
        settings = load_settings()
        theme = get_theme(settings.get("theme", "dark_green"))
        
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 55
        self.spacing = 10
        self.padding = (12, 6)
        
        with self.canvas.before:
            Color(*theme["button_bg"])
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update, size=self._update)
        
        avatar = Button(
            text=name[0].upper() if name else "?",
            size_hint=(None, None),
            size=(40, 40),
            pos_hint={'center_y': 0.5},
            background_normal='',
            background_color=theme["button_active"],
            color=theme["text_bright"],
            font_size='20sp',
            bold=True
        )
        self.add_widget(avatar)
        
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.75, spacing=1)
        
        self.name_label = Label(
            text=f"[b]{name}[/b]",
            markup=True,
            color=theme["text_bright"],
            font_size='14sp',
            halign='left',
            valign='middle',
            size_hint_y=0.55
        )
        
        self.mac_label = Label(
            text=mac_address,
            color=theme["text"],
            font_size='10sp',
            halign='left',
            valign='middle',
            size_hint_y=0.45
        )
        
        info_box.add_widget(self.name_label)
        info_box.add_widget(self.mac_label)
        self.add_widget(info_box)
    
    def _update(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._long_press_event = Clock.schedule_once(
                lambda dt: self._do_long_press(), 0.6
            )
            touch.grab(self)
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self._long_press_event:
                dx = abs(touch.pos[0] - touch.opos[0])
                dy = abs(touch.pos[1] - touch.opos[1])
                if dx > 10 or dy > 10:
                    Clock.unschedule(self._long_press_event)
                    self._long_press_event = None
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self._long_press_event:
                Clock.unschedule(self._long_press_event)
                self._long_press_event = None
                self._locate_contact()
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)
    
    def _do_long_press(self):
        self._long_press_event = None
        if self.on_long_press:
            self.on_long_press(self)
    
    def _locate_contact(self):
        pda = self._get_pda()
        if pda:
            pda.add_history(f"Поиск {self.name}...")
            pda.switch_to_name("КАРТА")
    
    def _get_pda(self):
        root = App.get_running_app().root
        if not root: return None
        if hasattr(root, 'map_engine'): return root
        for child in root.children:
            if hasattr(child, 'map_engine'): return child
        return None


class EditContactModal(ModalView):
    
    def __init__(self, contact_item, contacts_screen, **kwargs):
        super().__init__(**kwargs)
        self.contact_item = contact_item
        self.contacts_screen = contacts_screen
        self.size_hint = (None, None)
        self.size = (340, 220)
        self.background_color = (0, 0, 0, 0.95)
        
        settings = load_settings()
        self.theme = get_theme(settings.get("theme", "dark_green"))
        self._build_ui()
    
    def _build_ui(self):
        main_box = BoxLayout(orientation='vertical', padding=18, spacing=12)
        
        main_box.add_widget(Label(
            text=f"КОНТАКТ: {self.contact_item.name}",
            font_size='16sp', bold=True,
            color=self.theme["text_bright"],
            size_hint_y=None, height=30
        ))
        
        main_box.add_widget(Label(
            text="Новое имя:",
            color=self.theme["text"],
            size_hint_y=None, height=18
        ))
        
        self.name_input = TextInput(
            text=self.contact_item.name,
            size_hint_y=None, height=38,
            background_color=(0.1, 0.12, 0.1, 1),
            foreground_color=self.theme["text_bright"],
            multiline=False, font_size='14sp'
        )
        main_box.add_widget(self.name_input)
        
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        
        btn_save = Button(
            text="СОХРАНИТЬ", background_normal='',
            background_color=self.theme["button_active"], bold=True, font_size='12sp'
        )
        btn_save.bind(on_release=self._save_changes)
        btn_box.add_widget(btn_save)
        
        btn_delete = Button(
            text="УДАЛИТЬ", background_normal='',
            background_color=self.theme["error"], bold=True, font_size='12sp'
        )
        btn_delete.bind(on_release=self._delete_contact)
        btn_box.add_widget(btn_delete)
        
        main_box.add_widget(btn_box)
        
        btn_cancel = Button(
            text="ОТМЕНА", size_hint_y=None, height=32,
            background_normal='', background_color=self.theme["button_bg"],
            bold=True, font_size='11sp', color=self.theme["text"]
        )
        btn_cancel.bind(on_release=self.dismiss)
        main_box.add_widget(btn_cancel)
        
        self.add_widget(main_box)
    
    def _save_changes(self, *args):
        new_name = self.name_input.text.strip()
        if new_name:
            self.contact_item.name = new_name
            self.contact_item.name_label.text = f"[b]{new_name}[/b]"
            self.contacts_screen._save_contacts()
        self.dismiss()
    
    def _delete_contact(self, *args):
        self.contacts_screen.remove_contact(self.contact_item)
        self.dismiss()


class AddContactFromScanModal(ModalView):
    
    def __init__(self, device_name, mac_address, contacts_screen, **kwargs):
        super().__init__(**kwargs)
        self.device_name = device_name
        self.mac_address = mac_address
        self.contacts_screen = contacts_screen
        self.size_hint = (None, None)
        self.size = (340, 180)
        self.background_color = (0, 0, 0, 0.95)
        
        settings = load_settings()
        self.theme = get_theme(settings.get("theme", "dark_green"))
        self._build_ui()
    
    def _build_ui(self):
        main_box = BoxLayout(orientation='vertical', padding=18, spacing=12)
        
        main_box.add_widget(Label(
            text="ДОБАВИТЬ КОНТАКТ", font_size='16sp', bold=True,
            color=self.theme["text_bright"], size_hint_y=None, height=30
        ))
        
        main_box.add_widget(Label(
            text=f"Устройство: {self.device_name}\nMAC: {self.mac_address}",
            color=self.theme["text"], size_hint_y=None, height=35, font_size='10sp'
        ))
        
        self.name_input = TextInput(
            hint_text="Введите имя контакта",
            size_hint_y=None, height=38,
            background_color=(0.1, 0.12, 0.1, 1),
            foreground_color=self.theme["text_bright"],
            multiline=False, font_size='14sp'
        )
        main_box.add_widget(self.name_input)
        
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=8)
        
        btn_add = Button(
            text="ДОБАВИТЬ", background_normal='',
            background_color=self.theme["button_active"], bold=True, font_size='12sp'
        )
        btn_add.bind(on_release=self._add_contact)
        btn_box.add_widget(btn_add)
        
        btn_cancel = Button(
            text="ОТМЕНА", background_normal='',
            background_color=self.theme["button_bg"], bold=True,
            font_size='12sp', color=self.theme["text"]
        )
        btn_cancel.bind(on_release=self.dismiss)
        btn_box.add_widget(btn_cancel)
        
        main_box.add_widget(btn_box)
        self.add_widget(main_box)
    
    def _add_contact(self, *args):
        name = self.name_input.text.strip()
        if not name:
            name = self.device_name
        
        contact_data = {
            'name': name,
            'device': self.device_name,
            'mac': self.mac_address,
            'added': time.strftime("%H:%M:%S")
        }
        self.contacts_screen.add_contact(contact_data)
        self.dismiss()


class ScanResultsPanel(BoxLayout):
    
    def __init__(self, contacts_screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = 350
        self.padding = 12
        self.spacing = 6
        self.contacts_screen = contacts_screen
        
        settings = load_settings()
        self.theme = get_theme(settings.get("theme", "dark_green"))
        
        with self.canvas.before:
            Color(0, 0, 0, 0.95)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(*self.theme["border"])
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
        self.bind(pos=self._update, size=self._update)
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        header.add_widget(Label(
            text="СКАНИРОВАНИЕ УСТРОЙСТВ", font_size='14sp', bold=True,
            color=self.theme["text_bright"], size_hint_x=0.8
        ))
        btn_close = Button(
            text="X", size_hint=(None, None), size=(30, 30),
            background_normal='', background_color=self.theme["error"], bold=True, font_size='12sp'
        )
        btn_close.bind(on_release=self._close)
        header.add_widget(btn_close)
        self.add_widget(header)
        
        self.status_label = Label(
            text="Поиск устройств...",
            color=self.theme["text"],
            size_hint_y=None,
            height=25,
            font_size='11sp'
        )
        self.add_widget(self.status_label)
        
        self.device_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.device_list.bind(minimum_height=self.device_list.setter('height'))
        scroll = ScrollView(do_scroll_x=False, size_hint_y=0.8)
        scroll.add_widget(self.device_list)
        self.add_widget(scroll)
        
        Clock.schedule_once(lambda dt: self._scan_devices(), 0.2)
    
    def _update(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)
    
    def _scan_devices(self):
        self.device_list.clear_widgets()
        found_devices = []
        
        if BT_AVAILABLE:
            try:
                output = subprocess.check_output(
                    ["powershell", "Get-PnpDevice -Class Bluetooth -Status OK | Select-Object FriendlyName,InstanceId | Format-Table -AutoSize"],
                    text=True, errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                for line in output.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('FriendlyName') and not line.startswith('---'):
                        mac = self._extract_mac(line)
                        if mac:
                            name = line.replace(mac, '').strip()[:35]
                            if name:
                                found_devices.append({'name': name, 'mac': mac, 'source': 'Bluetooth'})
            except:
                pass
        
        if WIFI_AVAILABLE:
            try:
                output = subprocess.check_output(
                    ["netsh", "wlan", "show", "profiles"],
                    text=True, errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                for line in output.split('\n'):
                    if ":" in line and "Все профили пользователей" in line:
                        ssid = line.split(":", 1)[1].strip()
                        if ssid:
                            found_devices.append({
                                'name': f"WiFi: {ssid}",
                                'mac': f"SSID:{ssid[:18]}",
                                'source': 'WiFi'
                            })
            except:
                pass
        
        if not found_devices:
            self.status_label.text = "[b]УСТРОЙСТВА НЕ НАЙДЕНЫ[/b]"
            self.status_label.color = (1, 0.5, 0, 1)
            self.status_label.markup = True
            
            self.device_list.add_widget(Label(
                text="\nУбедитесь, что:\n- Bluetooth включен\n- WiFi включен\n- Устройства находятся рядом\n",
                color=(0.8, 0.8, 0.8, 1),
                size_hint_y=None,
                height=90,
                halign='center',
                valign='middle',
                font_size='10sp'
            ))
            return
        
        self.status_label.text = f"Найдено устройств: {len(found_devices)}"
        self.status_label.color = (0, 0.9, 0, 1)
        
        for device in found_devices:
            self._add_device_row(device['name'], device['mac'], device.get('source', 'Unknown'))
    
    def _extract_mac(self, text):
        match = re.search(r'(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}', text, re.IGNORECASE)
        return match.group(0).upper() if match else None
    
    def _add_device_row(self, device_name, mac_address, source):
        settings = load_settings()
        theme = get_theme(settings.get("theme", "dark_green"))
        
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=42, spacing=6, padding=(5, 2))
        
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.72, spacing=1)
        info_box.add_widget(Label(
            text=device_name[:30],
            color=theme["text"],
            font_size='11sp',
            halign='left', valign='middle',
            size_hint_y=0.5
        ))
        info_box.add_widget(Label(
            text=f"[{source}] {mac_address}",
            color=(0.6, 0.6, 0.6, 1),
            font_size='9sp',
            halign='left', valign='middle',
            size_hint_y=0.5
        ))
        row.add_widget(info_box)
        
        plus_path = os.path.join(PATH_TEX, "complete.png")
        if os.path.exists(plus_path):
            btn_add = Button(
                background_normal=plus_path,
                size_hint=(None, None), size=(32, 32),
                pos_hint={'center_y': 0.5},
                background_color=theme["button_active"]
            )
        else:
            btn_add = Button(
                text="+", size_hint=(None, None), size=(32, 32),
                pos_hint={'center_y': 0.5},
                background_normal='',
                background_color=theme["button_active"],
                bold=True, font_size='18sp', color=theme["text_bright"]
            )
        btn_add.bind(on_release=lambda x, n=device_name, m=mac_address: self._add_as_contact(n, m))
        row.add_widget(btn_add)
        
        self.device_list.add_widget(row)
    
    def _add_as_contact(self, device_name, mac_address):
        modal = AddContactFromScanModal(device_name, mac_address, self.contacts_screen)
        modal.open()
    
    def _close(self, *args):
        parent = self.parent
        if parent:
            parent.remove_widget(self)


class ContactSelectPanel(BoxLayout):
    
    def __init__(self, on_contact_selected, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (340, 400)
        self.padding = 12
        self.spacing = 8
        self.on_contact_selected = on_contact_selected
        
        settings = load_settings()
        self.theme = get_theme(settings.get("theme", "dark_green"))
        
        with self.canvas.before:
            Color(0, 0, 0, 0.92)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(*self.theme["border"])
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
        self.bind(pos=self._update, size=self._update)
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        header.add_widget(Label(
            text="ВЫБЕРИТЕ КОНТАКТ", font_size='15sp', bold=True,
            color=self.theme["text_bright"]
        ))
        btn_close = Button(
            text="X", size_hint=(None, None), size=(32, 32),
            background_normal='', background_color=self.theme["error"], bold=True, font_size='13sp'
        )
        btn_close.bind(on_release=self._close)
        header.add_widget(btn_close)
        self.add_widget(header)
        
        self.contacts_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=4)
        self.contacts_list.bind(minimum_height=self.contacts_list.setter('height'))
        scroll = ScrollView(do_scroll_x=False, size_hint_y=0.85)
        scroll.add_widget(self.contacts_list)
        self.add_widget(scroll)
        
        btn_no_contact = Button(
            text="БЕЗ ПРИВЯЗКИ К КОНТАКТУ", size_hint_y=None, height=38,
            background_normal='', background_color=self.theme["button_bg"],
            bold=True, font_size='12sp', color=self.theme["text"]
        )
        btn_no_contact.bind(on_release=lambda x: self._select_contact("", ""))
        self.add_widget(btn_no_contact)
        
        self._load_contacts()
    
    def _update(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)
    
    def _load_contacts(self):
        contacts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.json")
        self.contacts_list.clear_widgets()
        
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts = json.load(f)
                
                for contact in contacts:
                    item = ContactItem(
                        name=contact['name'],
                        device_name=contact['device'],
                        mac_address=contact['mac'],
                        contact_id=contact['id'],
                        on_long_press=None
                    )
                    item.on_touch_down = lambda touch, c=contact: (self._select_contact(c['name'], c['mac']) or True) if hasattr(item, 'collide_point') and item.collide_point(*touch.pos) else super(ContactItem, item).on_touch_down(touch)
                    self.contacts_list.add_widget(item)
            except:
                pass
        
        if len(self.contacts_list.children) == 0:
            self.contacts_list.add_widget(Label(
                text="Нет контактов\nДобавьте во вкладке КОНТАКТЫ",
                color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=55, halign='center', font_size='11sp'
            ))
    
    def _select_contact(self, name, mac):
        if self.on_contact_selected:
            self.on_contact_selected(name, mac)
        self._close()
    
    def _close(self, *args):
        parent = self.parent
        if parent:
            parent.remove_widget(self)


class ContactsScreen(FloatLayout):
    
    def __init__(self, pda_interface, **kwargs):
        super().__init__(**kwargs)
        self.pda = pda_interface
        self.contacts = []
        self.contacts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.json")
        
        settings = load_settings()
        self.theme = get_theme(settings.get("theme", "dark_green"))
        
        self._load_contacts()
        self._build_ui()
    
    def _build_ui(self):
        with self.canvas.before:
            Color(*self.theme["bg_main"])
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        with self.canvas.before:
            Color(*self.theme["bg_top"])
            self.top_rect = Rectangle()
            Color(*self.theme["accent"])
            self.top_line = Rectangle()
        
        self.contacts_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.contacts_list.bind(minimum_height=self.contacts_list.setter('height'))
        
        scroll = ScrollView(
            do_scroll_x=False,
            size_hint=(1, 0.82),
            pos_hint={'top': 0.88}
        )
        scroll.add_widget(self.contacts_list)
        self.add_widget(scroll)
        
        # Кнопка сканирования в правом нижнем углу
        menu_path = os.path.join(PATH_TEX, "menu.png")
        if os.path.exists(menu_path):
            btn_scan = Button(
                background_normal=menu_path,
                size_hint=(None, None),
                size=(55, 55),
                pos_hint={'right': 0.98, 'y': 0.03},
                background_color=self.theme["button_active"]
            )
        else:
            btn_scan = Button(
                text="СКАН",
                size_hint=(None, None),
                size=(55, 55),
                pos_hint={'right': 0.98, 'y': 0.03},
                background_normal='',
                background_color=self.theme["button_active"],
                bold=True,
                font_size='11sp',
                color=self.theme["text_bright"]
            )
        btn_scan.bind(on_release=self._show_scan_results)
        self.add_widget(btn_scan)
        
        self.bind(size=self._do_layout)
        self._refresh_contacts_list()
    
    def _do_layout(self, *args):
        self.top_rect.pos = (0, self.height - 90)
        self.top_rect.size = (self.width, 90)
        self.top_line.pos = (0, self.height - 90)
        self.top_line.size = (self.width, 2)
    
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def _load_contacts(self):
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, 'r', encoding='utf-8') as f:
                    self.contacts = json.load(f)
            except:
                self.contacts = []
    
    def _save_contacts(self):
        try:
            with open(self.contacts_file, 'w', encoding='utf-8') as f:
                json.dump(self.contacts, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def _show_scan_results(self, *args):
        panel = ScanResultsPanel(self)
        panel.pos_hint = {'x': 0, 'y': 0}
        self.add_widget(panel)
    
    def add_contact(self, contact_data):
        contact_data['id'] = time.time()
        self.contacts.append(contact_data)
        self._save_contacts()
        self._refresh_contacts_list()
        self.pda.add_history(f"Добавлен контакт: {contact_data['name']}")
    
    def remove_contact(self, contact_item):
        self.contacts = [c for c in self.contacts if c['id'] != contact_item.contact_id]
        self.contacts_list.remove_widget(contact_item)
        self._save_contacts()
        self.pda.add_history(f"Контакт {contact_item.name} удалён")
    
    def _show_edit_modal(self, contact_item):
        modal = EditContactModal(contact_item, self)
        modal.open()
    
    def _refresh_contacts_list(self):
        self.contacts_list.clear_widgets()
        
        if not self.contacts:
            self.contacts_list.add_widget(Label(
                text="Нет контактов\n\nНажмите кнопку снизу\nчтобы найти устройства вокруг",
                color=(0.6, 0.6, 0.6, 1),
                size_hint_y=None,
                height=100,
                halign='center',
                valign='middle',
                font_size='12sp'
            ))
        else:
            for contact in self.contacts:
                item = ContactItem(
                    name=contact['name'],
                    device_name=contact['device'],
                    mac_address=contact['mac'],
                    contact_id=contact['id'],
                    on_long_press=self._show_edit_modal
                )
                self.contacts_list.add_widget(item)