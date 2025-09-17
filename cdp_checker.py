import yaml
import json
from getpass import getpass
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from pathlib import Path
CONFIG_FILE = Path("config.yaml")
REFERENCE_FILE = Path("cdp_reference.json")
# Загружаем список устройств
file = open(CONFIG_FILE)
devices = yaml.safe_load(file)["devices"]
file.close()
# Вводим логин и пароль один раз
username = input("Введите логин: ")
password = getpass("Введите пароль: ")
# Собираем соседей по каждому свитчу
all_neighbors = {}
for device in devices:
   device["username"] = username
   device["password"] = password
   conn = ConnectHandler(**device)
   output = conn.send_command("show cdp neighbors")
   conn.disconnect()
   parsed = parse_output(platform="cisco_ios", command="show cdp neighbors", data=output)
   neighbors = []
   for item in parsed:
       neighbors.append([
           item.get("neighbor_name"),
           item.get("local_interface"),
           item.get("neighbor_interface")
       ])
   all_neighbors[device["ip"]] = neighbors
# Загружаем эталон
if REFERENCE_FILE.exists():
   file = open(REFERENCE_FILE)
   reference = json.load(file)
   file.close()
else:
   reference = {}
# Сравнение
for ip, neighbors in all_neighbors.items():
   old_neighbors = set(tuple(item) for item in reference.get(ip, []))
   current_neighbors = set(tuple(item) for item  in neighbors)
   added = current_neighbors - old_neighbors
   removed = old_neighbors - current_neighbors
   if added:
       print(f"[{ip}] Добавлены:", added)
   if removed:
       print(f"[{ip}] Удалены:", removed)
   if not added and not removed:
       print(f"[{ip}] Изменений нет")
# Сохраняем эталон
file = open(REFERENCE_FILE, "w")
json.dump(all_neighbors, file, indent=2)
file.close()
