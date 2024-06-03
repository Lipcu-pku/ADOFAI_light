import json

import os

import shutil

from tkinter import Tk

from tkinter.filedialog import askopenfilename


def ms_cal(beats, bpm):
    if bpm == 0:
        return 0
    else:
        return 60 / bpm * beats * 1000


def ang_cal(bpm, ms):
    return ms * bpm / 1000 * 3


class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'


tile_action_num = 0
fake_tile_num = 0
true_tile_num = 0

root = Tk()
root.iconbitmap()
root.withdraw()

path = askopenfilename(filetypes=[("ADOFAI files", "*.adofai"), ("ADOFAI files", "*.ADOFAI")])

cor = {
    ', }': '}',
    ',  }': '}',
    ']\n\t"decorations"': '],\n\t"decorations"',
    '],\n}': ']\n}',
    ',,': ',',
    '}\n\t\t{': '},\n\t\t{',
    '},\n\t]': '}\n\t]',
    '\n\\n': '\\n'
}
# 转化.adofai语法错误，但是肯定不全

with open(path, encoding="utf-8-sig") as f:
    info = f.read()
    for i in cor:
        info = info.replace(i, cor[i])
    content = json.loads(info)

pathDatatrans = {'R': 0,
                 'p': 15,
                 'J': 30,
                 'E': 45,
                 'T': 60,
                 'o': 75,
                 'U': 90,
                 'q': 105,
                 'G': 120,
                 'Q': 135,
                 'H': 150,
                 'W': 165,
                 'L': 180,
                 'x': 195,
                 'N': 210,
                 'Z': 235,
                 'F': 240,
                 'V': 255,
                 'D': 270,
                 'Y': 285,
                 'B': 300,
                 'C': 315,
                 'M': 330,
                 'A': 345,
                 '5': 555,
                 '6': 666,
                 '7': 777,
                 '8': 888,
                 '!': 999
                 }

if 'pathData' in content:
    # 把旧版的pathData转化为新版的angleData
    pathData = list(content['pathData'])
    angleData = [pathDatatrans[i] for i in pathData]
    for i, angle in enumerate(angleData):
        lastangle = angleData[i - 1] if i >= 1 else 0
        if angle == 555: angleData[i] = (lastangle + 72) % 360
        if angle == 666: angleData[i] = (lastangle - 72) % 360
        if angle == 777: angleData[i] = (lastangle + 360 / 7) % 360
        if angle == 888: angleData[i] = (lastangle - 360 / 7) % 360
    del content['pathData']
    content['angleData'] = angleData
else:
    angleData = content['angleData']

if 'decorations' not in content:
    content['decorations'] = []

size = int(input("光的大小 (正常为4): "))

depth = int(input("光的深度 (正常为-1): "))
repeat = int(input("光的叠加次数 (正常为16且越多越卡): "))
color = input("光的颜色 (正常为ffffff): ")
opacity = input("光的不透明度 (正常為100): ")
maskingType = "None"
maskingFrontDepth = -1
maskingBackDepth = -1

if input("全轨道范围? (True或False): ") == "True":
    Tile_FullRange = True
    Start_Tile = 0
    End_Tile = 0
    Tile_number = len(angleData)
else:
    Tile_FullRange = False
    Start_Tile = int(input("开始轨道数 (例如3): "))
    End_Tile = int(input("结束轨道数 (例如10): "))
    Tile_number = End_Tile - Start_Tile + 1

if input("范围名称? (False以取消): ") == "False":
    rangename = ""
else:
    rangename = f'_{input("范围名称 (例如Range1): ")}'

redo_ms = 0

total_floor = len(angleData)

tile_bpm = content["settings"]["bpm"]

tile_bpm_list = [tile_bpm] + ["None"] * total_floor

for action in content["actions"]:
    if action["eventType"] == "SetSpeed":
        if action["speedType"] == "Bpm":
            tile_bpm = action["beatsPerMinute"]
            tile_bpm_list[action["floor"]] = tile_bpm
        else:
            tile_bpm *= action["bpmMultiplier"]
            tile_bpm_list[action["floor"]] = tile_bpm

for i in range(total_floor + 1):
    if tile_bpm_list[i] == "None":
        tile_bpm_list[i] = tile_bpm_list[i - 1]

tile_size = 100
tile_opacity = 100

tile_size_list = [tile_size] + ["None"] * total_floor
tile_opacity_list = [tile_opacity] + ["None"] * total_floor

for action in content["actions"]:
    if action["eventType"] == "PositionTrack":
        if "justThisTile" in action:
            if action["justThisTile"] == "true":
                tile_size_list[action["floor"] + 1] = tile_size
                tile_opacity_list[action["floor"] + 1] = tile_opacity
        if "scale" in action:
            tile_size = action["scale"]
            tile_size_list[action["floor"]] = tile_size
        if "opacity" in action:
            tile_opacity = action["opacity"]
            tile_opacity_list[action["floor"]] = tile_opacity

