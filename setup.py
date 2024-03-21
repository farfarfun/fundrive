from funpypi import setups, read_version


version = read_version()

# multi_package=3
setups(
    [
        {
            "name": "fundrive",
            "version": version,
            "install_requires": ["requests", "funsecret", "tqdm", "funfile"],
        },
        {
            "name": "fundrive-deps",
            "packages": ["fundrive-deps"],
            "version": version,
            "install_requires": [
                f"fundrive>={version}",
                "requests_toolbelt",
            ],
        },
        {
            "name": "fundrive-lanzou",
            "packages": ["fundrive-deps"],
            "version": version,
            "install_requires": [
                f"fundrive>={version}",
                "requests_toolbelt",
                # "git+https://github.com/Leon406/lanzou-gui.git --no-deps",
            ],
        },
        {
            "name": "fundrive-oss",
            "packages": ["fundrive-deps"],
            "version": version,
            "install_requires": [
                f"fundrive>={version}",
                "oss2",
            ],
        },
    ]
)
