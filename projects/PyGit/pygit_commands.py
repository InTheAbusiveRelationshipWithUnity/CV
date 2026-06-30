import os
import sys
from typing import Union, Callable, Any
from datetime import datetime, timezone
from pygit.objects import (  # type: ignore
    hash_object,
    Tree,
    Commit,
    CommitHistoryIterator
)
from pygit.index import write_index, read_index  # type: ignore


CMD: dict[str, Callable[..., Any]] = dict()


def command(
        command: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(
        function: Callable[..., Any]
    ) -> Callable[..., Any]:
        CMD[command] = function
        return function

    return decorator


@command("config")
def config(args: list[str]) -> None:
    """
    Реализация функции config для хранения данных о коммитере
    """
    key, value = args[0], args[1]

    data = []
    if os.path.exists(".pygitconfig"):
        with open(".pygitconfig", "r") as f:
            data = f.readlines()

    with open(".pygitconfig", "w") as f:
        is_inside = False
        for i in range(len(data)):
            data[i] = data[i].replace("\n", "")
            if key == data[i][:len(key)]:
                data[i] = f"{key}: {value}"
                is_inside = True

        f.write("\n".join(data))

        if data == []:
            f.write(f"{key}: {value}")
        elif not is_inside:
            f.write(f"\n{key}: {value}")


@command("init")
def init() -> None:
    """
    Функция def init() -> None - реализации команды init
    """

    if os.path.exists(".pygit"):
        print("Директория уже существует")
    else:
        os.makedirs(".pygit")

    if not os.path.exists(".pygit/objects"):
        os.makedirs(os.path.join(".pygit", "objects"))
    if not os.path.exists(".pygit/refs/heads"):
        os.makedirs(os.path.join(".pygit", "refs", "heads"))

    with open(".pygit/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")

    print("Repository done")


def get_mode(path: str) -> bytes:
    """
    Функция для получения прав доступа на фалй/директорию по пути path
    """
    if os.path.isdir(path):
        mode = "0" + oct(os.stat(path).st_mode)[2:]
    else:
        mode = oct(os.stat(path).st_mode)[2:]

    return mode.encode("utf-8")


@command("add")
def add(file_path: str) -> None:
    """
    Функция def add() -> None - реализация команды add
    """
    if isinstance(file_path, list):
        file_path = file_path[0]
    if not os.path.exists(file_path):
        print("No such file")
        return None

    with open(file_path, "rb") as f:
        file = f.read()

    hash = hash_object(file, "blob")

    file_path_bytes = file_path.encode("utf-8")
    index = read_index()
    index = [
        (path, sha, mode) for path, sha, mode in index
        if path != file_path_bytes
    ]

    mode = get_mode(file_path)
    index.append((file_path_bytes, bytes.fromhex(hash), mode))

    write_index(index)


def get_directories() -> (
    tuple[
        dict[bytes, list[Union[bytes, tuple[bytes, bytes, bytes]]]],
        list[Union[bytes, tuple[bytes, bytes, bytes]]]
    ]
):
    """
    Функция, возвращающая все директории, расположенные в индексе
    """
    index = read_index()

    directories: dict[
        bytes,
        list[Union[bytes, tuple[bytes, bytes, bytes]]]
    ] = dict()
    directories[b""] = []
    dir_first_ord: list[Union[bytes, tuple[bytes, bytes, bytes]]] = []
    for path, sha, mode in index:
        dirs = path.split(b"/")

        if dirs.count(b"/") != 0:
            dir_first_ord.append(dirs[0])
        else:
            dir_first_ord.append((path, sha, mode))

        for i in range(len(dirs) - 1):
            if b"/".join(dirs[:i + 1]) not in directories:
                directories[b"/".join(dirs[:i + 1])] = []

            if i + 2 != len(dirs):
                key = b"/".join(dirs[:i + 1])
                value_path = b"/".join(dirs[:i + 2])
                directories[key].append(value_path)

        directories[b"/".join(dirs[:-1])].append((path, sha, mode))
    return (directories, dir_first_ord)


@command("write-tree")
def write_tree() -> str:
    def _tree_generator(
        dir: Union[bytes, tuple[bytes, bytes, bytes]],
        directories: dict[
            bytes,
            list[Union[bytes, tuple[bytes, bytes, bytes]]]
        ]
    ) -> Union[Tree, tuple[bytes, bytes, bytes]]:
        """
        Вспомогательная функция,
        рекурсивно обходящая директории и строящая деревья
        """
        if isinstance(dir, tuple):
            return dir

        data = []

        for i in directories[dir]:
            if isinstance(i, tuple):
                data.append(i)
            else:
                new_tree = _tree_generator(i, directories)
                if isinstance(new_tree, Tree):
                    sha = hash_object(
                        new_tree.serialize(),
                        "tree"
                    )
                    mode = get_mode(i.decode("utf-8"))
                    data.append((i, sha.encode("utf-8"), mode))

        tree = Tree(data)
        return tree

    dirs = get_directories()
    directories, dir_first_ord = dirs[0], dirs[1]
    lead_tree = Tree()

    for i in dir_first_ord:
        tree = _tree_generator(i, directories)

        if not isinstance(tree, tuple):
            sha = hash_object(tree.serialize(), "tree")
            if isinstance(i, bytes):
                mode = get_mode(i.decode("utf-8"))
                lead_tree.data.append((i, sha.encode("utf-8"), mode))
            continue
        lead_tree.data.append(tree)

    lead_sha = hash_object(lead_tree.serialize(), "tree")
    print(lead_sha)
    return str(lead_sha)


def get_commit() -> bytes:
    """
    Функция для получения хеша текущего коммита
    """
    if os.path.exists(".pygit/HEAD"):
        with open(".pygit/HEAD") as f:
            head = f.read().strip()

        if head.startswith("ref: refs/heads"):
            parent_path = ".pygit/" + head[5:].replace("/HEAD", "")
            if os.path.exists(parent_path):
                with open(parent_path, "r") as com:
                    return com.read().strip().encode("utf-8")

    return b""


@command("commit")
def commit(args: list[str]) -> None:
    """
    Реализация команды commit
    """
    message = args[-1]

    tree_sha = write_tree()
    parent_sha = get_commit()
    author = ""
    author_email = ""

    if os.path.exists(".pygitconfig"):
        with open(".pygitconfig", "r") as f:
            author_info = f.readlines()

        for i in author_info:
            if "email" in i:
                author_email = i[len("email: "):-1]
            elif "name" in i:
                author = i[len("name: "):-1]

    time = datetime.now(timezone.utc).astimezone()
    timestamp = str(int(time.timestamp()))
    zone = time.strftime("%z")

    new_commit = Commit(
        tree_sha.encode("utf-8"),
        parent_sha if parent_sha != b"" else None,
        author,
        author_email,
        timestamp + " " + zone,
        message
    )

    commit_hash = hash_object(new_commit.serialize(), "commit")

    with open(".pygit/HEAD") as f:
        head = f.read().strip()
        with open(".pygit/" + head[5:].replace("/HEAD", ""), "w") as com:
            com.write(commit_hash)

    f = open(".pygit/index", "w")
    f.close()


@command("log")
def log() -> None:
    """
    Реализация комманды log
    """
    sha = get_commit()
    for commit_info in CommitHistoryIterator(sha):
        print(commit_info)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in CMD:
        print("Missing command")

    command_name = sys.argv[1]
    command_args = sys.argv[2:]

    if command_args != []:
        CMD[command_name](command_args)
    else:
        CMD[command_name]()


if __name__ == "__main__":
    main()
