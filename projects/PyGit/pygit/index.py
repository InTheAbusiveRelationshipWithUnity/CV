from typing import Tuple, List
import os


def write_index(data: List[Tuple[bytes, bytes, bytes]]) -> None:
    """
    Записывает файлы в индекс
    """
    os.makedirs(".pygit", exist_ok=True)
    with open(".pygit/index", "wb") as file:
        for i in data:
            if isinstance(i[0], str):
                file.write(i[0].encode("utf-8"))
            elif isinstance(i[0], bytes):
                file.write(i[0])

            file.write(b"\x00")

            try:
                if isinstance(i[1], str):
                    file.write(bytes.fromhex(i[1]))
                else:
                    file.write(i[1])
            except ValueError:
                return None

            file.write(b" ")

            if isinstance(i[2], str):
                file.write(i[2].encode("utf-8"))
            elif isinstance(i[2], bytes):
                file.write(i[2])
            else:
                return None

            file.write(b"\n")


def read_index() -> List[Tuple[bytes, bytes, bytes]]:
    """
    Считывает индекс и возвращает список кортежей,
    в которых хранятся данные о Blob`ах
    """
    index: List[Tuple[bytes, bytes, bytes]] = []
    if not os.path.exists(".pygit/index"):
        return index
    with open(".pygit/index", "rb") as f:
        read = f.readline()

        while read != b"":
            flag_mode = read.find(b" ")
            flag_path = read.find(b"\x00")

            path = read[:flag_path]
            sha = read[flag_path + 1:flag_mode]
            mode = read[flag_mode + 1: -1]

            index.append((path, sha, mode))

            read = f.readline()

    return index
