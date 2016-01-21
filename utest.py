import sys
sys.path.append('src')
sys.path.append('lib')

sys.dont_write_bytecode = True  # stop pytest from cluttering everything with it's .pyc files

import pytest

def run(modules):
    if type(modules) != list:
        modules = [modules]
        pytest.main(['-p', 'no:cacheprovider'] + modules)  # also stop pytest from creating .cache folder

if __name__ == '__main__':

    # gather files
    import glob
    paths = []
    for folder in ['src', 'lib']:
        paths.extend(glob.glob(folder + '/*.py'))

    run(paths)
