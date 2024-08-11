import os


def wget(url, output=None, append=None, debug=None, quiet=None, verbose=None, noverbose=None):
    kwargs = {
        "output-file": output,
        "append-output": append,
        "debug": debug,
        "quiet": quiet,
        "verbose": verbose,
        "no-verbose": noverbose
    }

    args = ['--{}={}'.format(key, value) for key, value in kwargs.items() if value is not None]

    command = "wget {args} {url}".format(url=url, args=' '.join(args))
    res = os.system(command)
    return res
