# All integer types are little-endian

MATERIALS = {}

def addWater(idx):
    MATERIALS[idx] = "water"

def addGlass(idx):
    MATERIALS[idx] = "glass"

def addGlowing(idx):
    MATERIALS[idx] = "glow"

def buildFile(size, palette, indexes):
    length = size[0]
    width = size[1]
    height = size[2]

    paletteChunk = bytearray([
        0x52, 0x47, 0x42, 0x41, # "RGBA"
        0x0, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0 # Size (1024, 0)
    ])
    for item in palette:
        paletteChunk += bytearray([item[0], item[1], item[2], 255])
    for _ in range(256 - len(palette)):
        paletteChunk += bytearray([0, 0, 0, 255])

    sizeChunk = bytearray([
        0x53, 0x49, 0x5a, 0x45, # "SIZE"
        0x0c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (12, 0)
        width & 0xff, (width >> 8), 0x0, 0x0,
        length & 0xff, (length >> 8), 0x0, 0x0,
        height & 0xff, (height >> 8), 0x0, 0x0
    ])

    indexesSize = len(indexes)
    chunkSize = 4 * indexesSize + 4
    indexesChunk = bytearray([
        0x58, 0x59, 0x5a, 0x49, # "XYZI"
        chunkSize & 0xff, (chunkSize >> 8) & 0xff, (chunkSize >> 16) & 0xff, (chunkSize >> 24) & 0xff, # Content size
        0x0, 0x0, 0x0, 0x0, # Child content size
        indexesSize & 0xff, (indexesSize >> 8) & 0xff, (indexesSize >> 16) & 0xff, (indexesSize >> 24) & 0xff # Number of indices
    ])
    concatenatedIndices = bytearray()
    for index in indexes:
        concatenatedIndices.extend(index)
    indexesChunk += concatenatedIndices

    yDelta = f"{height // 2:03d}" # Will always be 3 characters

    baseTransformChunk = bytearray([
        0x6e, 0x54, 0x52, 0x4e, # "nTRN"
        0x2d, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (45, 0)
        0x00, 0x00, 0x00, 0x00, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
        0x01, 0x00, 0x00, 0x00, # Child node ID
        0xff, 0xff, 0xff, 0xff, # Reserved
        0x00, 0x00, 0x00, 0x00, # Layer ID
        0x01, 0x00, 0x00, 0x00, # Number of frames

        0x01, 0x00, 0x00, 0x00, # Just the transform attribute
        0x02, 0x00, 0x00, 0x00, # 2 byte key
        0x5f, 0x74, # "_t"
        0x07, 0x00, 0x00, 0x00, # 7-byte value,
        0x30, 0x20, 0x30, 0x20, ord(yDelta[0]), ord(yDelta[1]), ord(yDelta[2])  # "0 0 {yDelta}"
    ])

    groupChunk = bytearray([
        0x6e, 0x47, 0x52, 0x50, # "nGRP"
        0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (16, 0)
        0x01, 0x00, 0x00, 0x00, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
        0x01, 0x00, 0x00, 0x00, # Number of children

        0x02, 0x00, 0x00, 0x00 # Child ID
    ])

    shapeTransformChunk = bytearray([
        0x6e, 0x54, 0x52, 0x4e, # "nTRN"
        0x1c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (28, 0)
        0x02, 0x00, 0x00, 0x00, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
        0x03, 0x00, 0x00, 0x00, # Child node ID
        0xff, 0xff, 0xff, 0xff, # Reserved
        0x00, 0x00, 0x00, 0x00, # Layer ID
        0x01, 0x00, 0x00, 0x00, # Number of frames

        0x00, 0x00, 0x00, 0x00 # Empty attribute dict
    ])

    shapeChunk = bytearray([
        0x6e, 0x53, 0x48, 0x50, # "nSHP"
        0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (20, 0)
        0x03, 0x00, 0x00, 0x00, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty dict
        0x01, 0x00, 0x00, 0x00, # Number of models

        0x00, 0x00, 0x00, 0x00, # Model ID
        0x00, 0x00, 0x00, 0x00 # Empty dict
    ])

    materialChunks = bytearray()
    for id in MATERIALS:
        if MATERIALS[id] == "glass":
            materialChunk = bytearray([
                0x4d, 0x41, 0x54, 0x4c, # "MATL"
                0x2c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (44, 0)
                id, 0x00, 0x00, 0x00, # Index

                0x02, 0x00, 0x00, 0x00, # Material and transparency attributes
                0x05, 0x00, 0x00, 0x00, # 5 byte key
                0x5f, 0x74, 0x79, 0x70, 0x65, # "_type"
                0x06, 0x00, 0x00, 0x00, # 6 byte value
                0x5f, 0x67, 0x6c, 0x61, 0x73, 0x73, # "_glass"
                0x06, 0x00, 0x00, 0x00, # 6 byte key
                0x5f, 0x74, 0x72, 0x61, 0x6e, 0x73, # "_trans"
                0x03, 0x00, 0x00, 0x00, # 3 byte value
                0x30, 0x2e, 0x38 # "0.8"
            ])
        elif MATERIALS[id] == "water":
            materialChunk = bytearray([
                0x4d, 0x41, 0x54, 0x4c, # "MATL"
                0x2c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (44, 0)
                id, 0x00, 0x00, 0x00, # Index

                0x02, 0x00, 0x00, 0x00, # Material and transparency attributes
                0x05, 0x00, 0x00, 0x00, # 5 byte key
                0x5f, 0x74, 0x79, 0x70, 0x65, # "_type"
                0x06, 0x00, 0x00, 0x00, # 6 byte value
                0x5f, 0x67, 0x6c, 0x61, 0x73, 0x73, # "_glass"
                0x06, 0x00, 0x00, 0x00, # 6 byte key
                0x5f, 0x74, 0x72, 0x61, 0x6e, 0x73, # "_trans"
                0x03, 0x00, 0x00, 0x00, # 3 byte value
                0x30, 0x2e, 0x35 # "0.5"
            ])
        elif MATERIALS[id] == "glow":
            materialChunk = bytearray([
                0x4d, 0x41, 0x54, 0x4c, # "MATL"
                0x39, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (57, 0)
                id, 0x00, 0x00, 0x00, # Index

                0x03, 0x00, 0x00, 0x00, # Material, emit, and flux attributes
                0x05, 0x00, 0x00, 0x00, # 5 byte key
                0x5f, 0x74, 0x79, 0x70, 0x65, # "_type"
                0x05, 0x00, 0x00, 0x00, # 5 byte value
                0x5f, 0x65, 0x6d, 0x69, 0x74, # "_emit"
                0x05, 0x00, 0x00, 0x00, # 5 byte key
                0x5f, 0x65, 0x6d, 0x69, 0x74, # "_emit"
                0x04, 0x00, 0x00, 0x00, # 4 byte value
                0x30, 0x2e, 0x32, 0x35, # "0.25"
                0x05, 0x00, 0x00, 0x00, # 5 byte key
                0x5f, 0x66, 0x6c, 0x75, 0x78, # "_flux"
                0x01, 0x00, 0x00, 0x00, # 1 byte value
                0x31 # "1"
            ])
        materialChunks.extend(materialChunk)

    mainChunkSize = len(sizeChunk) + len(indexesChunk) + len(baseTransformChunk) + len(groupChunk) + len(shapeTransformChunk) + len(shapeChunk) + len(materialChunks) + len(paletteChunk)
    mainChunk = bytearray([
        0x4d, 0x41, 0x49, 0x4e, # "MAIN"
        0x00, 0x00, 0x00, 0x00, # Content size (0)
        mainChunkSize & 0xff, (mainChunkSize >> 8) & 0xff, (mainChunkSize >> 16) & 0xff, (mainChunkSize >> 24) & 0xff # Child content size
    ])
    mainChunk.extend(sizeChunk)
    mainChunk.extend(indexesChunk)
    mainChunk.extend(baseTransformChunk)
    mainChunk.extend(groupChunk)
    mainChunk.extend(shapeTransformChunk)
    mainChunk.extend(shapeChunk)
    mainChunk.extend(materialChunks)
    mainChunk.extend(paletteChunk)

    with open("out.vox", "wb") as file:
        file.write(b'VOX ')
        file.write((200).to_bytes(4, 'little'))
        file.write(mainChunk)