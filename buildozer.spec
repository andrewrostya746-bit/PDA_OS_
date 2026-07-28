[app]
# (str) Title of your application
title = PDA OS

# (str) Package name
package.name = pdaos

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code directory
source.dir = .

# (list) Source files to include (extensions)
source.include_exts = py,png,jpg,kv,atlas,json

# (value) Version of your application
version = 0.1

# (list) Application requirements
# Note: we use python3 and kivy as your project requires
requirements = python3,kivy

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Android architectures to build for.
# Left only arm64-v8a to prevent GitHub Actions memory crash.
android.archs = arm64-v8a

# (bool) Allow backup
android.allow_backup = True

# (bool) Automatically accept SDK licenses (CRITICAL for GitHub Actions)
android.accept_sdk_license = True

# (int) Target Android API. 33 or 34 is required by Google Play now.
android.api = 33

# (int) Minimum API your APK will support (API 24 is Android 7.0, minimum for Kivy)
android.minapi = 24

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug and outputs)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
