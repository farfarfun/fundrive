from typing import Optional

import chardet  # type: ignore

from ..common.io import MAX_CHUNK_SIZE
from ..pcs import BaiduPCSApi
from .display import display_blocked_remotepath


def cat(
    api: BaiduPCSApi,
    remotepath: str,
    max_chunk_size: int = MAX_CHUNK_SIZE,
    encoding: Optional[str] = None,
    encrypt_password: bytes = b"",
):
    fs = api.file_stream(remotepath, encrypt_password=encrypt_password)
    if not fs:
        display_blocked_remotepath(remotepath)
        return

    cn = fs.read()
    if cn:
        if encoding:
            print(cn.decode(encoding))
        else:
            r = chardet.detect(cn)
            if r["confidence"] > 0.5:
                print(cn.decode(r["encoding"]))  # type: ignore
            else:
                print(cn)
