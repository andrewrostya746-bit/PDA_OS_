from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')

# Оптимизация под планшет 1280x800
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'resizable', True)
Config.set('kivy', 'keyboard_mode', 'system')  # ← ДОБАВИТЬ ЭТУ СТРОКУ!

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from config import load_settings

Window.borderless = False  # ← ИЗМЕНИТЬ на False (не fullscreen!)
Window.fullscreen = False  # ← ИЗМЕНИТЬ на False
Window.size = (1280, 800)  # ← ДОБАВИТЬ


class PDAApp(App):
    def build(self):
        root = FloatLayout()
        settings = load_settings()
        password = settings.get("password", "")
        
        if password:
            from pda_interface import LoginScreen
            login = LoginScreen(on_success_callback=lambda: self._start_pda(root))
            root.add_widget(login)
        else:
            self._start_pda(root)
        
        return root
    
    def _start_pda(self, root):
        from pda_interface import PDA_Interface
        pda = PDA_Interface()
        root.add_widget(pda)


if __name__ == '__main__':
    PDAApp().run()