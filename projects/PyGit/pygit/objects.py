import abc
import hashlib
import zlib
import os
from typing import List, Tuple, Union, Optional


class GitObject(abc.ABC):
    @abc.abstractmethod
    def serialize(self) -> bytes:
        pass

    @abc.abstractmethod
    def deserialize(self, data: bytes) -> None:
        pass


class Blob(GitObject):
    """
    class Blob(GitObject) - хранит содержимое файла
    """
    def __init__(self, data: bytes):
        self.data = data

    def serialize(self) -> bytes:
        return self.data

    def deserialize(self, data: bytes) -> None:
        self.data = data


class Tree(GitObject):
    """
    class Tree(GitObject) -
    Хранит информацию о целых директориях и файлах
    """
    def __init__(self, data: List[Tuple[bytes, bytes, bytes]] = []):
        self.data = data

    def serialize(self) -> bytes:
        binary = b""
        for mode, path, sha in self.data:
            binary += mode + b" " + path + b"\x00" + sha
        return binary

    def deserialize(self, data: bytes) -> None:
        self.data = []
        count = 0
        while count < len(data):
            flag = data.find(b" ", count)
            if flag < 0:
                break
            mode = data[count:flag]
            count = flag + 1

            flag = data.find(b"\x00", count)
            if flag < 0:
                break
            path = data[count:flag]

            if count + 20 > len(data):
                break
            sha = data[count:count + 20]
            count += 20

            self.data.append((mode, path, sha))


class Commit(GitObject):
    """
    class Commit(GitObject) -
    Хранит данные о коммите
    """
    def __init__(
        self,
        tree_hash: bytes = b"",
        parent_hash: Optional[bytes] = None,
        author: str = "",
        email: str = "",
        timemark: str = "",
        text: str = "",
    ):

        self.tree_hash = tree_hash
        self.parent_hash = parent_hash
        self.author = author
        self.email = email
        self.timemark = timemark
        self.text = text

    def serialize(self) -> bytes:
        git_txt = b""

        git_txt += (f"tree {self.tree_hash.hex()} ").encode("utf-8")
        if self.parent_hash:
            git_txt += f"parent {self.parent_hash.hex()} ".encode("utf-8")
        git_txt += f"author {self.author} email <{self.email}>".encode("utf-8")
        git_txt += f"time {self.timemark} message ".encode("utf-8")
        git_txt += self.text.encode("utf-8")

        return git_txt

    def deserialize(self, data: bytes) -> None:
        decode = data.decode("utf-8")

        author_flag = decode.find("author")
        parent_flag = decode.find("parent")
        email_flag = decode.find("email")
        time_flag = decode.find("time")
        message_flag = decode.find("message")

        if parent_flag != -1:
            self.tree_hash = bytes.fromhex(decode[5:parent_flag - 1])
            parent_hex = decode[parent_flag + 7: author_flag - 1]
            self.parent_hash = bytes.fromhex(parent_hex)
        else:
            self.tree_hash = bytes.fromhex(decode[5:author_flag - 1])

        self.author = decode[author_flag + 7: email_flag - 1]
        self.author_email = decode[email_flag + 7: time_flag - 1]
        self.timemark = decode[time_flag + 5: message_flag - 1]
        self.text = decode[message_flag + 8:]


class CommitHistoryIterator:
    """
    Класс-итератор class CommitHistoryIterator -
    Построение истории коммитов
    """
    def __init__(self, start_sha: Optional[bytes]):
        self.current_sha = start_sha

    def __iter__(self) -> "CommitHistoryIterator":
        return self

    def __next__(self) -> dict[str, Union[bytes, str]]:
        if self.current_sha is None:
            raise StopIteration

        dehash = dehash_object(self.current_sha)
        commit = Commit()
        commit.deserialize(dehash[1].encode("utf-8"))

        sha = self.current_sha

        if commit.parent_hash is None:
            self.current_sha = None
        else:
            self.current_sha = commit.parent_hash

        return {
            "sha1": sha,
            "author": commit.author,
            "author email": commit.author_email,
            "time": commit.timemark,
            "message": commit.text
        }


def dehash_object(sha: bytes) -> tuple[str, str]:
    """
    Производит дехеширование данных
    """
    decode_sha = sha.decode("utf-8")
    with open(
        os.path.join(".pygit/objects", decode_sha[:2], decode_sha[2:]),
        "rb"
    ) as f:
        data = f.read()
    data = zlib.decompress(data)

    header = data[:data.find(b"\x00")].decode("utf-8")
    decode_data = data[data.find(b"\x00") + 1:].decode("utf-8")

    return (header.split(" ")[0], decode_data)


def hash_object(data: bytes, obj_type: str) -> str:
    """
    Хеширует данные
    """
    head = f"{obj_type} {len(data)}\0".encode("utf-8")
    data = head + data

    sha1 = hashlib.sha1(data).hexdigest()
    data = zlib.compress(data)

    path = f".pygit/objects/{sha1[:2]}/{sha1[2:]}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as file:
        file.write(data)

    return sha1
