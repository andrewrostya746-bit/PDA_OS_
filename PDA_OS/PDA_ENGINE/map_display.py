import sqlite3
import time
import math
import random
from io import BytesIO
import mgrs
import os

from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Line, InstructionGroup
from kivy.app import App

from config import PATH_MAP, PATH_ARROW, get_theme, load_settings


class MapDisplay(Widget):
    map_center_x = NumericProperty(2394.5 * 256)
    map_center_y = NumericProperty(2645.5 * 256)
    zoom_scale = NumericProperty(1.0)
    player_x = NumericProperty(2394.5 * 256)
    player_y = NumericProperty(2645.5 * 256)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tile_size = 256
        self.markers = []
        self._long_press_event = None
        self._hover_tooltip = None
        self._texture_cache = {}
        
        self.settings = load_settings()
        self.theme = get_theme(self.settings.get("theme", "dark_green"))
        
        self.filter_locations = True
        self.filter_side_quests = True
        self.filter_key_markers = True
        self.filter_stashes = True

        try:
            self.m = mgrs.MGRS()
        except Exception as e:
            print(f"[ERROR] mgrs: {e}")
            self.m = None

        self.tile_group = InstructionGroup()
        self.marker_group = InstructionGroup()
        self.canvas.add(self.tile_group)
        self.canvas.add(self.marker_group)

        try:
            self.db = sqlite3.connect(PATH_MAP)
            self.cursor = self.db.cursor()
            self.db.execute("PRAGMA journal_mode = MEMORY;")
            self.db.execute("PRAGMA cache_size = 10000;")
        except Exception as e:
            print(f"[ERROR] База MBTiles: {e}")

        self.bind(map_center_x=self.draw_all, map_center_y=self.draw_all,
                  zoom_scale=self.draw_all, size=self.draw_all, pos=self.draw_all)
        self.bind(player_x=self._on_player_move, player_y=self._on_player_move)
        Window.bind(mouse_pos=self.on_mouse_pos)

        self.init_gps_hardware()

    def _get_pda(self):
        root = App.get_running_app().root
        if not root:
            return None
        if hasattr(root, 'device_coords_label'):
            return root
        for child in root.children:
            if hasattr(child, 'device_coords_label'):
                return child
        return None

    def init_gps_hardware(self):
        try:
            from plyer import gps
            gps.configure(on_location=self.on_hardware_gps_data, on_status=lambda st: None)
            gps.start(minTime=1000, minDistance=1)
            print("[SYSTEM] GPS подключен.")
        except Exception:
            print("[SYSTEM] Эмуляция GPS.")
            Clock.schedule_interval(self.emulate_gps_drift, 1.0)

    def on_hardware_gps_data(self, **kwargs):
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat and lon:
            self.lat_lon_to_map_pixels(lat, lon)

    def emulate_gps_drift(self, dt):
        self.player_x += random.uniform(-2, 2)
        self.player_y += random.uniform(-2, 2)
        self.player_x = max(2390*256, min(2399*256, self.player_x))
        self.player_y = max(2643*256, min(2648*256, self.player_y))

    def lat_lon_to_map_pixels(self, lat, lon):
        try:
            n = 2.0 ** 12
            tile_x = ((lon + 180.0) / 360.0) * n
            lat_rad = math.radians(lat)
            tile_y = (1.0 - (math.asinh(math.tan(lat_rad)) / math.pi)) / 2.0 * n
            self.player_x = tile_x * 256
            self.player_y = tile_y * 256
        except:
            pass

    def enforce_bounds(self):
        self.zoom_scale = max(0.3, min(25.0, self.zoom_scale))
        self.map_center_x = max(2390*256, min(2399*256, self.map_center_x))
        self.map_center_y = max(2643*256, min(2648*256, self.map_center_y))

    def trigger_update(self):
        self.draw_all()

    def focus_marker(self, marker_pos):
        Animation.stop_all(self)
        anim = Animation(map_center_x=marker_pos[0], map_center_y=marker_pos[1],
                         zoom_scale=4.0, duration=0.6, t='out_quad')
        anim.start(self)

    def auto_center_map(self, dt=None):
        self.zoom_scale = 1.0
        self.map_center_x = self.player_x
        self.map_center_y = self.player_y
        self.enforce_bounds()
        self.draw_all()
        self.update_device_mgrs()

    def _on_player_move(self, *args):
        self.draw_all()
        self.update_device_mgrs()

    def update_device_mgrs(self):
        pda = self._get_pda()
        if not pda or not self.m:
            return
        
        tile_x = self.player_x / 256.0
        tile_y = self.player_y / 256.0
        n = 2.0 ** 12
        lon = (tile_x / n) * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
        lat = math.degrees(lat_rad)
        try:
            mgrs_coord = self.m.toMGRS(lat, lon)
            if isinstance(mgrs_coord, bytes):
                mgrs_coord = mgrs_coord.decode('utf-8')
            pda.device_coords_label.text = f"УСТРОЙСТВО: [b]{mgrs_coord}[/b]"
        except:
            pda.device_coords_label.text = "УСТРОЙСТВО: N/A"

    def _is_marker_visible(self, tex_path):
        location_markers = ["home.png", "localion.png", "big_location.png"]
        side_quest_markers = ["not_main_quest.png"]
        key_markers = ["shelter.png", "neizvestno.png"]
        stash_markers = ["common_shron.png", "yellow_shron.png", "red_shron.png"]
        
        filename = os.path.basename(tex_path)
        
        if any(m in filename for m in location_markers):
            return self.filter_locations
        if any(m in filename for m in side_quest_markers):
            return self.filter_side_quests
        if any(m in filename for m in key_markers):
            return self.filter_key_markers
        if any(m in filename for m in stash_markers):
            return self.filter_stashes
        
        return True

    def draw_all(self, *args):
        if not self.parent or self.width < 10:
            return
        self.tile_group.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        zoom_offset = int(math.log2(self.zoom_scale)) if self.zoom_scale > 0 else 0
        current_zoom = max(12, min(16, 12 + zoom_offset))
        factor = 2 ** (current_zoom - 12)
        x12_min = self.map_center_x - (self.width/2) / self.zoom_scale
        x12_max = self.map_center_x + (self.width/2) / self.zoom_scale
        y12_min = self.map_center_y - (self.height/2) / self.zoom_scale
        y12_max = self.map_center_y + (self.height/2) / self.zoom_scale
        min_col = int(math.floor((x12_min * factor) / 256)) - 1
        max_col = int(math.ceil((x12_max * factor) / 256)) + 1
        min_row = int(math.floor((y12_min * factor) / 256)) - 1
        max_row = int(math.ceil((y12_max * factor) / 256)) + 1
        self.tile_group.add(Color(1, 1, 1, 1))
        try:
            self.cursor.execute(
                "SELECT tile_column, tile_row, tile_data FROM tiles WHERE zoom_level=? AND tile_column BETWEEN ? AND ? AND tile_row BETWEEN ? AND ?",
                (current_zoom, min_col, max_col, min_row, max_row))
            for col, row, data in self.cursor.fetchall():
                key = (current_zoom, col, row)
                if key not in self._texture_cache:
                    try:
                        self._texture_cache[key] = CoreImage(BytesIO(data), ext='png').texture
                    except:
                        try:
                            self._texture_cache[key] = CoreImage(BytesIO(data), ext='jpg').texture
                        except:
                            continue
                texture = self._texture_cache[key]
                x_12 = (col * 256) / factor
                y_12 = (row * 256) / factor
                rx = cx + (x_12 - self.map_center_x) * self.zoom_scale
                ry = cy + (y_12 - self.map_center_y) * self.zoom_scale
                rs = (256 / factor) * self.zoom_scale
                self.tile_group.add(Rectangle(texture=texture, pos=(rx, ry), size=(rs, rs)))
        except:
            pass
        self.refresh_markers()

    def refresh_markers(self):
        self.marker_group.clear()
        self.marker_group.add(Color(*self.theme["text"]))
        ms = 30
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        if os.path.exists(PATH_ARROW):
            px = cx + (self.player_x - self.map_center_x) * self.zoom_scale
            py = cy + (self.player_y - self.map_center_y) * self.zoom_scale
            self.marker_group.add(Rectangle(source=PATH_ARROW,
                                            pos=(px-18, py-18), size=(36, 36)))
        for marker in self.markers:
            pos = marker['pos']
            tex_path = marker['tex']
            
            if not self._is_marker_visible(tex_path):
                continue
            
            if "big_location" in tex_path and self.zoom_scale > 2.5:
                continue
                
            rx = cx + (pos[0] - self.map_center_x) * self.zoom_scale
            ry = cy + (pos[1] - self.map_center_y) * self.zoom_scale
            self.marker_group.add(Rectangle(source=tex_path, pos=(rx-ms/2, ry), size=(ms, ms)))
            if marker.get('text'):
                lbl = CoreLabel(text=marker['text'], font_size=13, bold=True, color=self.theme["text_bright"])
                lbl.refresh()
                tex = lbl.texture
                self.marker_group.add(Rectangle(texture=tex,
                                                pos=(rx-tex.width/2, ry-tex.height-5),
                                                size=tex.size))

    def add_marker(self, pos, texture_path, text=""):
        marker_id = time.time()
        self.markers.append({'id': marker_id, 'pos': pos, 'tex': texture_path,
                             'text': text, 'quest_title': '', 'quest_desc': ''})
        self.refresh_markers()
        return marker_id

    def remove_marker(self, marker_id):
        self.markers = [m for m in self.markers if m['id'] != marker_id]
        self.refresh_markers()

    def confirm_delete_marker(self, marker):
        self._long_press_event = None
        view = ModalView(size_hint=(None, None), size=(300, 140), background_color=(0,0,0,0.96))
        box = BoxLayout(orientation='vertical', padding=15, spacing=12)
        box.add_widget(Label(text="Удалить эту метку?", font_size='16sp', bold=True, color=self.theme["text_bright"]))
        btn_layout = BoxLayout(spacing=12)
        btn_yes = Button(text="УДАЛИТЬ", background_normal='', background_color=self.theme["error"], bold=True)
        btn_no = Button(text="НЕТ", background_normal='', background_color=self.theme["button_bg"], bold=True)
        
        def on_yes(*args):
            self.remove_marker(marker['id'])
            pda = self._get_pda()
            if pda:
                pda.add_history("Метка удалена")
            view.dismiss()
            
        btn_yes.bind(on_release=on_yes)
        btn_no.bind(on_release=lambda x: view.dismiss())
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        box.add_widget(btn_layout)
        view.add_widget(box)
        view.open()

    def on_mouse_pos(self, window, pos):
        pda = self._get_pda()
        if not pda or not hasattr(pda, 'current_tab') or pda.current_tab != "КАРТА" or not self.parent:
            self.hide_tooltip()
            return
        
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        if self.m and self.collide_point(*pos):
            local_x = self.map_center_x + (pos[0] - cx) / self.zoom_scale
            local_y = self.map_center_y + (pos[1] - cy) / self.zoom_scale
            tile_x = local_x / 256.0
            tile_y = local_y / 256.0
            n = 2.0 ** 12
            lon = (tile_x / n) * 360.0 - 180.0
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile_y / n)))
            lat = math.degrees(lat_rad)
            try:
                mgrs_coord = self.m.toMGRS(lat, lon)
                if isinstance(mgrs_coord, bytes):
                    mgrs_coord = mgrs_coord.decode('utf-8')
                pda.mgrs_label.text = f"КУРСОР: [b]{mgrs_coord}[/b]"
            except:
                pda.mgrs_label.text = "КУРСОР: N/A"
        
        hovered_quest = None
        for marker in self.markers:
            if "quest" in marker['tex'] and marker.get('quest_title'):
                rx = cx + (marker['pos'][0] - self.map_center_x) * self.zoom_scale
                ry = cy + (marker['pos'][1] - self.map_center_y) * self.zoom_scale
                if abs(pos[0]-rx) < 22 and abs(pos[1]-ry) < 22:
                    hovered_quest = marker
                    break
        if hovered_quest:
            self.show_tooltip(hovered_quest, pos)
        else:
            self.hide_tooltip()

    def show_tooltip(self, marker, mouse_pos):
        pda = self._get_pda()
        if not pda:
            return
        if self._hover_tooltip:
            self._hover_tooltip.pos = (mouse_pos[0]+18, mouse_pos[1]-35)
            self._hover_tooltip.title_lbl.text = f"[b]{marker['quest_title'].upper()}[/b]"
            self._hover_tooltip.desc_lbl.text = marker['quest_desc']
            return
        self._hover_tooltip = BoxLayout(orientation='vertical', size_hint=(None,None),
                                        size=(240, 75), padding=8, spacing=3)
        self._hover_tooltip.pos = (mouse_pos[0]+18, mouse_pos[1]-35)
        with self._hover_tooltip.canvas.before:
            Color(*self.theme["panel_bg"])
            self._hover_tooltip.bg = Rectangle(pos=self._hover_tooltip.pos, size=self._hover_tooltip.size)
            Color(*self.theme["border"])
            self._hover_tooltip.border = Line(rectangle=(self._hover_tooltip.x, self._hover_tooltip.y,
                                                         self._hover_tooltip.width, self._hover_tooltip.height), width=1.5)
        self._hover_tooltip.bind(pos=self._update_tooltip_canvas, size=self._update_tooltip_canvas)
        title_lbl = Label(text=f"[b]{marker['quest_title'].upper()}[/b]", markup=True,
                          color=self.theme["text_bright"], font_size='12sp')
        desc_lbl = Label(text=marker['quest_desc'], color=self.theme["text"], font_size='10sp')
        self._hover_tooltip.title_lbl = title_lbl
        self._hover_tooltip.desc_lbl = desc_lbl
        self._hover_tooltip.add_widget(title_lbl)
        self._hover_tooltip.add_widget(desc_lbl)
        pda.add_widget(self._hover_tooltip)

    def _update_tooltip_canvas(self, instance, *args):
        instance.bg.pos = instance.pos
        instance.bg.size = instance.size
        instance.border.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def hide_tooltip(self):
        if self._hover_tooltip:
            pda = self._get_pda()
            if pda and self._hover_tooltip in pda.children:
                pda.remove_widget(self._hover_tooltip)
            self._hover_tooltip = None

    def show_label_input(self, local_pos, tex_path, screen_pos):
        pda = self._get_pda()
        if not pda:
            return
        ti = TextInput(size_hint=(None,None), size=(180, 40),
                       pos=(screen_pos[0]-90, screen_pos[1]-80),
                       multiline=False, font_size='14sp')
        pda.add_widget(ti)
        def on_enter(instance):
            text = instance.text.strip()
            self.add_marker(local_pos, tex_path, text)
            pda.remove_widget(instance)
            pda.add_history(f"Метка: {text}" if text else "Марка добавлена")
        ti.bind(on_text_validate=on_enter)
        def on_focus(instance, value):
            if not value and instance in pda.children:
                pda.remove_widget(instance)
        ti.bind(focus=on_focus)
        Clock.schedule_once(lambda dt: setattr(ti, 'focus', True), 0.1)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        cx = self.x + self.width/2
        cy = self.y + self.height/2
        local_pos = (self.map_center_x + (touch.x-cx)/self.zoom_scale,
                     self.map_center_y + (touch.y-cy)/self.zoom_scale)
        if touch.is_mouse_scrolling:
            old_scale = self.zoom_scale
            factor = 1.2 if touch.button == 'scrollup' else 0.8
            self.zoom_scale *= factor
            self.map_center_x += (touch.x-cx) * (1.0/old_scale - 1.0/self.zoom_scale)
            self.map_center_y += (touch.y-cy) * (1.0/old_scale - 1.0/self.zoom_scale)
            self.enforce_bounds()
            return True
        if touch.button == 'right':
            pda = self._get_pda()
            if pda and hasattr(pda, 'selected_marker') and pda.selected_marker:
                if pda.placing_quest:
                    marker_id = self.add_marker(local_pos, pda.selected_marker, "")
                    pda.finalize_quest_creation(marker_id, local_pos)
                else:
                    if any(x in pda.selected_marker for x in ["localion.png", "big_location.png", "home.png"]):
                        self.show_label_input(local_pos, pda.selected_marker, touch.pos)
                    else:
                        self.add_marker(local_pos, pda.selected_marker, "")
                        pda.add_history("Маркер установлен")
                pda.cancel_selection()
                return True
            return False
        if touch.button == 'left':
            for marker in self.markers:
                if "quest" not in marker['tex']:
                    rx = cx + (marker['pos'][0]-self.map_center_x)*self.zoom_scale
                    ry = cy + (marker['pos'][1]-self.map_center_y)*self.zoom_scale
                    if abs(touch.x-rx) < 22 and abs(touch.y-ry) < 22:
                        self._long_press_event = Clock.schedule_once(
                            lambda dt, m=marker: self.confirm_delete_marker(m), 0.8)
                        break
            touch.grab(self)
            touch.ud['prev_screen_pos'] = touch.pos
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self._long_press_event:
                dx = touch.pos[0] - touch.ud['prev_screen_pos'][0]
                dy = touch.pos[1] - touch.ud['prev_screen_pos'][1]
                if (dx**2 + dy**2) > 20:
                    Clock.unschedule(self._long_press_event)
                    self._long_press_event = None
            dx = touch.pos[0] - touch.ud['prev_screen_pos'][0]
            dy = touch.pos[1] - touch.ud['prev_screen_pos'][1]
            self.map_center_x -= dx/self.zoom_scale
            self.map_center_y -= dy/self.zoom_scale
            self.enforce_bounds()
            touch.ud['prev_screen_pos'] = touch.pos
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self._long_press_event:
                Clock.unschedule(self._long_press_event)
                self._long_press_event = None
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)