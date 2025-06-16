import inspect


def start_program(source, launcher, tmpdir_factory):
    f = tmpdir_factory.mktemp('data').join('program.py')
    lines = inspect.getsourcelines(source)
    code = ''.join(line[4:] for line in lines[0][1:])
    f.write(code)
    launcher.load(str(f))
    launcher.cycle_start()
    yield str(f)
    launcher.abort()
    launcher.unload()
