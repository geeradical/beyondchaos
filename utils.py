from os import path
import random

ENEMY_TABLE = path.join("tables", "enemycodes.txt")
ITEM_TABLE = path.join("tables", "itemcodes.txt")
SPELL_TABLE = path.join("tables", "spellcodes.txt")
SPELLBANS_TABLE = path.join("tables", "spellbans.txt")
ESPER_TABLE = path.join("tables", "espercodes.txt")
CHEST_TABLE = path.join("tables", "chestcodes.txt")
COMMAND_TABLE = path.join("tables", "commandcodes.txt")
CHAR_TABLE = path.join("tables", "charcodes.txt")
TEXT_TABLE = path.join("tables", "text.txt")
SHORT_TEXT_TABLE = path.join("tables", "shorttext.txt")
ENEMY_NAMES_TABLE = path.join("tables", "enemynames.txt")
MODIFIERS_TABLE = path.join("tables", "moves.txt")
MOVES_TABLE = path.join("tables", "moves.txt")
LOCATION_TABLE = path.join("tables", "locationformations.txt")
LOCATION_PALETTE_TABLE = path.join("tables", "locationpaletteswaps.txt")
BATTLE_BG_PALETTE_TABLE = path.join("tables", "battlebgpalettes.txt")
CHARACTER_PALETTE_TABLE = path.join("tables", "charpaloptions.txt")
EVENT_PALETTE_TABLE = path.join("tables", "eventpalettes.txt")
MALE_NAMES_TABLE = path.join("tables", "malenames.txt")
FEMALE_NAMES_TABLE = path.join("tables", "femalenames.txt")
MAP_NAMES_TABLE = path.join("tables", "mapnames.txt")
USED_LOCATIONS_TABLE = path.join("tables", "usedlocs.txt")
UNUSED_LOCATIONS_TABLE = path.join("tables", "unusedlocs.txt")
TOWER_LOCATIONS_TABLE = path.join("tables", "finaldungeonmaps.txt")
TOWER_CHECKPOINTS_TABLE = path.join("tables", "finaldungeoncheckpoints.txt")
MAP_BATTLE_BG_TABLE = path.join("tables", "mapbattlebgs.txt")
ENTRANCE_REACHABILITY_TABLE = path.join("tables", "reachability.txt")
FINAL_BOSS_AI_TABLE = path.join("tables", "finalai.txt")
TREASURE_ROOMS_TABLE = path.join("tables", "treasurerooms.txt")


class Substitution(object):
    location = None

    @property
    def size(self):
        return len(self.bytestring)

    def set_location(self, location):
        self.location = location

    def write(self, filename):
        f = open(filename, 'r+b')
        bs = "".join(map(chr, self.bytestring))
        f.seek(self.location)
        f.write(bs)
        f.close()


texttable = {}
f = open(TEXT_TABLE)
for line in f:
    line = line.strip()
    char, value = tuple(line.split())
    texttable[char] = value
texttable[' '] = 'FE'
f.close()


def name_to_bytes(name, length):
    name = map(lambda c: hex2int(texttable[c]), name)
    assert len(name) <= length
    while len(name) < length:
        name.append(0xFF)
    return name


shorttexttable = {}
f = open(SHORT_TEXT_TABLE)
for line in f:
    line = line.strip()
    char, value = tuple(line.split())
    shorttexttable[char] = value
shorttexttable[' '] = 'FF'
f.close()


def hex2int(hexstr):
    return int(hexstr, 16)


battlebg_palettes = {}
f = open(BATTLE_BG_PALETTE_TABLE)
for line in f:
    line = line.strip()
    bg, palette = tuple(line.split())
    bg, palette = hex2int(bg), hex2int(palette)
    battlebg_palettes[bg] = palette
f.close()


def int2bytes(value, length=2, reverse=True):
    # reverse=True means high-order byte first
    bs = []
    while value:
        bs.append(value & 255)
        value = value >> 8

    while len(bs) < length:
        bs.append(0)

    if not reverse:
        bs = reversed(bs)

    return bs[:length]


