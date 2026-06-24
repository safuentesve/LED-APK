# ============================================================
#  LED Panel Controller - Python/Kivy
#  Protocolo BLE extraído del APK com.led.spotled v1.9.4
#  UUIDs reales: FF10/FF11 y FF20/FF21
# ============================================================

import threading
import struct
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (
    StringProperty, BooleanProperty, ListProperty, NumericProperty
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar

# ── Android BLE imports (solo disponibles en Android) ──────
try:
    from jnius import autoclass, cast, java_method
    from android.permissions import request_permissions, Permission, check_permission

    BluetoothAdapter        = autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothDevice_cls     = autoclass('android.bluetooth.BluetoothDevice')
    BluetoothGatt_cls       = autoclass('android.bluetooth.BluetoothGatt')
    BluetoothGattCallback   = autoclass('android.bluetooth.BluetoothGattCallback')
    BluetoothGattCharacteristic = autoclass('android.bluetooth.BluetoothGattCharacteristic')
    UUID_cls                = autoclass('java.util.UUID')
    PythonActivity          = autoclass('org.kivy.android.PythonActivity')
    ANDROID = True
except Exception:
    ANDROID = False

# ── UUIDs BLE (extraídos del APK) ─────────────────────────
SVC_FF10   = "0000ff10-0000-1000-8000-00805f9b34fb"
CHAR_FF11  = "0000ff11-0000-1000-8000-00805f9b34fb"
CHAR_FF12  = "0000ff12-0000-1000-8000-00805f9b34fb"
SVC_FF20   = "0000ff20-0000-1000-8000-00805f9b34fb"
CHAR_FF21  = "0000ff21-0000-1000-8000-00805f9b34fb"

# ── Efectos de animación ───────────────────────────────────
EFFECTS = [
    (0,  "➡ Desplazar"),
    (1,  "⬆ Subir"),
    (2,  "⬇ Bajar"),
    (3,  "✦ Parpadear"),
    (4,  "■ Estático"),
    (5,  "◈ Aparecer"),
    (6,  "↺ Girar"),
    (7,  "★ Arcoíris"),
]

# ── Paleta de colores de texto ─────────────────────────────
TEXT_COLORS = [
    "#FFFFFF", "#FF0000", "#FF6600", "#FFFF00",
    "#00FF00", "#00FFFF", "#0080FF", "#FF00FF",
    "#FF9999", "#99FF99", "#99CCFF", "#FFCC99",
    "#FF3399", "#00CC66", "#9933FF", "#FF6633",
]

# ── KV Layout ─────────────────────────────────────────────
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex
#:import MDColors kivymd.color_definitions

<ColorSwatch>:
    size_hint: None, None
    size: dp(36), dp(36)
    canvas.before:
        Color:
            rgba: root.swatch_color
        RoundedRectangle:
            size: self.size
            pos: self.pos
            radius: [dp(8)]
        Color:
            rgba: (1,1,1,1) if root.selected else (0,0,0,0)
        Line:
            rounded_rectangle: [self.x+2, self.y+2, self.width-4, self.height-4, dp(6)]
            width: 2.5

<EffectButton>:
    size_hint_y: None
    height: dp(64)
    md_bg_color: app.accent_color if root.selected else app.surface2_color
    elevation: 0
    radius: [dp(10)]

MDScreen:
    md_bg_color: app.bg_color

    MDBoxLayout:
        orientation: 'vertical'

        # ── Header ─────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(60)
            md_bg_color: app.surface_color
            padding: dp(16), 0
            spacing: dp(12)

            MDLabel:
                text: "💡"
                font_style: "H5"
                size_hint_x: None
                width: dp(40)
                halign: "center"

            MDLabel:
                text: "LED Panel Controller"
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: app.text_color

            Widget:

            MDIcon:
                id: status_icon
                icon: "bluetooth-off"
                theme_text_color: "Custom"
                text_color: app.error_color
                size_hint_x: None
                width: dp(36)

        # ── Scroll ─────────────────────────────────────────
        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(14)
                spacing: dp(12)
                adaptive_height: True

                # ── BT Card ────────────────────────────────
                MDCard:
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(10)
                    md_bg_color: app.surface_color
                    radius: [dp(14)]
                    elevation: 0
                    adaptive_height: True

                    MDLabel:
                        text: "CONEXIÓN BLUETOOTH"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: app.text2_color

                    MDRaisedButton:
                        id: bt_btn
                        text: "Buscar panel LED"
                        md_bg_color: app.accent_color
                        elevation: 0
                        on_release: app.toggle_bluetooth()
                        size_hint_x: 1

                    MDLabel:
                        id: device_label
                        text: "Sin dispositivo conectado"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: app.text2_color
                        font_style: "Caption"

                # ── Texto Card ─────────────────────────────
                MDCard:
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(10)
                    md_bg_color: app.surface_color
                    radius: [dp(14)]
                    elevation: 0
                    adaptive_height: True

                    MDLabel:
                        text: "MENSAJE"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: app.text2_color

                    MDTextField:
                        id: msg_field
                        hint_text: "Escribe tu mensaje aquí..."
                        text: "Hola! :)"
                        max_text_length: 120
                        mode: "fill"
                        fill_color: app.surface2_color
                        line_color_focus: app.accent_color
                        text_color_focus: app.text_color
                        text_color_normal: app.text_color
                        multiline: True

                # ── Efectos Card ───────────────────────────
                MDCard:
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(10)
                    md_bg_color: app.surface_color
                    radius: [dp(14)]
                    elevation: 0
                    adaptive_height: True

                    MDLabel:
                        text: "ANIMACIÓN"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: app.text2_color

                    MDGridLayout:
                        id: effects_grid
                        cols: 2
                        spacing: dp(8)
                        adaptive_height: True

                    MDBoxLayout:
                        adaptive_height: True
                        spacing: dp(12)

                        MDLabel:
                            text: "Velocidad"
                            size_hint_x: None
                            width: dp(80)
                            theme_text_color: "Custom"
                            text_color: app.text2_color

                        MDSlider:
                            id: speed_slider
                            min: 1
                            max: 10
                            value: 5
                            step: 1
                            hint: True
                            hint_bg_color: app.accent_color
                            color: app.accent_color

                # ── Color Texto ────────────────────────────
                MDCard:
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(12)
                    md_bg_color: app.surface_color
                    radius: [dp(14)]
                    elevation: 0
                    adaptive_height: True

                    MDLabel:
                        text: "COLOR DEL TEXTO"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: app.text2_color

                    MDGridLayout:
                        id: text_color_grid
                        cols: 8
                        spacing: dp(8)
                        adaptive_height: True

                    MDBoxLayout:
                        adaptive_height: True
                        spacing: dp(10)

                        MDLabel:
                            id: text_color_preview
                            text: "  Aa  "
                            size_hint_x: None
                            width: dp(60)
                            halign: "center"
                            theme_text_color: "Custom"
                            text_color: [1,1,1,1]
                            font_style: "H6"
                            canvas.before:
                                Color:
                                    rgba: app.surface2_color
                                RoundedRectangle:
                                    size: self.size
                                    pos: self.pos
                                    radius: [dp(8)]

                        MDLabel:
                            text: "Toca un color arriba"
                            theme_text_color: "Custom"
                            text_color: app.text2_color
                            font_style: "Caption"

                # ── Color Fondo ────────────────────────────
                MDCard:
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(12)
                    md_bg_color: app.surface_color
                    radius: [dp(14)]
                    elevation: 0
                    adaptive_height: True

                    MDLabel:
                        text: "FONDO DEL PANEL"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: app.text2_color

                    MDGridLayout:
                        id: bg_color_grid
                        cols: 8
                        spacing: dp(8)
                        adaptive_height: True

                    MDBoxLayout:
                        adaptive_height: True
                        spacing: dp(10)

                        MDLabel:
                            id: bg_color_preview
                            text: "  "
                            size_hint_x: None
                            width: dp(60)
                            canvas.before:
                                Color:
                                    rgba: app.selected_bg_color
                                RoundedRectangle:
                                    size: self.size
                                    pos: self.pos
                                    radius: [dp(8)]

                        MDLabel:
                            text: "Color de fondo del panel"
                            theme_text_color: "Custom"
                            text_color: app.text2_color
                            font_style: "Caption"

                # ── Send ───────────────────────────────────
                MDRaisedButton:
                    id: send_btn
                    text: "📤  Enviar al panel"
                    md_bg_color: app.accent_color
                    elevation: 0
                    disabled: True
                    size_hint_x: 1
                    size_hint_y: None
                    height: dp(52)
                    font_size: "16sp"
                    on_release: app.send_to_panel()

                # ── Log ────────────────────────────────────
                MDCard:
                    md_bg_color: app.surface2_color
                    radius: [dp(10)]
                    elevation: 0
                    size_hint_y: None
                    height: dp(130)
                    padding: dp(10)

                    ScrollView:
                        id: log_scroll

                        MDLabel:
                            id: log_label
                            text: "» App lista. Conecta tu panel LED."
                            theme_text_color: "Custom"
                            text_color: app.text2_color
                            font_style: "Caption"
                            font_name: "RobotoMono"
                            adaptive_height: True
                            halign: "left"
"""


# ── Widgets personalizados ─────────────────────────────────
class ColorSwatch(ButtonBehavior, Widget):
    swatch_color = ListProperty([1, 1, 1, 1])
    selected = BooleanProperty(False)


class EffectButton(MDFlatButton):
    selected = BooleanProperty(False)


# ── Protocolo BLE SpotLED ─────────────────────────────────
class LEDProtocol:
    """
    Construcción de frames según el protocolo de com.led.spotled.
    Extraído del DEX: CharacterStringObject + ColorObject + CommandExecutor.
    Header: 0x99, CMD: 0x04 (set text), longitud 2 bytes, payload, checksum XOR.
    """
    CMD_SET_TEXT    = 0x04
    CMD_DISCONNECT  = 0x06
    CMD_BRIGHTNESS  = 0x07
    HEADER          = 0x99

    @staticmethod
    def hex_to_rgb(hex_color: str):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    @classmethod
    def build_text_frame(cls, text: str, text_color: str, bg_color: str,
                          effect: int, speed: int) -> bytes:
        """
        Estructura del frame (reverse-engineered del APK):
        [HEADER=0x99][CMD=0x04][LEN_H][LEN_L]
        [EFFECT][SPEED_INV][ALIGN=0x01]
        [TEXT_R][TEXT_G][TEXT_B]
        [BG_R][BG_G][BG_B]
        [TEXT_BYTES...]
        [CHECKSUM_XOR]
        """
        tr, tg, tb = cls.hex_to_rgb(text_color)
        br, bg_r, bb = cls.hex_to_rgb(bg_color)
        text_bytes = text.encode('utf-8')

        payload = bytes([
            cls.CMD_SET_TEXT,
            effect & 0xFF,
            max(1, 11 - speed),   # velocidad invertida
            0x01,                  # alineación centro
            tr, tg, tb,            # color texto
            br, bg_r, bb,          # color fondo
        ]) + text_bytes

        lh = (len(payload) >> 8) & 0xFF
        ll = len(payload) & 0xFF
        frame = bytes([cls.HEADER, cls.CMD_SET_TEXT, lh, ll]) + payload

        checksum = 0
        for b in frame:
            checksum ^= b
        return frame + bytes([checksum & 0xFF])

    @classmethod
    def build_disconnect_frame(cls) -> bytes:
        payload = bytes([cls.CMD_DISCONNECT])
        frame = bytes([cls.HEADER, cls.CMD_DISCONNECT, 0x00, 0x01]) + payload
        cs = 0
        for b in frame:
            cs ^= b
        return frame + bytes([cs & 0xFF])


# ── GattCallback para Android ─────────────────────────────
if ANDROID:
    from jnius import PythonJavaClass, java_method

    class GattCallback(PythonJavaClass):
        __javainterfaces__ = ['android/bluetooth/BluetoothGattCallback']
        __javacontext__ = 'app'

        def __init__(self, app_ref):
            super().__init__()
            self.app = app_ref

        @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
        def onConnectionStateChange(self, gatt, status, new_state):
            # STATE_CONNECTED = 2, STATE_DISCONNECTED = 0
            if new_state == 2 and status == 0:
                Clock.schedule_once(lambda dt: self.app._on_gatt_connected(gatt), 0)
            else:
                Clock.schedule_once(lambda dt: self.app._on_gatt_disconnected(), 0)

        @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
        def onServicesDiscovered(self, gatt, status):
            if status == 0:
                Clock.schedule_once(lambda dt: self.app._on_services_discovered(gatt), 0)

        @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V')
        def onCharacteristicWrite(self, gatt, characteristic, status):
            ok = (status == 0)
            Clock.schedule_once(lambda dt: self.app._on_write_done(ok), 0)

        @java_method('(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V')
        def onCharacteristicChanged(self, gatt, characteristic):
            pass


# ── App Principal ─────────────────────────────────────────
class LEDPanelApp(MDApp):

    # KivyMD theme
    title = "LED Panel"
    theme_cls_primary_palette = "DeepPurple"

    # Colores custom
    bg_color      = ListProperty(get_color_from_hex("#0a0a0f"))
    surface_color = ListProperty(get_color_from_hex("#14141c"))
    surface2_color= ListProperty(get_color_from_hex("#1c1c28"))
    accent_color  = ListProperty(get_color_from_hex("#6c63ff"))
    text_color    = ListProperty(get_color_from_hex("#f0f0ff"))
    text2_color   = ListProperty(get_color_from_hex("#8888aa"))
    error_color   = ListProperty(get_color_from_hex("#ff5252"))
    ok_color      = ListProperty(get_color_from_hex("#00e676"))

    # Estado
    selected_text_color = ListProperty(get_color_from_hex("#FFFFFF"))
    selected_bg_color   = ListProperty(get_color_from_hex("#000000"))
    selected_effect     = NumericProperty(0)

    # BLE
    gatt        = None
    write_char  = None
    connected   = False
    gatt_cb     = None
    _write_queue = []
    _writing     = False

    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def on_start(self):
        self._build_effects()
        self._build_color_palettes()
        if ANDROID:
            self._request_permissions()

    # ── Permisos Android ──────────────────────────────────
    def _request_permissions(self):
        perms = [
            Permission.BLUETOOTH,
            Permission.BLUETOOTH_ADMIN,
            Permission.BLUETOOTH_SCAN,
            Permission.BLUETOOTH_CONNECT,
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
        ]
        request_permissions(perms, self._on_permissions)

    def _on_permissions(self, permissions, grants):
        if all(grants):
            self.log("Permisos Bluetooth OK ✓", "ok")
        else:
            self.log("⚠ Algunos permisos denegados", "err")

    # ── UI Builders ───────────────────────────────────────
    def _build_effects(self):
        grid = self.root.ids.effects_grid
        grid.clear_widgets()
        for eid, elabel in EFFECTS:
            btn = MDRaisedButton(
                text=elabel,
                md_bg_color=self.accent_color if eid == 0 else self.surface2_color,
                elevation=0,
                size_hint=(1, None),
                height="52dp",
            )
            btn.bind(on_release=partial(self._select_effect, eid))
            btn._eid = eid
            grid.add_widget(btn)

    def _build_color_palettes(self):
        # Texto
        tgrid = self.root.ids.text_color_grid
        tgrid.clear_widgets()
        for i, hexc in enumerate(TEXT_COLORS):
            sw = ColorSwatch(
                swatch_color=get_color_from_hex(hexc),
                selected=(i == 0)
            )
            sw._hex = hexc
            sw.bind(on_release=partial(self._select_text_color, hexc))
            tgrid.add_widget(sw)

        # Fondo
        bg_colors = [
            "#000000", "#FF0000", "#00FF00",
            "#0000FF", "#FFFF00", "#FF00FF",
            "#00FFFF", "#FF6600",
        ]
        bgrid = self.root.ids.bg_color_grid
        bgrid.clear_widgets()
        for i, hexc in enumerate(bg_colors):
            sw = ColorSwatch(
                swatch_color=get_color_from_hex(hexc),
                selected=(i == 0)
            )
            sw._hex = hexc
            sw.bind(on_release=partial(self._select_bg_color, hexc))
            bgrid.add_widget(sw)

    def _select_effect(self, eid, btn):
        self.selected_effect = eid
        grid = self.root.ids.effects_grid
        for w in grid.children:
            w.md_bg_color = self.surface2_color
        btn.md_bg_color = self.accent_color

    def _select_text_color(self, hexc, swatch):
        self.selected_text_color = get_color_from_hex(hexc)
        grid = self.root.ids.text_color_grid
        for w in grid.children:
            w.selected = False
        swatch.selected = True
        preview = self.root.ids.text_color_preview
        preview.text_color = get_color_from_hex(hexc)

    def _select_bg_color(self, hexc, swatch):
        self.selected_bg_color = get_color_from_hex(hexc)
        grid = self.root.ids.bg_color_grid
        for w in grid.children:
            w.selected = False
        swatch.selected = True

    # ── Log ───────────────────────────────────────────────
    def log(self, msg: str, kind: str = "info"):
        colors = {"ok": "#00e676", "err": "#ff5252", "info": "#8888aa"}
        c = colors.get(kind, "#8888aa")
        label = self.root.ids.log_label
        label.text += f"\n[color={c}]» {msg}[/color]"
        label.markup = True
        Clock.schedule_once(lambda dt: self._scroll_log(), 0.1)

    def _scroll_log(self):
        sv = self.root.ids.log_scroll
        sv.scroll_y = 0

    # ── Bluetooth ─────────────────────────────────────────
    def toggle_bluetooth(self):
        if self.connected:
            self._disconnect()
        else:
            self._start_scan()

    def _start_scan(self):
        if not ANDROID:
            self.log("BLE solo disponible en Android", "err")
            return

        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter is None:
            self.log("Este dispositivo no soporta Bluetooth", "err")
            return
        if not adapter.isEnabled():
            self.log("Activa el Bluetooth en tu teléfono", "err")
            return

        self.root.ids.bt_btn.text = "Buscando..."
        self.log("Iniciando escaneo BLE...", "info")

        def scan_thread():
            try:
                scanner = adapter.getBluetoothLeScanner()
                if scanner is None:
                    Clock.schedule_once(lambda dt: self.log("Scanner BLE no disponible", "err"), 0)
                    return

                # Callback de escaneo usando ScanCallback
                from jnius import PythonJavaClass, java_method

                class ScanCb(PythonJavaClass):
                    __javainterfaces__ = ['android/bluetooth/le/ScanCallback']
                    __javacontext__ = 'app'

                    def __init__(cb_self):
                        super().__init__()
                        cb_self.found = False

                    @java_method('(ILandroid/bluetooth/le/ScanResult;)V')
                    def onScanResult(cb_self, callbackType, result):
                        if cb_self.found:
                            return
                        device = result.getDevice()
                        name = device.getName() or ""
                        addr = device.getAddress()

                        # Filtrar por nombre típico de paneles LED
                        led_keywords = ["LED", "BT", "SPOT", "PANEL", "SIGN", "HW"]
                        match = any(k.upper() in name.upper() for k in led_keywords)

                        # También aceptar por UUID del servicio
                        uuids = result.getScanRecord().getServiceUuids()
                        if uuids:
                            uuid_strs = [str(u) for u in uuids.toArray()]
                            if SVC_FF10 in uuid_strs or SVC_FF20 in uuid_strs:
                                match = True

                        if match or (not match and name):
                            cb_self.found = True
                            scanner.stopScan(cb_self)
                            Clock.schedule_once(
                                lambda dt: self.app._connect_device(device, name, addr), 0
                            )

                    @java_method('(I)V')
                    def onScanFailed(cb_self, error):
                        Clock.schedule_once(
                            lambda dt: self.app.log(f"Escaneo falló: código {error}", "err"), 0
                        )

                scan_cb = ScanCb()
                scan_cb.app = self
                scanner.startScan(scan_cb)

                # Timeout 10s
                import time
                time.sleep(10)
                if not scan_cb.found:
                    scanner.stopScan(scan_cb)
                    Clock.schedule_once(
                        lambda dt: self.log("No se encontró ningún panel LED", "err"), 0
                    )
                    Clock.schedule_once(
                        lambda dt: self._reset_bt_btn(), 0
                    )

            except Exception as e:
                Clock.schedule_once(lambda dt: self.log(f"Error scan: {e}", "err"), 0)
                Clock.schedule_once(lambda dt: self._reset_bt_btn(), 0)

        threading.Thread(target=scan_thread, daemon=True).start()

    def _connect_device(self, device, name, addr):
        self.log(f"Dispositivo encontrado: {name or 'Sin nombre'} [{addr}]", "info")
        self.log("Conectando...", "info")

        ctx = PythonActivity.mActivity
        self.gatt_cb = GattCallback(self)
        self.gatt = device.connectGatt(ctx, False, self.gatt_cb)

    def _on_gatt_connected(self, gatt):
        self.log("GATT conectado ✓", "ok")
        gatt.discoverServices()

    def _on_gatt_disconnected(self):
        self.connected = False
        self.write_char = None
        self.gatt = None
        self._update_ui_disconnected()
        self.log("Dispositivo desconectado", "err")

    def _on_services_discovered(self, gatt):
        # Intentar servicio FF10 primero, luego FF20
        write_char = None

        for svc_uuid, char_uuid in [(SVC_FF10, CHAR_FF11), (SVC_FF20, CHAR_FF21)]:
            svc = gatt.getService(UUID_cls.fromString(svc_uuid))
            if svc:
                ch = svc.getCharacteristic(UUID_cls.fromString(char_uuid))
                if ch:
                    write_char = ch
                    self.log(f"Servicio {svc_uuid[-4:].upper()} encontrado ✓", "ok")
                    break

        if write_char is None:
            # Último recurso: buscar en todos los servicios
            services = gatt.getServices()
            for svc in services.toArray():
                chars = svc.getCharacteristics()
                for ch in chars.toArray():
                    props = ch.getProperties()
                    WRITE_NO_RESP = BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE
                    WRITE = BluetoothGattCharacteristic.PROPERTY_WRITE
                    if (props & WRITE_NO_RESP) or (props & WRITE):
                        write_char = ch
                        self.log(f"Char de escritura: {ch.getUuid()}", "info")
                        break
                if write_char:
                    break

        if write_char:
            self.write_char = write_char
            self.gatt = gatt
            self.connected = True
            self._update_ui_connected()
        else:
            self.log("No se encontró característica de escritura", "err")
            gatt.disconnect()

    def _on_write_done(self, ok: bool):
        self._writing = False
        if ok:
            self.log("Chunk enviado ✓", "ok")
        else:
            self.log("Error escribiendo chunk", "err")
        self._flush_queue()

    # ── UI States ─────────────────────────────────────────
    def _update_ui_connected(self):
        self.root.ids.bt_btn.text = "Desconectar"
        self.root.ids.status_icon.icon = "bluetooth"
        self.root.ids.status_icon.text_color = self.ok_color
        self.root.ids.device_label.text = f"✓ Conectado"
        self.root.ids.device_label.theme_text_color = "Custom"
        self.root.ids.device_label.text_color = self.ok_color
        self.root.ids.send_btn.disabled = False
        self.log("¡Conectado! Ya puedes enviar mensajes.", "ok")

    def _update_ui_disconnected(self):
        self.root.ids.bt_btn.text = "Buscar panel LED"
        self.root.ids.status_icon.icon = "bluetooth-off"
        self.root.ids.status_icon.text_color = self.error_color
        self.root.ids.device_label.text = "Sin dispositivo conectado"
        self.root.ids.device_label.text_color = self.text2_color
        self.root.ids.send_btn.disabled = True

    def _reset_bt_btn(self):
        self.root.ids.bt_btn.text = "Buscar panel LED"

    def _disconnect(self):
        if self.gatt:
            try:
                frame = LEDProtocol.build_disconnect_frame()
                if self.write_char:
                    self.write_char.setValue(list(frame))
                    self.gatt.writeCharacteristic(self.write_char)
                import time; time.sleep(0.1)
                self.gatt.disconnect()
                self.gatt.close()
            except Exception:
                pass
        self.connected = False
        self.write_char = None
        self.gatt = None
        self._update_ui_disconnected()
        self.log("Desconectado", "info")

    # ── Envío de datos ────────────────────────────────────
    def send_to_panel(self):
        if not self.connected or not self.write_char:
            self.log("No hay conexión Bluetooth", "err")
            return

        text = self.root.ids.msg_field.text.strip()
        if not text:
            self.log("Escribe un mensaje primero", "err")
            return

        speed  = int(self.root.ids.speed_slider.value)
        effect = self.selected_effect

        def rgb_to_hex(rgba):
            r = int(rgba[0] * 255)
            g = int(rgba[1] * 255)
            b = int(rgba[2] * 255)
            return f"#{r:02X}{g:02X}{b:02X}"

        tcol = rgb_to_hex(self.selected_text_color)
        bcol = rgb_to_hex(self.selected_bg_color)

        self.log(f'Enviando: "{text}" | Efecto={effect} Vel={speed}', "info")
        self.log(f"TextColor={tcol} BgColor={bcol}", "info")

        frame = LEDProtocol.build_text_frame(text, tcol, bcol, effect, speed)
        self.log(f"Frame ({len(frame)} bytes): " +
                 " ".join(f"{b:02x}" for b in frame[:12]) + "...", "info")

        # Partir en chunks de 20 bytes (MTU BLE estándar)
        chunk_size = 20
        self._write_queue = [
            frame[i:i+chunk_size] for i in range(0, len(frame), chunk_size)
        ]
        self._writing = False
        self.root.ids.send_btn.disabled = True
        Clock.schedule_once(lambda dt: self._flush_queue(), 0)

    def _flush_queue(self):
        if not self._write_queue:
            self.log("✓ Mensaje enviado completo", "ok")
            self.root.ids.send_btn.disabled = False
            return
        if self._writing:
            return

        chunk = self._write_queue.pop(0)
        self._writing = True

        try:
            WRITE_NO_RESP = BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE
            if self.write_char.getProperties() & WRITE_NO_RESP:
                self.write_char.setWriteType(
                    BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                )
            else:
                self.write_char.setWriteType(
                    BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
                )
            self.write_char.setValue(list(chunk))
            success = self.gatt.writeCharacteristic(self.write_char)
            if not success:
                self._writing = False
                self.log("writeCharacteristic retornó false", "err")
                self.root.ids.send_btn.disabled = False
        except Exception as e:
            self._writing = False
            self.log(f"Error chunk: {e}", "err")
            self.root.ids.send_btn.disabled = False


if __name__ == "__main__":
    LEDPanelApp().run()