for i in range(total_floor + 1):
    if tile_size_list[i] == "None":
        tile_size_list[i] = tile_size_list[i - 1]
    if tile_opacity_list[i] == "None":
        tile_opacity_list[i] = tile_opacity_list[i - 1]

if content["settings"]["trackAnimation"] == "None":
    light_show = [False] + ["None"] * total_floor
else:
    light_show = [True] + ["None"] * total_floor
light_show_ms = [ms_cal(content["settings"]["beatsAhead"], tile_bpm_list[0])] + ["None"] * total_floor

if content["settings"]["trackDisappearAnimation"] == "None":
    light_hide = [False] + ["None"] * total_floor
else:
    light_hide = [True] + ["None"] * total_floor
light_hide_ms = [ms_cal(content["settings"]["beatsBehind"], tile_bpm_list[0])] + ["None"] * total_floor

for action in content["actions"]:
    if action["eventType"] == "AnimateTrack":
        if "trackAnimation" in action:
            if action["trackAnimation"] == "None":
                light_show[action["floor"]] = False
            else:
                light_show[action["floor"]] = True
                light_show_ms[action["floor"]] = ms_cal(action["beatsAhead"], tile_bpm_list[action["floor"]])
        if "trackDisappearAnimation" in action:
            if action["trackDisappearAnimation"] == "None":
                light_hide[action["floor"]] = False
            else:
                light_hide[action["floor"]] = True
                light_hide_ms[action["floor"]] = ms_cal(action["beatsBehind"], tile_bpm_list[action["floor"]])

for i in range(total_floor + 1):
    if light_show[i] == "None":
        light_show[i] = light_show[i - 1]
    if light_show_ms[i] == "None":
        light_show_ms[i] = light_show_ms[i - 1]
    if light_hide[i] == "None":
        light_hide[i] = light_hide[i - 1]
    if light_hide_ms[i] == "None":
        light_hide_ms[i] = light_hide_ms[i - 1]

for action in content["actions"]:
    if action["eventType"] == "MoveTrack":
        start_tile = action["startTile"]
        end_tile = action["endTile"]
        if start_tile[1] == "ThisTile":
            start_tile = start_tile[0] + action["floor"]
        elif start_tile[1] == "Start":
            start_tile = start_tile[0]
        else:
            start_tile = total_floor + start_tile[0]
        if end_tile[1] == "ThisTile":
            end_tile = end_tile[0] + action["floor"]
        elif end_tile[1] == "Start":
            end_tile = end_tile[0]
        else:
            end_tile = total_floor + end_tile[0]
        final_tag = ""
        if "gapLength" in action:
            for tag in range(start_tile, end_tile, int(action["gapLength"]) + 1):
                final_tag = final_tag + "Light_of_Floor_" + str(tag) + " "
            final_tag = final_tag + "Light_of_Floor_" + str(end_tile)
        else:
            for tag in range(start_tile, end_tile):
                final_tag = final_tag + "Light_of_Floor_" + str(tag) + " "
            final_tag = final_tag + "Light_of_Floor_" + str(end_tile)

        # final_tag為所有標籤

        new_action = {
            "floor": action["floor"],
            "eventType": "MoveDecorations",
            "duration": action["duration"],
            "tag": f"{final_tag}",
        }

        if "positionOffset" in action:
            new_action = new_action | {
                "positionOffset": [action["positionOffset"][0],
                                   action["positionOffset"][1]],
            }
        if "rotationOffset" in action:
            new_action = new_action | {
                "rotationOffset": action["rotationOffset"],
            }
        if "opacity" in action:
            new_action = new_action | {
                "opacity": action["opacity"],
            }
        if "parallaxOffset" in action:
            new_action = new_action | {
                "parallaxOffset": [None, None],
            }
        new_action = new_action | {
            "angleOffset": action["angleOffset"],
            "ease": f"{action["ease"]}",
            "eventTag": f"{action["eventTag"]}",
        }
        content["actions"].append(new_action)
        tile_action_num += 1

        if "scale" in action:
            for size_number in range(repeat):
                if "gapLength" in action:
                    final_tag = ""
                    for tag in range(start_tile, end_tile, int(action["gapLength"]) + 1):
                        final_tag = final_tag + "Light_of_Floor_" + str(tag) + "_size_" + str(size_number) + " "
                    final_tag = final_tag + "Light_of_Floor_" + str(end_tile) + "_size_" + str(size_number)
                else:
                    final_tag = ""
                    for tag in range(start_tile, end_tile):
                        final_tag = final_tag + "Light_of_Floor_" + str(tag) + "_size_" + str(size_number) + " "
                    final_tag = final_tag + "Light_of_Floor_" + str(end_tile) + "_size_" + str(size_number)

                if isinstance(action["scale"], list):
                    new_action = {
                        "floor": action["floor"],
                        "eventType": "MoveDecorations",
                        "duration": action["duration"],
                        "scale": [(100 + size_number * size) * action["scale"][0] / 100,
                                  (100 + size_number * size) * action["scale"][1] / 100],
                        "tag": f"{final_tag}",
                    }
                else:
                    new_action = {
                        "floor": action["floor"],
                        "eventType": "MoveDecorations",
                        "duration": action["duration"],
                        "scale": [(100 + size_number * size) * action["scale"] / 100,
                                  (100 + size_number * size) * action["scale"] / 100],
                        "tag": f"{final_tag}",
                    }

                content["actions"].append(new_action)
                tile_action_num += 1

