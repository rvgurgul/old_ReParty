from struct import unpack, pack
from datetime import datetime
from base64 import urlsafe_b64encode
from os import walk, path

class ReplayParser:
    class Replay:
        def __init__(
                self, uuid, playid, date, spy_displayname, sniper_displayname, spy_username, sniper_username, result,
                venue, variant, game_type, guests, clock, duration,
                selected_missions, picked_missions, completed_missions
        ):
            x = uuid.find('=')
            if x:
                uuid = uuid[:x]
            self.uuid = uuid
            self.playid = playid
            self.date = date
            self.spy = spy_displayname
            self.spy_username = spy_username
            self.sniper = sniper_displayname
            self.sniper_username = sniper_username
            self.result = result
            self.setup = game_type
            self.venue = venue
            self.variant = variant
            self.guests = guests
            self.clock = clock
            self.duration = duration
            self.selected_missions = selected_missions
            self.completed_missions = completed_missions
            self.picked_missions = picked_missions if game_type[0] == 'p' else None

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
            total_offset = self.players

            spy_user_len = sector[self.len_user_spy]
            spy_username = self.read_bytes(sector, total_offset, spy_user_len).decode()
            total_offset += spy_user_len

            sni_user_len = sector[self.len_user_sniper]
            sniper_username = self.read_bytes(sector, total_offset, sni_user_len).decode()

            spy_display_name, sniper_display_name = spy_username, sniper_username
            if self.len_disp_spy or self.len_disp_sniper:
                total_offset += sni_user_len
                spy_disp_len = sector[self.len_disp_spy]
                spy_display_name = self.read_bytes(sector, total_offset, spy_disp_len).decode()

                total_offset += spy_disp_len
                sni_disp_len = sector[self.len_disp_sniper]
                sniper_display_name = self.read_bytes(sector, total_offset, sni_disp_len).decode()

                if not spy_display_name:
                    spy_display_name = spy_username
                if not sniper_display_name:
                    sniper_display_name = sniper_username
            return spy_display_name, sniper_display_name, spy_username, sniper_username

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
    __MISSION_OFFSETS = {
        "Bug": 0,
        "Contact": 1,
        "Transfer": 2,
        "Swap": 3,
        "Inspect": 4,
        "Seduce": 5,
        "Purloin": 6,
        "Fingerprint": 7,
    }

    def __init__(self):
        if self.__VENUE_MAP is None:
            def endian_swap(value):
                return unpack("<I", pack(">I", value))[0]

            self.__VENUE_MAP = {
                endian_swap(0x26C3303A): "High-rise",
                endian_swap(0xAAFA9659): "Ballroom",
                endian_swap(0x2519125B): "Ballroom",
                endian_swap(0xA1C5561A): "High-rise",
                endian_swap(0x5EAAB328): "Old Gallery",
                endian_swap(0x750C0A29): "Old Courtyard 2",
                endian_swap(0x83F59536): "Panopticon",
                endian_swap(0x91A0BEA8): "Old Veranda",
                endian_swap(0xBC1F89B8): "Old Balcony",
                endian_swap(0x4073020D): "Pub",
                endian_swap(0xF3FF853B): "Pub",
                endian_swap(0xB0E7C209): "Old Ballroom",
                endian_swap(0x6B68CFB4): "Old Courtyard",
                endian_swap(0x8FE37670): "Double Modern",
                endian_swap(0x206114E6): "Modern",
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
        for mission in self.__MISSION_OFFSETS:
            if data & (1 << self.__MISSION_OFFSETS[mission]):
                missions.add(mission)
        return missions

    def __get_game_type(self, info):
        mode = info >> 28
        available = (info & 0x0FFFC000) >> 14
        required = info & 0x00003FFF
        real_mode = self.__MODE_MAP[mode]
        if real_mode == 'k':
            available = required
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

        date = datetime.fromtimestamp(self.__unpack_int(bytes_read, offsets.timestamp))
        venue = self.__VENUE_MAP[self.__unpack_int(bytes_read, offsets.venue)]
        if venue == 'Terrace' and date < datetime(year=2018, month=6, day=3):
            # Differentiate old from new Terrace by game date
            venue = 'Old Terrace'

        variant = None
        if offsets.variant:
            try:
                variant = self.__VARIANT_MAP[venue][self.__unpack_int(bytes_read, offsets.variant)]
            except KeyError:
                pass

        return ReplayParser.Replay(
            uuid=urlsafe_b64encode(bytes_read[uuid_offset:uuid_offset + 16]).decode(),
            playid=self.__unpack_short(bytes_read, offsets.playid), date=date,
            spy_displayname=name_extracts[0], sniper_displayname=name_extracts[1],
            spy_username=name_extracts[2], sniper_username=name_extracts[3],
            result=self.__RESULT_MAP[self.__unpack_int(bytes_read, offsets.result)],
            venue=venue, variant=variant,
            game_type=self.__get_game_type(self.__unpack_int(bytes_read, offsets.setup)),
            guests=self.__unpack_int(bytes_read, offsets.guests) if offsets.guests else None,
            clock=self.__unpack_int(bytes_read, offsets.clock) if offsets.clock else None,
            duration=int(self.__unpack_float(bytes_read, offsets.duration)),
            selected_missions=self.__unpack_missions(bytes_read, offsets.missions_s),
            picked_missions=self.__unpack_missions(bytes_read, offsets.missions_p),
            completed_missions=self.__unpack_missions(bytes_read, offsets.missions_c)
        )

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
        return list(filter(lambda replay: not any(not crit(replay) for crit in criteria), replays))

    def find_and_filter_replays(self, replays_directory, criteria):
        return self.filter_replays(self.parse_replays(self.find_replays(replays_directory)), criteria)
