from nltsecret import read_secret

read_secret(
    "fundrive", "webdav", "funtrack", "server_url", "http://192.168.31.131:19798/dav/"
)
read_secret("fundrive", "webdav", "funtrack", "username", value="funtrack")
read_secret("fundrive", "webdav", "funtrack", "password", value="funtrack")
