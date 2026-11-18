import network
import time

def conectar(ssid, senha, timeout=20):
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if wifi.isconnected():
        return wifi
    wifi.disconnect()
    wifi.connect(ssid, senha)
    inicio = time.ticks_ms()
    while not wifi.isconnected():
        if time.ticks_diff(time.ticks_ms(), inicio) >= timeout * 1000:
            raise OSError("Tempo de conexao Wi-Fi esgotado")
        time.sleep_ms(250)
    return wifi
