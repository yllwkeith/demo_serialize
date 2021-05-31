import random
import hashlib
import io

from linked_list import int_to_bytes, ListNode, ListRand


def calc_checksum(linked_list):
    checksum = hashlib.md5(b"1" if linked_list.looped() else b"0")
    nodes = {
        node: index
        for index, node in enumerate(linked_list)
    }
    for node in linked_list:
        rand = int_to_bytes(nodes[node.rand] + 1) if node.rand else int_to_bytes(0)
        checksum.update(rand)
        checksum.update(node.data.encode("utf-8"))
    return checksum


def test():
    nodes = [
        ListNode(data=f"test_data_{index}")
        for index in range(random.randint(1, 10))
    ]

    linked_list = ListRand()
    for node in nodes:
        linked_list.add(node)
        node.rand = random.choice([random.choice(nodes), None])

    print("Generated RandList:", linked_list, f"hash: {calc_checksum(linked_list).hexdigest()}", sep="\n")

    test_stream = io.BytesIO()
    linked_list.serialize(test_stream)

    test_stream.seek(0)

    new_linked_list = ListRand()
    new_linked_list.deserialize(test_stream)
    print("Deserialized RandList:", new_linked_list, f"hash: {calc_checksum(new_linked_list).hexdigest()}", sep="\n")

    test_stream.truncate(0)
    test_stream.seek(0)

    linked_list.head.prev = linked_list.tail
    linked_list.tail.next = linked_list.head

    print("Generated Looped RandList:", linked_list, f"hash: {calc_checksum(linked_list).hexdigest()}", sep="\n")

    linked_list.serialize(test_stream)
    test_stream.seek(0)
    new_linked_list.deserialize(test_stream)

    print("Deserialized looped RandList:",
          new_linked_list, f"hash: {calc_checksum(new_linked_list).hexdigest()}", sep="\n")


test()
