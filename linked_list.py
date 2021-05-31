import hashlib
import io

INT_SIZE = 4
CHECKSUM_SIZE = 16
DATA_ENCODING = "utf-8"

LOOPED_MARK = b"1"
NON_LOOPED_MARK = b"0"


class EmptyListError(Exception):
    pass


class IntegrityError(Exception):
    pass


def int_to_bytes(_int: int):
    return _int.to_bytes(INT_SIZE, "big", signed=False)


def bytes_to_int(_bytes: bytes):
    return int.from_bytes(_bytes, "big", signed=False)


def read_int(stream: io.BytesIO):
    _bytes = stream.read(INT_SIZE)
    return bytes_to_int(_bytes)


def data_or_null(node):
    return node.data if node is not None else "null"


class ListNode:
    def __init__(self, data=None):
        self.prev = None
        self.next = None
        self.rand = None
        self.data = data

    def __str__(self):
        return "self: {}| prev: {}| rand: {}| next: {}".format(
            self.data, data_or_null(self.prev),
            data_or_null(self.rand), data_or_null(self.next),
        )


class ListRand:
    """
        Формат хранения ListRand
        Первый байт означает замкнутый список или нет (1/0).
        Далее все числа представленны в виде беззнакого числа размером в 4 байта.
        Со второго по пятый байт идет число означающие количество элементов в списке.
        Далее идут блоки с информацией о каждой отдельной ноде.
        Каждый блок состоит из трех частей: индекса случайного элемента, размера данных и самих данных.
        Индекс начинается с 1, 0 означает отсуствие ссылки.
        Данные -- строкой в utf-8.
        Последние 16 байт -- чексумма в виде md5 хеша.
    """

    def __init__(self):
        self.head = None
        self.tail = None
        self.count = 0

    def clear(self):
        self.head = None
        self.tail = None
        self.count = 0

    def looped(self):
        return self.head.prev is self.tail and self.tail.next is self.head

    def serialize(self, stream: io.BytesIO):
        if not self.count:
            raise EmptyListError

        looped = LOOPED_MARK if self.looped() else NON_LOOPED_MARK
        stream.write(looped)

        stream.write(int_to_bytes(self.count))
        checksum = hashlib.md5(looped)

        nodes = {
            node: index
            for index, node in enumerate(self)
        }

        for node in self:
            rand = nodes[node.rand] + 1 if node.rand else 0
            rand = int_to_bytes(rand)
            stream.write(rand)
            checksum.update(rand)

            data = bytes(node.data, encoding=DATA_ENCODING)
            stream.write(int_to_bytes(len(node.data)))
            stream.write(data)
            checksum.update(data)

        stream.write(checksum.digest())

    def deserialize(self, stream: io.BytesIO):
        self.clear()

        looped = stream.read(1)
        looped = True if looped == LOOPED_MARK else False

        checksum = hashlib.md5(LOOPED_MARK if looped else NON_LOOPED_MARK)

        nodes = {}
        total_count = read_int(stream)
        while total_count > self.count:
            rand = stream.read(INT_SIZE)
            checksum.update(rand)
            rand = bytes_to_int(rand) - 1

            data_size = read_int(stream)
            data = stream.read(data_size)
            checksum.update(data)
            data = data.decode(DATA_ENCODING)

            nodes.setdefault(self.count, ListNode())

            node = nodes[self.count]
            node.data = data

            if rand != -1:
                nodes.setdefault(rand, ListNode())
                node.rand = nodes[rand]

            self.add(node)
        expected_checksum = stream.read(CHECKSUM_SIZE)

        if looped:
            self.head.prev = self.tail
            self.tail.next = self.head

        if checksum.digest() != expected_checksum:
            self.clear()
            raise IntegrityError

    def add(self, node):
        if not self.count:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node

        self.count += 1

    def __iter__(self):
        if not self.count:
            raise EmptyListError

        cur_element = 0
        node = self.head
        while node is not None and cur_element < self.count:
            yield node
            node = node.next
            cur_element += 1

    def __str__(self):
        return "\n".join(map(str, self))
