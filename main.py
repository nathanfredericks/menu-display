from time import sleep

import machine
import network
import requests
from env import MENU_API_ENDPOINT, MENU_API_KEY, PASSWORD, SSID
from picographics import DISPLAY_INKY_PACK, PicoGraphics
from pimoroni import Button
from pngdec import PNG

display = PicoGraphics(display=DISPLAY_INKY_PACK)
display.set_update_speed(1)
display.set_font("bitmap8")

button_a = Button(12)
button_b = Button(13)
button_c = Button(14)

wlan = network.WLAN(network.STA_IF)


def clear():
    display.set_pen(15)
    display.clear()


def set_init():
    clear()
    display.set_pen(0)
    lunch_width = display.measure_text("Lunch", 3)
    display.text("Lunch", (296 - 10 - lunch_width), 10, scale=3)
    dinner_width = display.measure_text("Dinner", 3)
    display.text("Dinner", (296 - 10 - dinner_width), 50, scale=3)
    display.update()


def set_not_available():
    clear()
    display.set_pen(0)
    width = display.measure_text("Menu not available", 3)
    display.text("Menu not available", (296 - width) // 2, 89, scale=3)
    png = PNG(display)
    png.open_file("x.png")
    png.decode((296 - 64) // 2, 15)
    display.update()


def set_loading():
    clear()
    display.set_pen(0)
    width = display.measure_text("Loading...", 3)
    display.text("Loading...", (296 - width) // 2, 89, scale=3)
    png = PNG(display)
    png.open_file("sandglass.png")
    png.decode((296 - 64) // 2, 15)
    display.update()


def set_menu(period, items, date):
    clear()
    display.set_pen(0)
    display.text(period, 30, 7, scale=2)
    display.text("\n".join(f"* {item}" for item in items), 10, 30, 296 - 10, 2)
    display.text(date, 10, 128 - 20, 296 - 10, 2)
    png = PNG(display)
    png.open_file("fork-knife.png")
    png.decode(10, 5)
    display.update()


def connect():
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    attempts = 0
    while not wlan.isconnected() and attempts < 15:
        print("Waiting for connection...")
        sleep(1)
        attempts += 1

    if wlan.isconnected():
        print(f"Connected to {wlan.ifconfig()[0]}")
    else:
        print("Failed to connect after 15 attempts.")


def disconnect():
    wlan.active(False)
    wlan.disconnect()


def fetch_menu():
    try:
        response = requests.get(
            MENU_API_ENDPOINT,
            headers={"X-API-Key": MENU_API_KEY},
        )
        if response.status_code != 200:
            print("Menu not available")
            return None

        json_data = response.json()
        if not json_data["menu"]["lunch"] or not json_data["menu"]["dinner"]:
            print("Menu not available")
            return None

        return json_data

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def update_menu(period):
    set_loading()
    connect()
    print("Fetching menu...")

    json_data = fetch_menu()
    if json_data is None:
        set_not_available()
        return

    print("Fetched menu")

    if period == "lunch":
        set_menu("Lunch", json_data["menu"]["lunch"], json_data["date"])
    elif period == "dinner":
        set_menu("Dinner", json_data["menu"]["dinner"], json_data["date"])


set_init()

while True:
    if button_a.read():
        update_menu("lunch")

    if button_b.read():
        update_menu("dinner")

    if button_c.read():
        print("Resetting...")
        machine.reset()