def read_multi(f, length=2, reverse=True):
    vals = map(ord, f.read(length))
    if reverse:
        vals = list(reversed(vals))
    value = 0
    for val in vals:
        value = value << 8
        value = value | val
    return value


def write_multi(f, value, length=2, reverse=True):
    vals = []
    while value:
        vals.append(value & 0xFF)
        value = value >> 8
    if len(vals) > length:
        raise Exception("Value length mismatch.")

    while len(vals) < length:
        vals.append(0x00)

    if not reverse:
        vals = reversed(vals)

    f.write(''.join(map(chr, vals)))


utilrandom = random.Random()
utran = utilrandom
random = utilrandom


def mutate_index(index, length, continuation=None,
                 basic_range=None, extended_range=None):
    if length == 0:
        return None

    highest = length - 1
    continuation = continuation or [True, False]
    basic_range = basic_range or (-3, 3)
    extended_range = extended_range or (-1, 1)

    index += utran.randint(*basic_range)
    index = max(0, min(index, highest))
    while utran.choice(continuation):
        index += utran.randint(*extended_range)
        index = max(0, min(index, highest))

    return index


def generate_swapfunc(swapcode=None):
    if swapcode is None:
        swapcode = utran.randint(0, 7)

    f = lambda w: w
    g = lambda w: w
    h = lambda w: w
    if swapcode & 1:
        f = lambda (x, y, z): (y, x, z)
    if swapcode & 2:
        g = lambda (x, y, z): (z, y, x)
    if swapcode & 4:
        h = lambda (x, y, z): (x, z, y)
    swapfunc = lambda w: f(g(h(w)))

    return swapfunc


def shift_middle(triple, degree, ungray=False):
    low, medium, high = tuple(sorted(triple))
    triple = list(triple)
    mediumdex = triple.index(medium)
    if ungray:
        lowdex, highdex = triple.index(low), triple.index(high)
        while utran.choice([True, False]):
            low -= 1
            high += 1

        low = max(0, low)
        high = min(31, high)

        triple[lowdex] = low
        triple[highdex] = high

    if degree < 0:
        value = low
    else:
        value = high
    degree = abs(degree)
    a = (1 - (degree/90.0)) * medium
    b = (degree/90.0) * value
    medium = a + b
    medium = int(round(medium))
    triple[mediumdex] = medium
    return tuple(triple)


def get_palette_transformer(changing=True, always=False, middle=True):
    degree = utran.randint(-75, 75)

    if changing:
        lumas = 32
        swapfuncs, flag = [], 6
        thirds = random.choice([True, False])
        while True:
            indexes = [0, 31]
            if not thirds:
                half = lumas / 2
                midpoint = utran.randint(0, half) + utran.randint(0, half)
                indexes.append(midpoint)
            else:
                third = lumas / 3
                thirdpoint = utran.randint(0, third) + utran.randint(0, third)
                indexes.append(thirdpoint)
                thirdpoint = (thirdpoint + utran.randint(0, third) +
                              utran.randint(0, third))
                indexes.append(thirdpoint)
            indexes = sorted(indexes)
            for (a, b) in zip(indexes, indexes[1:]):
                if b - a < 6 or b > 31:
                    break
            else:
                break

        swapfuncs = []
        for i in xrange(32):
            if i in indexes:
                swapcode = random.randint(1, 7) if always is True else None
                swapfunc = generate_swapfunc(swapcode=swapcode)
            swapfuncs.append(swapfunc)
    else:
        swapcode = random.randint(1, 7) if always is True else None
        swapfunc = generate_swapfunc(swapcode=swapcode)
        swapfuncs = [swapfunc for _ in xrange(32)]

    assert len(swapfuncs) == 32

    def color_transformer(red, green, blue):
        a = red >= green
        b = red >= blue
        c = green >= blue
        index = (a << 2) | (b << 1) | c
        luma = (red + green + blue) / 3
        index = luma
        swapfunc = swapfuncs[index]
        red, green, blue = swapfunc((red, green, blue))
        if middle:
            red, green, blue = shift_middle((red, green, blue), degree)
        return (red, green, blue)

    def palette_transformer(raw_palette):
        transformed = []
        for color in raw_palette:
            blue = (color & 0x7c00) >> 10
            green = (color & 0x03e0) >> 5
            red = color & 0x001f
            red, green, blue = color_transformer(red, green, blue)
            assert min(red, green, blue) >= 0x00
            assert max(red, green, blue) <= 0x1F
            color = 0 | red | (green << 5) | (blue << 10)
            assert color <= 0x7FFF
            transformed.append(color)
        return transformed

    return palette_transformer