old_color_list = ["32", "1e", "14", "0f", "0a", "0a", "05", "05", "05", "05", "05", "05", "05", "05", "05", "05", "05"]
new_color_list = ["70", "58", "46", "3d", "32", "32", "24", "24", "24", "24", "24", "24", "24", "24", "24", "24", "24"]

List = [0] + angleData
Light_of_Floor_Angle = []
Light_of_Floor_TurnAngle = []

List_len = len(List)
for i in range(List_len - 1):
    if List[i] == 999:
        Light_of_Floor_Angle.append((List[i - 1] - List[i + 1]) % 360)
        Light_of_Floor_TurnAngle.append(List[i - 1] - 180)
    elif List[i + 1] == 999:
        Light_of_Floor_Angle.append(999)
        Light_of_Floor_TurnAngle.append(List[i])
    else:
        Light_of_Floor_Angle.append((180 - List[i + 1] + List[i]) % 360)
        Light_of_Floor_TurnAngle.append(List[i])

Light_of_Floor_Angle.append(180)
if List[-1] == 999:
    Light_of_Floor_TurnAngle.append(List[-2])
else:
    Light_of_Floor_TurnAngle.append(List[-1])

for floor in range(List_len):
    if Tile_FullRange is True or Start_Tile <= floor <= End_Tile:
        DoTile = True
    else:
        DoTile = False

    legacy = False

    if DoTile is True:
        for floor_time in range(1, repeat + 1):

            legacy = Light_of_Floor_Angle[floor] % 15 == 0 or Light_of_Floor_Angle[floor] == 999

            if floor_time <= 16:
                if legacy is True:
                    light_color = f'{color}{old_color_list[floor_time]}'
                else:
                    light_color = f'{color}{new_color_list[floor_time]}'
            else:
                if legacy is True:
                    light_color = f'{color}05'
                else:
                    light_color = f'{color}24'

            light_total_tag = f"Light_of_Floor{rangename} "
            light_total_tag += f"Light_of_Floor_{floor} "
            light_total_tag += f"Light_of_Floor_{floor}_size_{floor_time}"

            if legacy:
                decoration = {
                    "floor": floor,
                    "eventType": "AddDecoration",
                    "decorationImage": f"Light_of_Floor_white/{Light_of_Floor_Angle[floor]}.png",
                    "position": [0, 0],
                    "relativeTo": "Tile",
                    "pivotOffset": [0, 0],
                    "rotation": Light_of_Floor_TurnAngle[floor],
                    "lockRotation": False,
                    "scale": [(100 + floor_time * size) * tile_size_list[floor] / 100,
                              (100 + floor_time * size) * tile_size_list[floor] / 100],
                    "lockScale": False,
                    "tile": [1, 1],
                    "color": light_color,
                    "opacity": 0,
                    "depth": f'{depth}',
                    "parallax": [f'{(floor_time - 1) * -2}', f'{(floor_time - 1) * -2}'],
                    "parallaxOffset": [0, 0],
                    "tag": f"{light_total_tag}",
                    "imageSmoothing": True,
                    "blendMode": "None",
                    "maskingType": f'{maskingType}',
                    "useMaskingDepth": False,
                    "maskingFrontDepth": f'{maskingFrontDepth}',
                    "maskingBackDepth": f'{maskingBackDepth}',
                    "hitbox": "None",
                    "hitboxEventTag": "",
                    "failHitboxType": "Box",
                    "failHitboxScale": [100, 100],
                    "failHitboxOffset": [0, 0],
                    "failHitboxRotation": 0
                }
            else:
                if Light_of_Floor_Angle[floor] == 999:
                    TrackType = "Midspin"
                else:
                    TrackType = "Normal"
                decoration = {
                    "floor": floor,
                    "eventType": "AddObject",
                    "objectType": "Floor",
                    "planetColorType": "DefaultRed",
                    "planetColor": "ff0000",
                    "planetTailColor": "ff0000",
                    "trackType": f"{TrackType}",
                    "trackAngle": Light_of_Floor_Angle[floor],
                    "trackColorType": "Single",
                    "trackColor": f"{light_color}",
                    "secondaryTrackColor": f"{light_color}",
                    "trackColorAnimDuration": 2,
                    "trackOpacity": 0,
                    "trackStyle": "Minimal",
                    "trackIcon": "None",
                    "trackIconAngle": 0,
                    "trackRedSwirl": False,
                    "trackGraySetSpeedIcon": False,
                    "trackSetSpeedIconBpm": 100,
                    "trackGlowEnabled": False,
                    "trackGlowColor": "ffffff",
                    "position": [0, 0],
                    "relativeTo": "Tile",
                    "pivotOffset": [0, 0],
                    "rotation": Light_of_Floor_TurnAngle[floor],
                    "lockRotation": False,
                    "scale": [100 + floor_time * size * tile_size_list[floor] / 100,
                              100 + floor_time * size * tile_size_list[floor] / 100],
                    "lockScale": False,
                    "depth": depth,
                    "parallax": [f'{(floor_time - 1) * -2}', f'{(floor_time - 1) * -2}'],
                    "parallaxOffset": [0, 0],
                    "tag": f"{light_total_tag}",
                }
            content["decorations"].append(decoration)
            if legacy:
                fake_tile_num += 1
            else:
                true_tile_num += 1

    if light_hide[floor] is True:
        if floor != 0:
            actions = {
                "floor": floor,
                "eventType": "MoveDecorations",
                "duration": 0,
                "tag": f"Light_of_Floor_{floor - 1}",
                "visible": False,
                "scale": [0, 0],
                "opacity": 0,
                "parallaxOffset": [0, 0],
                "angleOffset": f"{ang_cal(tile_bpm_list[floor], light_hide_ms[floor])}",
                "ease": "Linear",
                "eventTag": "",
            }
            content["actions"].append(actions)
            tile_action_num += 1

    if light_show[floor] is True:
        actions = {
            "floor": floor,
            "eventType": "MoveDecorations",
            "duration": 0,
            "tag": f"Light_of_Floor_{floor}",
            "opacity": f'{opacity}',
            "parallaxOffset": [0, 0],
            "angleOffset": f"{ang_cal(tile_bpm_list[floor], light_show_ms[floor]) * -1}",
            "ease": "Linear",
            "eventTag": "",
        }
        content["actions"].append(actions)
        tile_action_num += 1
    else:
        actions = {
            "floor": 0,
            "eventType": "MoveDecorations",
            "duration": 0,
            "tag": f"Light_of_Floor_{floor}",
            "opacity": f'{float(opacity) * float(tile_opacity_list[floor]) / 100}',
            "parallaxOffset": [0, 0],
            "angleOffset": 0,
            "ease": "Linear",
            "eventTag": "",
        }
        content["actions"].append(actions)
        tile_action_num += 1

