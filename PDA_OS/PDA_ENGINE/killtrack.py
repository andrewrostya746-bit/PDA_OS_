import subprocess
import os
import math
import random
import time
import re
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Rectangle, Color, Line


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


WIFI_AVAILABLE = check_wifi_available()


class KillTrackScreen(FloatLayout):
    
    def __init__(self, pda_interface, **kwargs):
        super().__init__(**kwargs)
        self.pda = pda_interface
        self.tracked_macs = []
        self.heatmap_points = []
        self._build_ui()
    
    def _build_ui(self):
        # Левая панель инструментов
        self.tools_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.25, 0.82),
            pos_hint={'x': 0.02, 'center_y': 0.48},
            spacing=4,
            padding=(0, 10)
        )
        
        tools = [
            ("МОНИТОРИНГ СЕТЕЙ", self.show_network_monitor),
            ("WiFi HEATMAP", self.show_heatmap_tool),
            ("MAC ТРЕКЕР", self.show_mac_tracker),
            ("АНАЛИЗ БЕЗОПАСНОСТИ", self.show_security_analyzer),
            ("ЭКСПОРТ ПАРОЛЕЙ", self.show_password_export)
        ]
        
        for tool_name, callback in tools:
            btn = Button(
                text=tool_name,
                size_hint_y=None,
                height=42,
                background_normal='',
                background_color=(0.12, 0.15, 0.12, 1),
                color=(0, 0.9, 0, 1),
                halign='left',
                valign='middle',
                padding=(10, 5),
                font_size='11sp',
                bold=True
            )
            btn.bind(on_release=callback)
            self.tools_panel.add_widget(btn)
        
        self.add_widget(self.tools_panel)
        
        # Правая панель контента
        self.right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.7, 0.78),
            pos_hint={'right': 0.98, 'y': 0.04},
            spacing=6,
            padding=8
        )
        
        with self.right_panel.canvas.before:
            Color(0.06, 0.08, 0.06, 0.9)
            self.panel_bg = Rectangle(pos=self.right_panel.pos, size=self.right_panel.size)
            Color(0, 0.4, 0, 1)
            self.panel_border = Line(
                rectangle=(self.right_panel.x, self.right_panel.y,
                          self.right_panel.width, self.right_panel.height),
                width=1.5
            )
        
        self.right_panel.bind(pos=self._update_panel, size=self._update_panel)
        
        self.tool_title = Label(
            text="ВЫБЕРИТЕ ИНСТРУМЕНТ",
            font_size='14sp',
            bold=True,
            color=(0, 0.8, 0, 1),
            size_hint_y=None,
            height=30
        )
        self.right_panel.add_widget(self.tool_title)
        
        self.tool_content = BoxLayout(
            orientation='vertical',
            size_hint_y=0.9,
            spacing=4
        )
        self.right_panel.add_widget(self.tool_content)
        
        self.add_widget(self.right_panel)
    
    def _update_panel(self, *args):
        self.panel_bg.pos = self.right_panel.pos
        self.panel_bg.size = self.right_panel.size
        self.panel_border.rectangle = (
            self.right_panel.x, self.right_panel.y,
            self.right_panel.width, self.right_panel.height
        )
    
    def clear_tool_content(self):
        self.tool_content.clear_widgets()
        
        if not WIFI_AVAILABLE:
            self.tool_content.add_widget(Label(
                text="WiFi модуль не обнаружен.\nФункции недоступны.",
                color=(1, 0.5, 0, 1),
                size_hint_y=None,
                height=35,
                font_size='10sp',
                halign='center'
            ))
    
    def _run_wlan_command(self, command):
        if not WIFI_AVAILABLE:
            return None
        try:
            return subprocess.check_output(
                command,
                text=True, errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except:
            return None
    
    def _get_saved_profiles(self):
        output = self._run_wlan_command(["netsh", "wlan", "show", "profiles"])
        if not output:
            return []
        
        profiles = []
        for line in output.split('\n'):
            if ":" in line and "Все профили пользователей" in line:
                ssid = line.split(":", 1)[1].strip()
                if ssid:
                    profiles.append(ssid)
        return profiles
    
    def _get_profile_details(self, ssid):
        output = self._run_wlan_command(
            ["netsh", "wlan", "show", "profile", f"name={ssid}", "key=clear"]
        )
        if not output:
            return {}
        
        details = {'ssid': ssid}
        for line in output.split('\n'):
            line = line.strip()
            if "Содержимое ключа" in line or "Key Content" in line:
                details['password'] = line.split(":", 1)[1].strip()
            elif "Проверка подлинности" in line or "Authentication" in line:
                details['auth'] = line.split(":", 1)[1].strip()
            elif "Шифрование" in line or "Encryption" in line:
                details['encryption'] = line.split(":", 1)[1].strip()
        
        return details
    
    def _scan_available_networks(self):
        output = self._run_wlan_command(
            ["netsh", "wlan", "show", "networks", "mode=bssid"]
        )
        if not output:
            return []
        
        networks = []
        current = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if "SSID" in line and "BSSID" not in line:
                if current:
                    networks.append(current)
                current = {'ssid': line.split(':', 1)[1].strip()}
            elif "BSSID" in line:
                try:
                    current['bssid'] = line.split(':', 1)[1].strip()
                except:
                    pass
            elif "Signal" in line or "Сигнал" in line:
                try:
                    current['signal'] = line.split(':', 1)[1].strip()
                except:
                    pass
            elif "Channel" in line or "Канал" in line:
                try:
                    current['channel'] = line.split(':', 1)[1].strip()
                except:
                    pass
            elif "Authentication" in line or "Проверка подлинности" in line:
                try:
                    current['auth'] = line.split(':', 1)[1].strip()
                except:
                    pass
        
        if current:
            networks.append(current)
        
        return networks
    
    def show_network_monitor(self, *args):
        self.clear_tool_content()
        self.tool_title.text = "МОНИТОРИНГ СЕТЕЙ"
        
        if not WIFI_AVAILABLE:
            return
        
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=4)
        
        btn_saved = Button(
            text="СОХРАНЁННЫЕ", background_normal='',
            background_color=(0, 0.5, 0, 1), bold=True, font_size='10sp'
        )
        btn_saved.bind(on_release=lambda x: self._show_saved_networks())
        btn_row.add_widget(btn_saved)
        
        btn_available = Button(
            text="ДОСТУПНЫЕ", background_normal='',
            background_color=(0, 0.4, 0.5, 1), bold=True, font_size='10sp'
        )
        btn_available.bind(on_release=lambda x: self._show_available_networks())
        btn_row.add_widget(btn_available)
        
        self.tool_content.add_widget(btn_row)
        
        self.network_scroll = ScrollView(do_scroll_x=False, size_hint_y=0.9)
        self.network_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.network_list.bind(minimum_height=self.network_list.setter('height'))
        self.network_scroll.add_widget(self.network_list)
        self.tool_content.add_widget(self.network_scroll)
        
        self._show_saved_networks()
    
    def _show_saved_networks(self):
        self.network_list.clear_widgets()
        profiles = self._get_saved_profiles()
        
        if not profiles:
            self.network_list.add_widget(Label(
                text="Сохранённые сети не найдены",
                color=(0.8, 0.8, 0, 1), size_hint_y=None, height=25, font_size='10sp'
            ))
            return
        
        self.pda.add_history(f"Мониторинг: {len(profiles)} сохранённых сетей")
        
        for ssid in profiles:
            details = self._get_profile_details(ssid)
            password = details.get('password', '')
            
            if password:
                text = f"[b]{ssid}[/b] | [color=00ff00]ПАРОЛЬ: {password}[/color]"
                color = (0, 1, 0, 1)
            else:
                text = f"[b]{ssid}[/b] | Открытая сеть"
                color = (0.8, 0.8, 0, 1)
            
            self.network_list.add_widget(Label(
                text=text, markup=True, color=color,
                size_hint_y=None, height=25, font_size='10sp'
            ))
    
    def _show_available_networks(self):
        self.network_list.clear_widgets()
        networks = self._scan_available_networks()
        
        if not networks:
            self.network_list.add_widget(Label(
                text="Доступные сети не найдены",
                color=(0.8, 0.8, 0, 1), size_hint_y=None, height=25, font_size='10sp'
            ))
            return
        
        self.pda.add_history(f"Сканирование: {len(networks)} доступных сетей")
        
        for net in networks:
            ssid = net.get('ssid', 'Неизвестно')
            signal = net.get('signal', '?')
            channel = net.get('channel', '?')
            auth = net.get('auth', '?')
            
            try:
                sig_val = int(signal.replace('%', ''))
                if sig_val > 70:
                    color = (0, 1, 0, 1)
                elif sig_val > 40:
                    color = (1, 1, 0, 1)
                else:
                    color = (1, 0.5, 0, 1)
            except:
                color = (0.8, 0.8, 0.8, 1)
            
            text = f"[b]{ssid}[/b] | Сигнал: {signal} | CH{channel} | {auth}"
            self.network_list.add_widget(Label(
                text=text, markup=True, color=color,
                size_hint_y=None, height=25, font_size='9sp'
            ))
    
    def show_heatmap_tool(self, *args):
        self.clear_tool_content()
        self.tool_title.text = "WiFi HEATMAP"
        
        if not WIFI_AVAILABLE:
            return
        
        btn_scan = Button(
            text="СКАНИРОВАТЬ И ЗАПИСАТЬ ТОЧКУ",
            size_hint_y=None, height=36,
            background_normal='',
            background_color=(0, 0.6, 0, 1), bold=True, font_size='11sp'
        )
        btn_scan.bind(on_release=self._do_heatmap_scan)
        self.tool_content.add_widget(btn_scan)
        
        btn_clear = Button(
            text="ОЧИСТИТЬ ДАННЫЕ",
            size_hint_y=None, height=32,
            background_normal='',
            background_color=(0.6, 0.3, 0, 1), bold=True, font_size='10sp'
        )
        btn_clear.bind(on_release=lambda x: self._clear_heatmap())
        self.tool_content.add_widget(btn_clear)
        
        btn_export = Button(
            text="ЭКСПОРТ В ФАЙЛ",
            size_hint_y=None, height=32,
            background_normal='',
            background_color=(0, 0.4, 0.6, 1), bold=True, font_size='10sp'
        )
        btn_export.bind(on_release=self._export_heatmap)
        self.tool_content.add_widget(btn_export)
        
        self.heatmap_stats = Label(
            text=f"Точек собрано: {len(self.heatmap_points)}",
            color=(0, 0.8, 0, 1), size_hint_y=None, height=22, font_size='11sp'
        )
        self.tool_content.add_widget(self.heatmap_stats)
        
        self.heatmap_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.heatmap_list.bind(minimum_height=self.heatmap_list.setter('height'))
        
        scroll = ScrollView(do_scroll_x=False, size_hint_y=0.7)
        scroll.add_widget(self.heatmap_list)
        self.tool_content.add_widget(scroll)
        
        self._refresh_heatmap_list()
    
    def _do_heatmap_scan(self, *args):
        networks = self._scan_available_networks()
        
        if not networks:
            return
        
        try:
            gps_data = self.pda.map_engine.player_x, self.pda.map_engine.player_y
            tile_x = gps_data[0] / 256.0
            tile_y = gps_data[1] / 256.0
            n = 2.0 ** 12
            lon = (tile_x / n) * 360.0 - 180.0
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
            lat = math.degrees(lat_rad)
        except:
            lat, lon = 0, 0
        
        timestamp = time.strftime("%H:%M:%S")
        
        for net in networks:
            point = {
                'ssid': net.get('ssid', 'Unknown'),
                'bssid': net.get('bssid', 'N/A'),
                'signal': net.get('signal', 'N/A'),
                'channel': net.get('channel', 'N/A'),
                'auth': net.get('auth', 'N/A'),
                'lat': lat,
                'lon': lon,
                'time': timestamp
            }
            self.heatmap_points.append(point)
        
        self._refresh_heatmap_list()
        self.heatmap_stats.text = f"Точек собрано: {len(self.heatmap_points)}"
        self.pda.add_history(f"Heatmap: записано {len(networks)} точек")
    
    def _refresh_heatmap_list(self):
        self.heatmap_list.clear_widgets()
        for point in self.heatmap_points[-40:]:
            self.heatmap_list.add_widget(Label(
                text=f"{point['ssid'][:18]} | {point['signal']} | CH{point['channel']} | "
                     f"{point['lat']:.4f}, {point['lon']:.4f}",
                color=(0, 0.9, 0, 1), size_hint_y=None, height=22, font_size='9sp'
            ))
    
    def _clear_heatmap(self):
        self.heatmap_points = []
        self.heatmap_list.clear_widgets()
        self.heatmap_stats.text = "Точек собрано: 0"
        self.pda.add_history("Heatmap: данные очищены")
    
    def _export_heatmap(self):
        if not self.heatmap_points:
            self.tool_content.add_widget(Label(
                text="Нет данных для экспорта", color=(1, 0.5, 0, 1),
                size_hint_y=None, height=22, font_size='10sp'
            ))
            return
        
        try:
            export_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wifi_heatmap.txt")
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("WiFi Heatmap Data\n")
                f.write("=" * 60 + "\n\n")
                for point in self.heatmap_points:
                    f.write(f"SSID: {point['ssid']}\n")
                    f.write(f"BSSID: {point['bssid']}\n")
                    f.write(f"Signal: {point['signal']}\n")
                    f.write(f"Channel: {point['channel']}\n")
                    f.write(f"Auth: {point['auth']}\n")
                    f.write(f"Latitude: {point['lat']:.6f}\n")
                    f.write(f"Longitude: {point['lon']:.6f}\n")
                    f.write(f"Time: {point['time']}\n")
                    f.write("-" * 40 + "\n")
            
            self.tool_content.add_widget(Label(
                text=f"Экспортировано: {export_path}",
                color=(0, 1, 0, 1), size_hint_y=None, height=25, font_size='10sp'
            ))
            self.pda.add_history(f"Heatmap экспортирован в wifi_heatmap.txt")
        except Exception as e:
            self.tool_content.add_widget(Label(
                text=f"ОШИБКА: {str(e)}", color=(1, 0, 0, 1), size_hint_y=None, height=22, font_size='10sp'
            ))
    
    def show_mac_tracker(self, *args):
        self.clear_tool_content()
        self.tool_title.text = "MAC ТРЕКЕР"
        
        if not WIFI_AVAILABLE:
            return
        
        input_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=36, spacing=4)
        
        self.mac_input = TextInput(
            hint_text="AA:BB:CC:DD:EE:FF",
            background_color=(0.1, 0.12, 0.1, 1),
            foreground_color=(0, 1, 0, 1),
            multiline=False, font_size='11sp'
        )
        input_box.add_widget(self.mac_input)
        
        btn_add = Button(
            text="ДОБАВИТЬ", size_hint_x=0.3,
            background_normal='',
            background_color=(0, 0.6, 0, 1), bold=True, font_size='10sp'
        )
        btn_add.bind(on_release=self._add_mac_target)
        input_box.add_widget(btn_add)
        
        self.tool_content.add_widget(input_box)
        
        self.target_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.target_list.bind(minimum_height=self.target_list.setter('height'))
        
        scroll = ScrollView(do_scroll_x=False, size_hint_y=0.8)
        scroll.add_widget(self.target_list)
        self.tool_content.add_widget(scroll)
        
        self._refresh_target_list()
    
    def _add_mac_target(self, *args):
        mac = self.mac_input.text.strip().upper()
        
        if not mac:
            return
        
        if not re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', mac):
            self.tool_content.add_widget(Label(
                text="НЕВЕРНЫЙ ФОРМАТ MAC АДРЕСА",
                color=(1, 0, 0, 1), size_hint_y=None, height=22, font_size='10sp'
            ))
            return
        
        for target in self.tracked_macs:
            if target['mac'] == mac:
                self.tool_content.add_widget(Label(
                    text=f"MAC {mac} уже отслеживается",
                    color=(1, 1, 0, 1), size_hint_y=None, height=22, font_size='10sp'
                ))
                return
        
        self.tracked_macs.append({
            'mac': mac,
            'added': time.strftime("%H:%M:%S"),
            'note': ''
        })
        
        self.mac_input.text = ""
        self._refresh_target_list()
        self.pda.add_history(f"MAC трекер: добавлен {mac}")
    
    def _refresh_target_list(self):
        self.target_list.clear_widgets()
        if not self.tracked_macs:
            self.target_list.add_widget(Label(
                text="Нет отслеживаемых устройств",
                color=(0.7, 0.7, 0.7, 1), size_hint_y=None, height=22, font_size='10sp'
            ))
            return
        
        for target in self.tracked_macs:
            self.target_list.add_widget(Label(
                text=f"[b]{target['mac']}[/b] | Добавлен: {target['added']} | ОТСЛЕЖИВАЕТСЯ",
                markup=True, color=(0, 1, 0, 1), size_hint_y=None, height=25, font_size='10sp'
            ))
    
    def show_security_analyzer(self, *args):
        self.clear_tool_content()
        self.tool_title.text = "АНАЛИЗ БЕЗОПАСНОСТИ"
        
        if not WIFI_AVAILABLE:
            return
        
        btn_analyze = Button(
            text="ПРОВЕРИТЬ МОЮ СЕТЬ",
            size_hint_y=None, height=36,
            background_normal='',
            background_color=(0, 0.6, 0, 1), bold=True, font_size='11sp'
        )
        btn_analyze.bind(on_release=self._analyze_security)
        self.tool_content.add_widget(btn_analyze)
        
        self.security_results = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.security_results.bind(minimum_height=self.security_results.setter('height'))
        
        scroll = ScrollView(do_scroll_x=False, size_hint_y=0.85)
        scroll.add_widget(self.security_results)
        self.tool_content.add_widget(scroll)
    
    def _analyze_security(self, *args):
        self.security_results.clear_widgets()
        
        profiles = self._get_saved_profiles()
        if not profiles:
            self.security_results.add_widget(Label(
                text="Нет сохранённых сетей для анализа",
                color=(0.8, 0, 0, 1), size_hint_y=None, height=25, font_size='10sp'
            ))
            return
        
        weak_passwords = [
            "12345678", "password", "qwerty123", "admin", "1234567890",
            "00000000", "11111111", "123123123", "abc12345"
        ]
        
        issues_found = 0
        
        for ssid in profiles:
            details = self._get_profile_details(ssid)
            password = details.get('password', '')
            auth = details.get('auth', 'Неизвестно')
            encryption = details.get('encryption', 'Неизвестно')
            
            issues = []
            
            if 'WEP' in auth or 'WEP' in encryption:
                issues.append("WEP - НЕБЕЗОПАСНО")
            elif 'WPA' in auth and 'WPA2' not in auth:
                issues.append("WPA - УСТАРЕВШИЙ")
            elif 'Open' in auth or 'Открытая' in auth:
                issues.append("ОТКРЫТАЯ СЕТЬ")
            
            if password:
                if len(password) < 8:
                    issues.append(f"Короткий пароль ({len(password)} символов)")
                if password.lower() in weak_passwords:
                    issues.append("СЛАБЫЙ ПАРОЛЬ")
                if password.isdigit():
                    issues.append("Пароль только из цифр")
            
            if issues:
                color = (1, 0.5, 0, 1)
                status = "ПРОБЛЕМЫ"
                issues_found += 1
            else:
                color = (0, 1, 0, 1)
                status = "БЕЗОПАСНО"
            
            self.security_results.add_widget(Label(
                text=f"[b]{ssid}[/b] - {status}",
                markup=True, color=color, size_hint_y=None, height=22, font_size='10sp'
            ))
            
            for issue in issues:
                self.security_results.add_widget(Label(
                    text=f"    [!] {issue}",
                    color=(1, 0.5, 0, 1), size_hint_y=None, height=18, font_size='9sp'
                ))
        
        total = len(profiles)
        safe = total - issues_found
        
        self.security_results.add_widget(Label(
            text=f"\nИТОГО: {total} сетей | Безопасно: {safe} | Проблемы: {issues_found}",
            color=(0, 1, 0, 1) if issues_found == 0 else (1, 0.5, 0, 1),
            size_hint_y=None, height=28, font_size='11sp', bold=True
        ))
        
        self.pda.add_history(f"Анализ безопасности: {safe}/{total} сетей безопасны")
    
    def show_password_export(self, *args):
        self.clear_tool_content()
        self.tool_title.text = "ЭКСПОРТ ПАРОЛЕЙ"
        
        if not WIFI_AVAILABLE:
            return
        
        btn_export = Button(
            text="ЭКСПОРТИРОВАТЬ ВСЕ ПАРОЛИ",
            size_hint_y=None, height=40,
            background_normal='',
            background_color=(0, 0.6, 0, 1), bold=True, font_size='12sp'
        )
        btn_export.bind(on_release=self._export_all_passwords)
        self.tool_content.add_widget(btn_export)
        
        self.export_status = Label(
            text="Нажмите кнопку для экспорта\nвсех сохранённых паролей WiFi",
            color=(0, 0.8, 0, 1), size_hint_y=None, height=45,
            halign='center', valign='middle', font_size='10sp'
        )
        self.tool_content.add_widget(self.export_status)
        
        self.export_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2)
        self.export_list.bind(minimum_height=self.export_list.setter('height'))
        
        scroll = ScrollView(do_scroll_x=False, size_hint_y=0.7)
        scroll.add_widget(self.export_list)
        self.tool_content.add_widget(scroll)
    
    def _export_all_passwords(self, *args):
        self.export_list.clear_widgets()
        
        profiles = self._get_saved_profiles()
        if not profiles:
            self.export_status.text = "Нет сохранённых сетей"
            return
        
        exported = 0
        passwords_data = []
        
        for ssid in profiles:
            details = self._get_profile_details(ssid)
            password = details.get('password', '')
            
            if password:
                exported += 1
                passwords_data.append(f"{ssid}: {password}")
                self.export_list.add_widget(Label(
                    text=f"[b]{ssid}[/b]: [color=00ff00]{password}[/color]",
                    markup=True, color=(0, 1, 0, 1), size_hint_y=None, height=22, font_size='10sp'
                ))
        
        try:
            export_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wifi_passwords.txt")
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("WiFi Passwords Export\n")
                f.write("=" * 40 + "\n\n")
                for line in passwords_data:
                    f.write(line + "\n")
            
            self.export_status.text = f"Экспортировано паролей: {exported}\nФайл: wifi_passwords.txt"
        except Exception as e:
            self.export_status.text = f"ОШИБКА: {str(e)}"
        
        self.pda.add_history(f"Экспортировано {exported} паролей")