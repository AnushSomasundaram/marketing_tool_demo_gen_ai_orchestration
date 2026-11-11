

import pyautogui

x = int(input("Enter X position: "))

y = int(input("Enter Y position: "))

pyautogui.moveTo(x, y, duration=0.5)

print(f"Mouse moved to X={x}, Y={y}")

