from struct import unpack, pack
from datetime import datetime
from base64 import urlsafe_b64encode
from os import walk, path

class ReplayParser:
    class __ReplayVersionConstants:
        def __init__(
                self, magic_number=0x00, file_version=0x04, protocol_version=0x08, spyparty_version=0x0C,
                duration=0x14, uuid=0x18, timestamp=0x28, playid=0x2C,
                players=0x50, len_user_spy=0x2E, len_user_sniper=0x2F, len_disp_spy=None, len_disp_sniper=None,
                guests=None, clock=None, result=0x30, setup=0x34, venue=0x38, variant=None,
                missions_s=0x3C, missions_p=0x40, missions_c=0x44
        ):
            self.magic_number = magic_number
            self.file_version = file_version
            self.protocol_version = protocol_version
            self.spyparty_version = spyparty_version
            self.duration = duration
            self.uuid = uuid
            self.timestamp = timestamp
            self.playid = playid
            self.players = players
            self.len_user_spy = len_user_spy
            self.len_user_sniper = len_user_sniper
            self.len_disp_spy = len_disp_spy
            self.len_disp_sniper = len_disp_sniper
            self.guests = guests
            self.clock = clock
            self.result = result
            self.setup = setup
            self.venue = venue
            self.variant = variant
            self.missions_s = missions_s
            self.missions_p = missions_p
            self.missions_c = missions_c

        @staticmethod
        def read_bytes(sector, start, length):
            return sector[start:(start + length)]

        def extract_names(self, sector):
            spy_user_len = sector[self.len_user_spy]
            sni_user_len = sector[self.len_user_sniper]
            total_offset = self.players

            spy_name = self.read_bytes(sector, total_offset, spy_user_len).decode()
            total_offset += spy_user_len
            sni_name = self.read_bytes(sector, total_offset, sni_user_len).decode()

            if self.len_disp_spy or self.len_disp_sniper:
                total_offset += sni_user_len
                spy_disp_len = sector[self.len_disp_spy]
                temp = self.read_bytes(sector, total_offset, spy_disp_len).decode()
                if temp:
                    spy_name = temp

                total_offset += spy_disp_len
                sni_disp_len = sector[self.len_disp_sniper]
                temp = self.read_bytes(sector, total_offset, sni_disp_len).decode()
                if temp:
                    sni_name = temp

            return spy_name, sni_name

    @staticmethod
    def endian_swap(value):
        return unpack("<I", pack(">I", value))[0]

    __HEADER_DATA_MINIMUM_BYTES = 416
    __OFFSETS_DICT = {
        3: __ReplayVersionConstants(),
        4: __ReplayVersionConstants(
            players=0x54,
            result=0x34,
            setup=0x38,
            venue=0x3C,
            missions_s=0x40,
            missions_p=0x44,
            missions_c=0x48
        ),
        5: __ReplayVersionConstants(
            players=0x60,
            len_user_spy=0x2E,
            len_user_sniper=0x2F,
            len_disp_spy=0x30,
            len_disp_sniper=0x31,
            guests=0x50,
            clock=0x54,
            result=0x38,
            setup=0x3C,
            venue=0x40,
            missions_s=0x44,
            missions_p=0x48,
            missions_c=0x4C
        ),
        6: __ReplayVersionConstants(
            players=0x64,
            len_user_spy=0x2E,
            len_user_sniper=0x2F,
            len_disp_spy=0x30,
            len_disp_sniper=0x31,
            guests=0x54,
            clock=0x58,
            result=0x38,
            setup=0x3C,
            venue=0x40,
            variant=0x44,
            missions_s=0x48,
            missions_p=0x4C,
            missions_c=0x50
        )
    }
    __VENUE_MAP = None
    __VARIANT_MAP = {
        "Teien": [
            "BooksBooksBooks",
            "BooksStatuesBooks",
            "StatuesBooksBooks",
            "StatuesStatuesBooks",
            "BooksBooksStatues",
            "BooksStatuesStatues",
            "StatuesBooksStatues",
            "StatuesStatuesStatues"
        ],
        "Aquarium": [
            "Bottom",
            "Top"
        ],
    }
    __RESULT_MAP = {
        0: "Missions Win",
        1: "Time Out",
        2: "Spy Shot",
        3: "Civilian Shot",
        4: "In Progress"
    }
    __MODE_MAP = {
        0: "k",
        1: "p",
        2: "a"
    }

    def __init__(self):
        self.__VENUE_MAP = {
            self.endian_swap(0x26C3303A): "High-rise",
            self.endian_swap(0xAAFA9659): "Ballroom",
            self.endian_swap(0x2519125B): "Ballroom",
            self.endian_swap(0xA1C5561A): "High-rise",
            self.endian_swap(0x5EAAB328): "Old Gallery",
            self.endian_swap(0x750C0A29): "Old Courtyard 2",
            self.endian_swap(0x83F59536): "Panopticon",
            self.endian_swap(0x91A0BEA8): "Old Veranda",
            self.endian_swap(0xBC1F89B8): "Old Balcony",
            self.endian_swap(0x4073020D): "Pub",
            self.endian_swap(0xF3FF853B): "Pub",
            self.endian_swap(0xB0E7C209): "Old Ballroom",
            self.endian_swap(0x6B68CFB4): "Old Courtyard",
            self.endian_swap(0x8FE37670): "Double Modern",
            self.endian_swap(0x206114E6): "Modern",
            0x6f81a558: "Veranda",
            0x9dc5bb5e: "Courtyard",
            0x168f4f62: "Library",
            0x1dbd8e41: "Balcony",
            0x7173b8bf: "Gallery",
            0x9032ce22: "Terrace",
            0x2e37f15b: "Moderne",
            0x79dfa0cf: "Teien",
            0x98e45d99: "Aquarium",
            0x35ac5135: "Redwoods",
            0xf3e61461: "Modern"
        }

    def __unpack_missions(self, sector, offset):
        data = self.__unpack_int(sector, offset)
        missions = set()
        if data & (1 << 0):
            missions.add("Bug")
        if data & (1 << 1):
            missions.add("Contact")
        if data & (1 << 2):
            missions.add("Transfer")
        if data & (1 << 3):
            missions.add("Swap")
        if data & (1 << 4):
            missions.add("Inspect")
        if data & (1 << 5):
            missions.add("Seduce")
        if data & (1 << 6):
            missions.add("Purloin")
        if data & (1 << 7):
            missions.add("Fingerprint")
        return missions

    def __get_game_type(self, info):
        mode = info >> 28
        available = (info & 0x0FFFC000) >> 14
        required = info & 0x00003FFF
        real_mode = self.__MODE_MAP[mode]
        return "%s%d/%d" % (real_mode, required, available)

    @staticmethod
    def __read_bytes(sector, start, length):
        return sector[start:(start + length)]

    @staticmethod
    def __unpack_byte(sector, offset):
        return unpack('B', sector[offset])[0]

    def __unpack_float(self, sector, offset):
        return unpack('f', self.__read_bytes(sector, offset, 4))[0]

    def __unpack_int(self, sector, start):
        return unpack('I', self.__read_bytes(sector, start, 4))[0]

    def __unpack_short(self, sector, start):
        return unpack('H', self.__read_bytes(sector, start, 2))[0]

    def parse(self, replay_file_path):
        with open(replay_file_path, "rb") as replay_file:
            bytes_read = bytearray(replay_file.read())

        if len(bytes_read) < self.__HEADER_DATA_MINIMUM_BYTES:
            # raise Exception(f"A minimum of {self.__HEADER_DATA_MINIMUM_BYTES} bytes are required for replay parsing"
            #                 f" ({replay_file_path})")
            return

        if bytes_read[:4] != b"RPLY":
            # raise Exception("Unknown File")
            return

        read_file_version = self.__unpack_int(bytes_read, 0x04)
        try:
            offsets = self.__OFFSETS_DICT[read_file_version]
        except KeyError:
            # raise Exception("Unknown file version %d" % read_file_version)
            return

        name_extracts = offsets.extract_names(bytes_read)
        uuid_offset = offsets.uuid
        ret = {
            'spy': name_extracts[0], 'sniper': name_extracts[1],
            'result': self.__RESULT_MAP[self.__unpack_int(bytes_read, offsets.result)],
            'venue': self.__VENUE_MAP[self.__unpack_int(bytes_read, offsets.venue)],
            'selected_missions': self.__unpack_missions(bytes_read, offsets.missions_s),
            'picked_missions': self.__unpack_missions(bytes_read, offsets.missions_p),
            'completed_missions': self.__unpack_missions(bytes_read, offsets.missions_c),
            'playid': self.__unpack_short(bytes_read, offsets.playid),
            'start_time': datetime.fromtimestamp(self.__unpack_int(bytes_read, offsets.timestamp)),
            'duration': int(self.__unpack_float(bytes_read, offsets.duration)),
            'game_type': self.__get_game_type(self.__unpack_int(bytes_read, offsets.setup)),
            'uuid': urlsafe_b64encode(bytes_read[uuid_offset:uuid_offset + 16]).decode(),
            'guests': self.__unpack_int(bytes_read, offsets.guests) if offsets.guests else None,
            'clock': self.__unpack_int(bytes_read, offsets.clock) if offsets.clock else None,
            'variant': None,
            'path': replay_file_path
        }

        if offsets.variant:
            try:
                ret['variant'] = self.__VARIANT_MAP[ret['level']][self.__unpack_int(bytes_read, offsets.variant)]
            except KeyError:
                pass

        if ret['uuid'].find('=') > 0:
            ret['uuid'] = ret['uuid'][:ret['uuid'].find('=')]

        return ret

    @staticmethod
    def find_replays(from_directory):
        replays = []
        for root, _, files in walk(from_directory):
            if "__" in root:
                continue
            for file in files:
                if file.endswith(".replay"):
                    file_path = path.join(root, file)
                    if len(file_path) > 255:
                        # todo deal with excessively long paths later
                        continue
                    replays.append(file_path)
        return replays

    def parse_replays(self, replays):
        return map(self.parse, replays)

    @staticmethod
    def filter_replays(replays, criteria):
        # not any(not crit(...
        # filter games where any of the criteria are False
        return list(filter(lambda replay: not any(not crit(replay) for crit in criteria), replays))

    def find_and_filter_replays(self, replays_directory, criteria):
        # reps = self.find_replays(replays_directory)
        # parsed = self.parse_replays(reps)
        # filtered = self.filter_replays(parsed, criteria)
        # return filtered
        return self.filter_replays(self.parse_replays(self.find_replays(replays_directory)), criteria)
