import gzip
import json
import sys
import argparse
import random
import math

from nbt import nbt

import voxhelper

SHAPE_SIZE = 256
MAX_WIDTH = 2000
MAX_LENGTH = 2000
MAX_HEIGHT = 1000

COMPRESSION_COEFFICIENT = 400

GLOWING_MATERIALS = (
    "minecraft:lava",
    "minecraft:glowstone",
    "minecraft:shroomlight",
    "minecraft:beacon",
    "minecraft:fire",
    "minecraft:sea_lantern",
    "minecraft:torch",
    "minecraft:lantern",
    "minecraft:sea_pickle"
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

special = []

print("Creating vox palette...")
for name in idxMap.values():
    if name not in mapping:
        if name in complained: continue
        complained[name] = True
        print("WARNING - No mapping found for " + name + " - please report this issue!")
        continue
    if name not in paletteMap:
        colour = mapping[name]

        isSpecialMaterial = False
        if name == "minecraft:water" or name.find("glass") > -1 or name == "minecraft:ice" or name in GLOWING_MATERIALS:
            isSpecialMaterial = True
            
        if isSpecialMaterial or not args.compression:
            palette.append(colour)
            paletteMap[name] = len(palette)

            if isSpecialMaterial:
                special.append(len(palette))

            if name == "minecraft:water":
                voxhelper.addWater(paletteMap[name])
            elif name.find("glass") > -1 or name == "minecraft:ice":
                voxhelper.addGlass(paletteMap[name])
            elif name in GLOWING_MATERIALS:
                voxhelper.addGlowing(paletteMap[name])
        else:
            foundSimilar = False
            for idx, compare in enumerate(palette):
                if idx in special:
                    continue
                distanceSquared = (colour[0] - compare[0]) ** 2 + (colour[1] - compare[1]) ** 2 + (colour[2] - compare[2]) ** 2
                if distanceSquared < args.compression * COMPRESSION_COEFFICIENT:
                    foundSimilar = True
                    paletteMap[name] = idx + 1
                    palette[idx] = ((colour[0] + compare[0]) // 2, (colour[1] + compare[1]) // 2, (colour[2] + compare[2]) // 2)
                    break
            if not foundSimilar:
                palette.append(colour)
                paletteMap[name] = len(palette)

if len(palette) > 256:
    print("Too many block types in schematic! Maybe increase the compression level?")
    quit()

dataRaw = nbtfile["BlockData"]

if len(dataRaw) < 1e6:
    print("Parsing block data...")
else:
    print("Parsing block data (may take a little bit)...")

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

voxhelper.setExtent(width, length)

numShapesX = math.ceil(min(MAX_WIDTH, width) / SHAPE_SIZE)
numShapesY = math.ceil(min(MAX_LENGTH, length) / SHAPE_SIZE)
numShapesZ = math.ceil(min(MAX_HEIGHT, height) / SHAPE_SIZE)

numShapes = numShapesX * numShapesY * numShapesZ

print("Building shapes...")
numVoxels = 0
for shapeZ in range(numShapesZ):
    for shapeY in range(numShapesY):
        for shapeX in range(numShapesX):
            shapeNum = shapeX + shapeY * numShapesX + shapeZ * numShapesX * numShapesY + 1
            print(f"\033[FBuilding shapes... ({shapeNum} of {numShapes})")

            offsetX = shapeX * SHAPE_SIZE
            offsetY = shapeY * SHAPE_SIZE
            offsetZ = shapeZ * SHAPE_SIZE
            shapeWidth = min(SHAPE_SIZE, width - offsetX)
            shapeLength = min(SHAPE_SIZE, length - offsetY)
            shapeHeight = min(SHAPE_SIZE, height - offsetZ)

            indexes = []
            for z in range(shapeHeight):
                for y in range(shapeLength):
                    for x in range(shapeWidth):
                        block = data[(min(MAX_WIDTH, width) - (x + offsetX) - 1) + (y + offsetY) * width + (z + offsetZ) * width * length]
                        name = idxMap[block]
                        if name not in paletteMap:
                            continue
                        if name == "minecraft:air" or name == "minecraft:cave_air" or name == "minecraft:void_air":
                            continue
                        if name == "minecraft:grass" or name == "minecraft:short_grass" or name == "minecraft:tall_grass":
                            if random.random() > 0.2:
                                continue
                        idx = paletteMap[name]
                        indexes.append(bytearray((x, y, z, idx)))
                        numVoxels += 1

            voxhelper.addShape(indexes, (shapeWidth, shapeLength, shapeHeight), (offsetX, offsetY, offsetZ))


print(f"{numShapes} shapes, {numVoxels} voxels")

print("Building file...")
voxhelper.buildFile(palette)
print("Done!")