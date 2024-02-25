import gzip
import json
import sys
import argparse
import random
import math
import time

from nbt import nbt

import voxhelper

SHAPE_SIZE = 256
MAX_WIDTH = 2000
MAX_LENGTH = 2000
MAX_HEIGHT = 1000

COMPRESSION_COEFFICIENT = 400

AIR_BLOCKS = {
    "minecraft:air",
    "minecraft:cave_air",
    "minecraft:void_air"
}

ANNOYING_GRASS = {
    "minecraft:grass",
    "minecraft:short_grass",
    "minecraft:tall_grass"
}

GLOWING_MATERIALS = {
    "minecraft:lava",
    "minecraft:glowstone",
    "minecraft:shroomlight",
    "minecraft:beacon",
    "minecraft:fire",
    "minecraft:sea_lantern",
    "minecraft:torch",
    "minecraft:lantern",
    "minecraft:sea_pickle"
}

def isTransparent(name: str):
    return name == "minecraft:water" or name == "minecraft:ice" or name.find("glass") > -1

parser = argparse.ArgumentParser(prog="schem2vox.py")
parser.add_argument("-c", "--compression", type=int, choices=range(0, 11), help="Compression level to use (0-10)")
parser.add_argument("-u", "--cull", help="Cull voxels that cannot be seen", action="store_true")
parser.add_argument("-t", "--truncate", help="Discards as many colours as needed to fit into the palette, from the least-used up", action="store_true")
parser.add_argument("filename", help="Schematic file to use")
args = parser.parse_args()

if len(sys.argv) == 1:
    input("You need to give this script a .schem file!")
    quit()

mapping = json.load(open("assets/mapping.json", "r"))

decompressed = gzip.open(args.filename)

nbtfile = nbt.NBTFile(buffer=decompressed)

if "Palette" in nbtfile:
    # Version 1
    schematic = nbtfile
    paletteNBT = schematic["Palette"]
    dataRaw = schematic["BlockData"]
else:
    # Version 3
    schematic = nbtfile["Schematic"]
    blocks = schematic["Blocks"]
    paletteNBT = blocks["Palette"]
    dataRaw = blocks["Data"]


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
        if isTransparent(name) or name in GLOWING_MATERIALS:
            isSpecialMaterial = True
            
        if isSpecialMaterial or not args.compression:
            palette.append(colour)
            index = len(palette)
            paletteMap[name] = index

            if isSpecialMaterial:
                special.append(index)
        else:
            foundSimilar = False
            for idx, compare in enumerate(palette):
                if (idx + 1) in special:
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

if not args.truncate and len(palette) > 256:
    input(f"Too many block types in schematic ({len(palette)})! Increase the compression level or specify --truncate.\n")
    quit()

if len(dataRaw) < 1e6:
    print("Parsing block data...")
else:
    print("Parsing block data (may take a little bit)...")

startTime = time.time()
data = []
sum = 0
numBytes = 0
for part in dataRaw:
    sum += (part & 0x7f) << (7 * numBytes)
    if part & 0x80 == 0:
        data.append(sum)
        sum = 0
        numBytes = 0
    else:
        numBytes += 1
finishTime = time.time()
print(f"Done ({finishTime - startTime:.2f}s)")

ignore = set()
if args.truncate and len(palette) > 256:
    print("Truncating colours...")
    startTime = time.time()
    stats = {}
    for index in data:
        if index not in stats:
            stats[index] = 1
        else:
            stats[index] += 1
    statsSorted = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    newPalette = []
    newPaletteMap = {}

    for idx in range(len(statsSorted)):
        if idx > 254:
            ignore.add(statsSorted[idx][0])
        else:
            name = idxMap[statsSorted[idx][0]]
            newPalette.append(palette[paletteMap[name] - 1])
            newPaletteMap[name] = len(newPalette)
    
    palette = newPalette
    paletteMap = newPaletteMap


    finishTime = time.time()
    print(f"Done ({finishTime - startTime:.2f}s)")
elif args.truncate:
    print("No truncation needed")

print("Noting special material indices...")
for name in paletteMap:
    if name == "minecraft:water":
        voxhelper.addWater(paletteMap[name])
    elif name.find("glass") > -1 or name == "minecraft:ice":
        voxhelper.addGlass(paletteMap[name])
    elif name in GLOWING_MATERIALS:
        voxhelper.addGlowing(paletteMap[name])
    
width = schematic["Width"].value
length = schematic["Length"].value
height = schematic["Height"].value

voxhelper.setExtent(width, length)

outputWidth = min(MAX_WIDTH, width)
outputLength = min(MAX_LENGTH, length)
outputHeight = min(MAX_HEIGHT, height)

print(f"Output size: {outputWidth}x{outputLength}x{outputHeight}")

numShapesX = math.ceil(outputWidth / SHAPE_SIZE)
numShapesY = math.ceil(outputLength / SHAPE_SIZE)
numShapesZ = math.ceil(outputHeight / SHAPE_SIZE)

numShapes = numShapesX * numShapesY * numShapesZ

print("Building shapes...")
startTime = time.time()
numVoxels = 0
cullDeltas = (
    (-1, 0, 0),
    (1, 0, 0),
    (0, -1, 0),
    (0, 1, 0),
    (0, 0, -1),
    (0, 0, 1)
)
shouldCull = args.cull
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

            xOffsetWidth = outputWidth - offsetX - 1

            indexes = []
            for z in range(shapeHeight):
                for y in range(shapeLength):
                    for x in range(shapeWidth):
                        block = data[(xOffsetWidth - x) + (y + offsetY) * width + (z + offsetZ) * width * length]

                        if block in ignore: 
                            continue

                        name = idxMap[block]
                        if name not in paletteMap:
                            continue
                        if name in AIR_BLOCKS:
                            continue
                        if name in ANNOYING_GRASS:
                            if random.random() > 0.2:
                                continue
                        
                        if shouldCull:
                            cull = True
                            for delta in cullDeltas:
                                checkX = x + offsetX + delta[0]
                                checkY = y + offsetY + delta[1]
                                checkZ = z + offsetZ + delta[2]
                                if 0 <= checkX < outputWidth and 0 <= checkY < outputLength and 0 <= checkZ < outputHeight:
                                    checkBlock = data[(outputWidth - checkX - 1) + checkY * width + checkZ * width * length]
                                    checkName = idxMap[checkBlock]
                                    if checkName in AIR_BLOCKS or isTransparent(checkName):
                                        cull = False
                                        break
                                else:
                                    cull = False
                                    break
                            if cull:
                                continue

                        idx = paletteMap[name]
                        indexes.append(bytearray((x, y, z, idx)))
                        numVoxels += 1

            voxhelper.addShape(indexes, (shapeWidth, shapeLength, shapeHeight), (offsetX, offsetY, offsetZ))
finishTime = time.time()
print(f"Done ({finishTime - startTime:.2f}s)")

print(f"{numShapes} shapes, {numVoxels} voxels")

print("Building file...")
voxhelper.buildFile(palette)
print("Done!")