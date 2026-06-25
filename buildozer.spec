[app]
title = LED Panel Controller
package.name = ledpanelcontroller
package.domain = com.ledpanel

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.1.1,android,pyjnius

orientation = portrait

android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 33
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = False

p4a.hook =

[buildozer]
log_level = 2
warn_on_root = 1