def mutate_palette_dict(palette_dict):
    colorsets = {}
    for n, (red, green, blue) in palette_dict.items():
        key = (red >= green, red >= blue, green >= blue)
        if key not in colorsets:
            colorsets[key] = []
        colorsets[key].append(n)

    pastswap = []
    for key in colorsets:
        degree = utran.randint(-75, 75)

        while True:
            swapcode = utran.randint(0, 7)
            if swapcode not in pastswap or utran.randint(1, 10) == 10:
                break

        pastswap.append(swapcode)
        swapfunc = generate_swapfunc(swapcode)

        for n in colorsets[key]:
            red, green, blue = palette_dict[n]
            red, green, blue = shift_middle((red, green, blue), degree)
            low, medium, high = tuple(sorted([red, green, blue]))

            assert low <= medium <= high
            palette_dict[n] = swapfunc((low, medium, high))

    return palette_dict


def decompress(bytestring, simple=False, complicated=False, debug=False):
    result = ""
    buff = [chr(0)] * 2048
    buffaddr = 0x7DE
    while bytestring:
        flags, bytestring = ord(bytestring[0]), bytestring[1:]
        for i in xrange(8):
            if not bytestring:
                break

            if flags & (1 << i):
                byte, bytestring = bytestring[0], bytestring[1:]
                result += byte
                buff[buffaddr] = byte
                buffaddr += 1
                if buffaddr == 0x800:
                    buffaddr = 0
                if debug:
                    print "%x" % ord(byte),
            else:
                low, high, bytestring = (
                    ord(bytestring[0]), ord(bytestring[1]), bytestring[2:])
                seekaddr = low | ((high & 0x07) << 8)
                length = ((high & 0xF8) >> 3) + 3
                if simple:
                    copied = "".join([buff[seekaddr]] * length)
                elif complicated:
                    cycle = buffaddr - seekaddr
                    if cycle < 0:
                        cycle += 0x800
                    subbuff = "".join((buff+buff)[seekaddr:seekaddr+cycle])
                    while len(subbuff) < length:
                        subbuff = subbuff + subbuff
                    copied = "".join(subbuff[:length])
                else:
                    copied = "".join((buff+buff)[seekaddr:seekaddr+length])
                assert len(copied) == length
                result += copied
                if debug:
                    print "%x" % seekaddr, length,
                while copied:
                    byte, copied = copied[0], copied[1:]
                    buff[buffaddr] = byte
                    buffaddr += 1
                    if buffaddr == 0x800:
                        buffaddr = 0
                    if debug:
                        print "%x" % ord(byte),
            if debug:
                print
                import pdb; pdb.set_trace()
    return result


def line_wrap(things, width=16):
    newthings = []
    while things:
        newthings.append(things[:width])
        things = things[width:]
    return newthings


def get_matrix_reachability(M):
    M2 = zip(*M)
    new = [0]*len(M)
    new = [list(new) for _ in range(len(M))]
    for i, row in enumerate(M):
        for j, row2 in enumerate(M2):
            for a, b in zip(row, row2):
                if a & b:
                    new[i][j] = a & b
                    break
            else:
                new[i][j] = 0 | M[i][j]
    return new


if __name__ == "__main__":
    M = [[1,0,0,1],
         [0,1,0,0],
         [0,0,1,1],
         [1,0,0,1]]
    M = get_matrix_reachability(M)
    for row in M:
        print row
