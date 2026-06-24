[app]
title = LED Panel Controller
package.name = ledpanelcontroller
package.domain = com.ledpanel

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

# Cambiado a las versiones estables óptimas para evitar la compilación larga de recetas nativas viejas
requirements = python3, kivy==2.2.1, kivymd==1.1.1, android, pyjnius, setuptools

orientation = portrait

android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# Ajustes de empaquetado para compatibilidad con las librerías de Bluetooth
android.api = 33
android.minapi = 23
android.ndk = 25b
android.ndk_api = 23
android.sdk = 33

android.accept_sdk_license = True
android.skip_sdk_hints = False

android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = 0

[buildozer]
log_level = 2
warn_on_root = 1
