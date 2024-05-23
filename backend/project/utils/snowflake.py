import time


class IdWorker:
    START_TIMESTAMP = 1581766186828 // 1000
    SEQUENCE_BIT = 14
    MACHINE_BIT = 4
    DATA_CENTER_BIT = 4
    MAX_DATA_CENTER_NUM = -1 ^ (-1 << DATA_CENTER_BIT)
    MAX_MACHINE_NUM = -1 ^ (-1 << MACHINE_BIT)
    MAX_SEQUENCE = -1 ^ (-1 << SEQUENCE_BIT)

    MACHINE_LEFT = SEQUENCE_BIT
    DATA_CENTER_LEFT = SEQUENCE_BIT + MACHINE_BIT
    TIMESTAMP_LEFT = DATA_CENTER_LEFT + DATA_CENTER_BIT

    def __init__(self, data_center_id, machine_id):
        if data_center_id > self.MAX_DATA_CENTER_NUM or data_center_id < 0:
            raise ValueError(
                "DATA_CENTER_ID can't be greater than MAX_DATA_CENTER_NUM or less than 0")
        if machine_id > self.MAX_MACHINE_NUM or machine_id < 0:
            raise ValueError(
                "MACHINE_ID can't be greater than MAX_MACHINE_NUM or less than 0")
        self.data_center_id = data_center_id
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1

    def next_id(self):
        curr_timestamp = self.get_new_timestamp()
        if curr_timestamp < self.last_timestamp:
            raise RuntimeError(
                "Clock moved backwards. Refusing to generate id")
        if curr_timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
            if self.sequence == 0:
                curr_timestamp = self.get_next_second()
        else:
            self.sequence = 0

        self.last_timestamp = curr_timestamp

        return ((curr_timestamp - self.START_TIMESTAMP) << self.TIMESTAMP_LEFT |
                self.data_center_id << self.DATA_CENTER_LEFT |
                self.machine_id << self.MACHINE_LEFT |
                self.sequence)

    def get_next_second(self):
        second = self.get_new_timestamp()
        while second <= self.last_timestamp:
            second = self.get_new_timestamp()
        return second

    def get_new_timestamp(self):
        return int(time.time())


id_worker = IdWorker(6, 6)


def new_id():
    return id_worker.next_id()
