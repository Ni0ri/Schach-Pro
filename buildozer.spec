[app]
title = Schach Pro
package.name = schachpro
package.domain = org.schach
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy==2.3.0,pillow

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

orientation = portrait
fullscreen = 0

# Android Settings
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.allow_backup = True

# Build
log_level = 2
warn_on_root = 0

[buildozer]
log_level = 2
warn_on_root = 0
