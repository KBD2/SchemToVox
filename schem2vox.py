import gzip
from nbt import nbt
import json
import sys
import argparse

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

for item in paletteNBT:
    idxMap[paletteNBT[item].value] = item.split("[")[0]

palette = []
paletteMap = {}

for name in idxMap.values():
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

if len(palette) > 256:
    print("Too many block types in schematic!")
    quit()

dataRaw = nbtfile["BlockData"]

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

paletteChunk = bytes("RGBA", 'utf-8')
paletteChunk += (1024).to_bytes(4, 'little')
paletteChunk += (0).to_bytes(4, 'little')
for item in palette:
    paletteChunk += bytearray([item[0], item[1], item[2], 255])
for _ in range(256 - len(palette)):
    paletteChunk += bytearray([0, 0, 0, 255])

sizeChunk = bytes("SIZE", 'utf-8')
sizeChunk += (12).to_bytes(4, 'little')
sizeChunk += (0).to_bytes(4, 'little')
sizeChunk += min(256, width).to_bytes(4, "little")
sizeChunk += min(256, length).to_bytes(4, "little")
sizeChunk += min(256, height).to_bytes(4, "little")

indexes = []
for y in range(min(256, height)):
    print("Processing Y layer " + str(y))
    for z in range(min(256, length)):
        for x in range(min(256, width)):
            block = data[x + z * width + y * width * length]
            name = idxMap[block]
            if name == "minecraft:air" or name == "minecraft:cave_air" or name == "minecraft:void_air":
                continue
            idx = paletteMap[name]
            indexes.append(bytearray((min(256, width) - x - 1, z, y, idx)))
print(f"{len(indexes)} voxels in shape")

indexesChunk = bytes("XYZI", 'utf-8')
indexesChunk += (4 * len(indexes) + 4).to_bytes(4, 'little')
indexesChunk += (0).to_bytes(4, 'little')
indexesChunk += len(indexes).to_bytes(4, 'little')
concatenatedIndices = bytearray()
for index in indexes:
    concatenatedIndices.extend(index)
indexesChunk += concatenatedIndices

transformString = f"0 0 {height // 2}"

sceneGraphChunks = bytes("nTRN", 'utf-8')
transformChunk = [
    38 + len(transformString), 0,
    0,
    0, 1, -1, 0, 1,
    1
]
for value in transformChunk:
    if value < 0:
        sceneGraphChunks += value.to_bytes(4, 'little', signed=True)
    else:
        sceneGraphChunks += value.to_bytes(4, 'little')
sceneGraphChunks += (2).to_bytes(4, 'little') + bytes("_t", 'utf-8') + len(transformString).to_bytes(4, 'little') + bytes(transformString, 'utf-8')
sceneGraphChunks += bytes("nGRP", 'utf-8')
groupChunk = [
    16, 0,
    1,
    0, 1, 2
]
for value in groupChunk:
    sceneGraphChunks += value.to_bytes(4, 'little')
sceneGraphChunks += bytes("nTRN", 'utf-8')
transformChunk = [
    28, 0,
    2,
    0, 3, -1, 0, 1, 0
]
for value in transformChunk:
    if value < 0:
        sceneGraphChunks += value.to_bytes(4, 'little', signed=True)
    else:
        sceneGraphChunks += value.to_bytes(4, 'little')
sceneGraphChunks += bytes("nSHP", 'utf-8')
shapeChunk = [
    20, 0,
    3,
    0, 1, 0, 0
]
for value in shapeChunk:
    sceneGraphChunks += value.to_bytes(4, 'little')

mainChunk = bytes("MAIN", 'utf-8') + (0).to_bytes(4, 'little')
mainChunk += (len(sceneGraphChunks) + len(sizeChunk) + len(indexesChunk) + len(paletteChunk)).to_bytes(4, 'little')
mainChunk += sceneGraphChunks
mainChunk += sizeChunk
mainChunk += indexesChunk
mainChunk += paletteChunk

with open("out.vox", "wb") as file:
    file.write(b'VOX ')
    file.write((200).to_bytes(4, 'little'))
    file.write(mainChunk)