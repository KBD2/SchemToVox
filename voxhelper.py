# All integer types are little-endian

class Extent:
    offsetX: int
    offsetY: int

    def __init__(self):
        self.offsetX = 0
        self.offsetY = 0

class BuiltShape:
    sizeChunk: bytearray
    indexesChunk: bytearray
    transformChunk: bytearray
    shapeChunk: bytearray
    transformId: int

MATERIALS: dict[int, str] = {}

SHAPES: list[BuiltShape] = []

NEXT_AVAILABLE_NODE_ID = 2 # IDs 0 and 1 are for the base transform node and the group node

EXTENT = Extent()

def setExtent(width: int, length: int):
    assert width <= 1998
    assert length <= 1998
    EXTENT.offsetX = -width // 2
    EXTENT.offsetY = -length // 2

def addWater(idx: int):
    MATERIALS[idx] = "water"

def addGlass(idx: int):
    MATERIALS[idx] = "glass"

def addGlowing(idx: int):
    MATERIALS[idx] = "glow"

def addShape(indexes: list[bytearray], size: tuple, offset: tuple = (0, 0, 0)):
    global NEXT_AVAILABLE_NODE_ID

    width = size[0]
    length = size[1]
    height = size[2]

    assert 0 < width <= 256
    assert 0 < length <= 256
    assert 0 < height <= 256

    built = BuiltShape()

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
    indexesChunk.extend(concatenatedIndices)

    calculatedOffset = (
        offset[0] + EXTENT.offsetX + width // 2,
        offset[1] + EXTENT.offsetY + length // 2,
        offset[2] + height // 2
    )

    # 4 characters gives us from -999 to 1000, we limit the extent to 1998 to ensure this
    xString = f"{calculatedOffset[0]:04d}"
    yString = f"{calculatedOffset[1]:04d}"
    zString = f"{calculatedOffset[2]:04d}"

    transformNodeId = NEXT_AVAILABLE_NODE_ID
    NEXT_AVAILABLE_NODE_ID += 1
    shapeNodeId = NEXT_AVAILABLE_NODE_ID
    NEXT_AVAILABLE_NODE_ID += 1

    shapeTransformChunk = bytearray([
        0x6e, 0x54, 0x52, 0x4e, # "nTRN"
        0x34, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (52, 0)
        transformNodeId & 0xff, (transformNodeId >> 8) & 0xff, (transformNodeId >> 16) & 0xff, (transformNodeId >> 24) & 0xff, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
        shapeNodeId & 0xff, (shapeNodeId >> 8) & 0xff, (shapeNodeId >> 16) & 0xff, (shapeNodeId >> 24) & 0xff, # Child node ID
        0xff, 0xff, 0xff, 0xff, # Reserved
        0x00, 0x00, 0x00, 0x00, # Layer ID
        0x01, 0x00, 0x00, 0x00, # Number of frames

        0x01, 0x00, 0x00, 0x00, # Transform attribute
        0x02, 0x00, 0x00, 0x00, # 2-byte key
        0x5f, 0x74, # "_t"
        0x0e, 0x00, 0x00, 0x00, # 14-byte value
        ord(xString[0]), ord(xString[1]), ord(xString[2]), ord(xString[3]),
        0x20,
        ord(yString[0]), ord(yString[1]), ord(yString[2]), ord(yString[3]),
        0x20,
        ord(zString[0]), ord(zString[1]), ord(zString[2]), ord(zString[3])
    ])

    modelId = len(SHAPES)
    shapeChunk = bytearray([
        0x6e, 0x53, 0x48, 0x50, # "nSHP"
        0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (20, 0)
        shapeNodeId & 0xff, (shapeNodeId >> 8) & 0xff, (shapeNodeId >> 16) & 0xff, (shapeNodeId >> 24) & 0xff, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty dict
        0x01, 0x00, 0x00, 0x00, # Number of models

        modelId & 0xff, (modelId >> 8) & 0xff, (modelId >> 16) & 0xff, (modelId >> 24) & 0xff, # Model ID
        0x00, 0x00, 0x00, 0x00 # Empty dict
    ])

    built.sizeChunk = sizeChunk
    built.indexesChunk = indexesChunk
    built.transformChunk = shapeTransformChunk
    built.shapeChunk = shapeChunk
    built.transformId = transformNodeId

    SHAPES.append(built)

def buildFile(palette):
    shapesChunks = bytearray()
    for shape in SHAPES:
        shapesChunks.extend(shape.sizeChunk)
        shapesChunks.extend(shape.indexesChunk)

    baseTransformChunk = bytearray([
        0x6e, 0x54, 0x52, 0x4e, # "nTRN"
        0x1c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, # Size (28, 0)
        0x00, 0x00, 0x00, 0x00, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
        0x01, 0x00, 0x00, 0x00, # Child node ID
        0xff, 0xff, 0xff, 0xff, # Reserved
        0x00, 0x00, 0x00, 0x00, # Layer ID
        0x01, 0x00, 0x00, 0x00, # Number of frames

        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
    ])

    numChildren = len(SHAPES)
    contentSize = 12 + 4 * numChildren
    groupChunk = bytearray([
        0x6e, 0x47, 0x52, 0x50, # "nGRP"
        contentSize & 0xff, (contentSize >> 8) & 0xff, (contentSize >> 16) & 0xff, (contentSize >> 24) & 0xff, # Content size
        0x00, 0x00, 0x00, 0x00, # Child content size (0)
        0x01, 0x00, 0x00, 0x00, # Node ID
        0x00, 0x00, 0x00, 0x00, # Empty attribute dict
        numChildren & 0xff, (numChildren >> 8) & 0xff, (numChildren >> 16) & 0xff, (numChildren >> 24) & 0xff, # Number of children
    ])
    for shape in SHAPES:
        id = shape.transformId
        groupChunk.extend([id & 0xff, (id >> 8) & 0xff, (id >> 16) & 0xff, (id >> 24) & 0xff])
    
    nodeChunks = bytearray()
    for shape in SHAPES:
        nodeChunks.extend(shape.transformChunk)
        nodeChunks.extend(shape.shapeChunk)

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

    paletteChunk = bytearray([
        0x52, 0x47, 0x42, 0x41, # "RGBA"
        0x0, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0 # Size (1024, 0)
    ])
    for item in palette:
        paletteChunk.extend([item[0], item[1], item[2], 255])
    for _ in range(256 - len(palette)):
        paletteChunk.extend([0, 0, 0, 255])

    mainChunkSize = len(shapesChunks) + len(baseTransformChunk) + len(groupChunk) + len(nodeChunks) + len(materialChunks) + len(paletteChunk)
    mainChunk = bytearray([
        0x4d, 0x41, 0x49, 0x4e, # "MAIN"
        0x00, 0x00, 0x00, 0x00, # Content size (0)
        mainChunkSize & 0xff, (mainChunkSize >> 8) & 0xff, (mainChunkSize >> 16) & 0xff, (mainChunkSize >> 24) & 0xff # Child content size
    ])
    mainChunk.extend(shapesChunks)
    mainChunk.extend(baseTransformChunk)
    mainChunk.extend(groupChunk)
    mainChunk.extend(nodeChunks)
    mainChunk.extend(materialChunks)
    mainChunk.extend(paletteChunk)

    with open("out.vox", "wb") as file:
        file.write(b'VOX ')
        file.write((200).to_bytes(4, 'little'))
        file.write(mainChunk)