print("")

if tile_action_num <= 1000:
    print(f"新增了 {Colors.GREEN}{tile_action_num}{Colors.RESET} 个移动装饰")
elif tile_action_num <= 5000:
    print(f"新增了 {Colors.YELLOW}{tile_action_num}{Colors.RESET} 个移动装饰")
else:
    print(f"新增了 {Colors.RED}{tile_action_num}{Colors.RESET} 个移动装饰")

if fake_tile_num <= 16000:
    print(f"新增了 {Colors.GREEN}{fake_tile_num}{Colors.RESET} 个假轨道装饰")
elif fake_tile_num <= 80000:
    print(f"新增了 {Colors.YELLOW}{fake_tile_num}{Colors.RESET} 个假轨道装饰")
else:
    print(f"新增了 {Colors.RED}{fake_tile_num}{Colors.RESET} 个假轨道装饰")

if true_tile_num <= 300:
    print(f"新增了 {Colors.GREEN}{true_tile_num}{Colors.RESET} 个真轨道装饰")
elif true_tile_num <= 1000:
    print(f"新增了 {Colors.YELLOW}{true_tile_num}{Colors.RESET} 个真轨道装饰")
else:
    print(f"新增了 {Colors.RED}{true_tile_num}{Colors.RESET} 个真轨道装饰")

text_adofai = "_light"

new_path = path.rstrip('.adofai') + f"{text_adofai}.adofai"

print(json.dumps(content, indent=4), file=open(new_path, 'w', encoding='utf-8'))

fpath, fname = os.path.split(path)

docpath = os.path.join(fpath, 'Light_of_Floor_white')

if os.path.exists(docpath):
    pass
else:
    shutil.copytree('./Light_of_Floor_white', docpath)

print(f"档案储存在 {new_path}")
