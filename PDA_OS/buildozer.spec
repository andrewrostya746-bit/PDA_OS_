[app]
title = PDA OS
package.name = pdaos
source.dir = .
version = 2.0
requirements = python3,kivy,plyer
orientation = landscape
fullscreen = 1
android.api = 21
android.minapi = 21
android.ndk = 25c
android.arch = armeabi-v7a
android.entrypoint = main.py
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,BLUETOOTH

[buildozer]
log_level = 2
warn_on_root = 0
