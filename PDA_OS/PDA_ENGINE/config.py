import os
import json

# Авто-определение пути
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Если мы в PDA_ENGINE, поднимаемся на уровень выше
if os.path.basename(BASE_PATH) == "PDA_ENGINE":
    BASE_PATH = os.path.dirname(BASE_PATH)

PATH_TEX = os.path.join(BASE_PATH, "PDA_TEXTURES")
PATH_MAP = os.path.join(BASE_PATH, "PDA_MAP", "PDA_MAP.mbtiles")
PATH_SOUND_1 = os.path.join(BASE_PATH, "PDA_SOUND", "PDA_SOUND_1.ogg")
PATH_SOUND_2 = os.path.join(BASE_PATH, "PDA_SOUND", "PDA_SOUND_2.ogg")
PATH_ARROW = os.path.join(PATH_TEX, "strelochka.png")
PATH_CHANGE = os.path.join(PATH_TEX, "change.png")
PATH_SETTINGS = os.path.join(BASE_PATH, "settings.json")
PATH_SAVE_DATA = os.path.join(BASE_PATH, "save_data.json")

# Проверка
print(f"BASE_PATH: {BASE_PATH}")
print(f"PATH_TEX существует: {os.path.exists(PATH_TEX)}")
if os.path.exists(PATH_TEX):
    print(f"Файлы текстур: {len(os.listdir(PATH_TEX))} шт.")
else:
    print("ПАПКА ТЕКСТУР НЕ НАЙДЕНА!")

DEFAULT_SETTINGS = {
    "sound_volume": 0.7,
    "sound_enabled": True,
    "theme": "dark_green",
    "password": "1111",
    "language": "RU",
    "gps_update_interval": 2,
    "map_cache_size": 100,
    "startup_tab": "КАРТА"
}

THEMES = {
    "dark_green": {
        "name": "Тёмно-зелёная",
        "bg_main": (0.1, 0.1, 0.1, 1),
        "bg_top": (0.04, 0.05, 0.04, 1),
        "accent": (0, 0.5, 0, 1),
        "text": (0, 0.9, 0, 1),
        "text_bright": (0, 1, 0, 1),
        "button_bg": (0.12, 0.15, 0.12, 1),
        "button_active": (0, 0.6, 0, 1),
        "panel_bg": (0.06, 0.08, 0.06, 0.9),
        "border": (0, 0.4, 0, 1),
        "warning": (1, 0.5, 0, 1),
        "error": (1, 0, 0, 1)
    },
    "dark_amber": {
        "name": "Тёмно-янтарная",
        "bg_main": (0.08, 0.08, 0.06, 1),
        "bg_top": (0.04, 0.04, 0.02, 1),
        "accent": (0.6, 0.4, 0, 1),
        "text": (1, 0.8, 0, 1),
        "text_bright": (1, 0.9, 0.3, 1),
        "button_bg": (0.15, 0.12, 0.08, 1),
        "button_active": (0.6, 0.4, 0, 1),
        "panel_bg": (0.08, 0.06, 0.04, 0.9),
        "border": (0.5, 0.3, 0, 1),
        "warning": (1, 0.7, 0, 1),
        "error": (1, 0.2, 0, 1)
    },
    "dark_blue": {
        "name": "Тёмно-синяя",
        "bg_main": (0.06, 0.08, 0.12, 1),
        "bg_top": (0.03, 0.04, 0.06, 1),
        "accent": (0, 0.3, 0.6, 1),
        "text": (0, 0.7, 1, 1),
        "text_bright": (0.3, 0.8, 1, 1),
        "button_bg": (0.08, 0.1, 0.15, 1),
        "button_active": (0, 0.4, 0.7, 1),
        "panel_bg": (0.04, 0.06, 0.1, 0.9),
        "border": (0, 0.3, 0.5, 1),
        "warning": (0.8, 0.6, 0, 1),
        "error": (1, 0.2, 0.2, 1)
    },
    "monochrome": {
        "name": "Монохромная",
        "bg_main": (0.08, 0.08, 0.08, 1),
        "bg_top": (0.04, 0.04, 0.04, 1),
        "accent": (0.4, 0.4, 0.4, 1),
        "text": (0.8, 0.8, 0.8, 1),
        "text_bright": (1, 1, 1, 1),
        "button_bg": (0.12, 0.12, 0.12, 1),
        "button_active": (0.5, 0.5, 0.5, 1),
        "panel_bg": (0.06, 0.06, 0.06, 0.9),
        "border": (0.3, 0.3, 0.3, 1),
        "warning": (0.8, 0.8, 0, 1),
        "error": (0.8, 0.2, 0.2, 1)
    },
    "red_zone": {
        "name": "Красная Зона",
        "bg_main": (0.1, 0.05, 0.05, 1),
        "bg_top": (0.06, 0.02, 0.02, 1),
        "accent": (0.6, 0.1, 0.1, 1),
        "text": (1, 0.5, 0.5, 1),
        "text_bright": (1, 0.7, 0.7, 1),
        "button_bg": (0.15, 0.08, 0.08, 1),
        "button_active": (0.7, 0.1, 0.1, 1),
        "panel_bg": (0.1, 0.04, 0.04, 0.9),
        "border": (0.5, 0.1, 0.1, 1),
        "warning": (1, 0.5, 0, 1),
        "error": (1, 0, 0, 1)
    }
}


def load_settings():
    if os.path.exists(PATH_SETTINGS):
        try:
            with open(PATH_SETTINGS, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                settings = DEFAULT_SETTINGS.copy()
                settings.update(saved)
                return settings
        except:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    try:
        with open(PATH_SETTINGS, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False


def get_theme(theme_name=None):
    if theme_name is None:
        settings = load_settings()
        theme_name = settings.get("theme", "dark_green")
    return THEMES.get(theme_name, THEMES["dark_green"])


def save_app_data(markers, quests, history, tracked_macs, heatmap_points):
    data = {
        "markers": [],
        "quests": [],
        "history": [],
        "tracked_macs": tracked_macs,
        "heatmap_points": heatmap_points
    }
    
    for marker in markers:
        data["markers"].append({
            'id': marker.get('id', 0),
            'pos': list(marker.get('pos', [0, 0])),
            'tex': marker.get('tex', ''),
            'text': marker.get('text', ''),
            'quest_title': marker.get('quest_title', ''),
            'quest_desc': marker.get('quest_desc', '')
        })
    
    for quest in quests:
        data["quests"].append({
            'title': quest.get('title', ''),
            'desc': quest.get('desc', ''),
            'icon_path': quest.get('icon_path', ''),
            'marker_pos': list(quest.get('marker_pos', [0, 0])),
            'marker_id': quest.get('marker_id', 0)
        })
    
    data["history"] = history
    
    try:
        with open(PATH_SAVE_DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False


def load_app_data():
    if not os.path.exists(PATH_SAVE_DATA):
        return None
    
    try:
        with open(PATH_SAVE_DATA, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        markers = []
        for m in data.get("markers", []):
            markers.append({
                'id': m.get('id', 0),
                'pos': tuple(m.get('pos', [0, 0])),
                'tex': m.get('tex', ''),
                'text': m.get('text', ''),
                'quest_title': m.get('quest_title', ''),
                'quest_desc': m.get('quest_desc', '')
            })
        
        return {
            'markers': markers,
            'quests': data.get("quests", []),
            'history': data.get("history", []),
            'tracked_macs': data.get("tracked_macs", []),
            'heatmap_points': data.get("heatmap_points", [])
        }
    except:
        return None