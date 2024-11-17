from sqlalchemy import create_engine as create_engine2

engine_map = {}


def create_engine(uri, cache=True, *args, **kwargs):
    global engine_map
    if cache:
        if uri not in engine_map.keys():
            engine_map[uri] = create_engine2(uri)
        return engine_map[uri]
    return create_engine2(uri)


def create_engine_sqlite(db_path):
    return create_engine(f"sqlite:///{db_path}")


def create_engine_mysql(host, user, password, db_name="", port=3306):
    return create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8"
    )
