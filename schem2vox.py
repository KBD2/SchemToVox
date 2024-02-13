import gzip
from nbt import nbt
import json
import sys
import argparse
import random
import voxhelper

GLOWING_MATERIALS = (
    "minecraft:lava",
    "minecraft:glowstone",
    "minecraft:shroomlight",
    "minecraft:beacon",
    "minecraft:fire",
    "minecraft:sea_lantern",
    "minecraft:torch",
    "minecraft:lantern"
)

parser = argparse.ArgumentParser(prog="schem2vox.py")
parser.add_argument("-c", "--compression", type=int, choices=range(0, 11))
parser.add_argument("filename", help="Schematic file to use")
args = parser.parse_args()

if len(sys.argv) == 1:
    input("You need to give this script a .schem file!")
    quit()

mapping = json.load(open("assets/mapping.json", "r"))

decompressed = gzip.open(args.filename)

nbtfile = nbt.NBTFile(buffer=decompressed)

paletteNBT = nbtfile["Palette"]

idxMap = {}

print("Mapping indices...")
for item in paletteNBT:
    idxMap[paletteNBT[item].value] = item.split("[")[0]

palette = []
paletteMap = {}

complained = {}

print("Creating vox palette...")
for name in idxMap.values():
    if name not in mapping:
        if name in complained: continue
        complained[name] = True
        print("WARNING - No mapping found for " + name + " - please report this issue!")
        continue
    if name not in paletteMap:
        colour = mapping[name]
        if not args.compression:
            palette.append(colour)
            paletteMap[name] = len(palette)
        else:
            foundSimilar = False
            for idx, compare in enumerate(palette):
                distanceSquared = (colour[0] - compare[0]) ** 2 + (colour[1] - compare[1]) ** 2 + (colour[2] - compare[2]) ** 2
                if distanceSquared < args.compression * 400:
                    foundSimilar = True
                    paletteMap[name] = idx + 1
                    palette[idx] = ((colour[0] + compare[0]) // 2, (colour[1] + compare[1]) // 2, (colour[2] + compare[2]) // 2)
                    break
            if not foundSimilar:
                palette.append(colour)
                paletteMap[name] = len(palette)
        if name == "minecraft:water":
            voxhelper.addWater(paletteMap[name])
        elif name.find("glass") > -1:
            voxhelper.addGlass(paletteMap[name])
        elif name in GLOWING_MATERIALS:
            voxhelper.addGlowing(paletteMap[name])

if len(palette) > 256:
    print("Too many block types in schematic!")
    quit()

dataRaw = nbtfile["BlockData"]

print("Parsing block data...")
data = []
idx = 0
sum = 0
numBytes = 0
for idx in range(len(dataRaw)):
    part = dataRaw[idx]
    sum += (part & 0x7f) << (7 * numBytes)
    if part & 0x80 == 0:
        data.append(sum)
        sum = 0
        numBytes = 0
    else:
        numBytes += 1
    
width = nbtfile["Width"].value
length = nbtfile["Length"].value
height = nbtfile["Height"].value

print("Translating data...")
indexes = []
for y in range(min(256, height)):
    for z in range(min(256, length)):
        for x in range(min(256, width)):
            block = data[x + z * width + y * width * length]
            name = idxMap[block]
            if name not in paletteMap:
                continue
            if name == "minecraft:air" or name == "minecraft:cave_air" or name == "minecraft:void_air":
                continue
            if name == "minecraft:grass" or name == "minecraft:short_grass" or name == "minecraft:tall_grass":
                if random.random() > 0.2:
                    continue
            idx = paletteMap[name]
            indexes.append(bytearray((min(256, width) - x - 1, z, y, idx)))
print(f"{len(indexes)} voxels in shape")

print("Constructing file...")
voxhelper.buildFile((min(256, length), min(256, width), min(256, height)), palette, indexes)