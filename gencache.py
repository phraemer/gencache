# Probably exists already but rolled my own.
# Store or fetch from a cache a the result of a build of some directory tree's contents.
# The key to the cache is a hash of the directory tree's contents.

import hashlib, os, sys, argparse, shutil
from distutils.dir_util import copy_tree

parser = argparse.ArgumentParser()
parser.add_argument("--command", help="'fetch' to fetch from the cache, 'store' to store.", required=True)
parser.add_argument("--source", help="Path to the source code directory that generates the build.", required=True)
parser.add_argument("--build", help="Path to the output dir of the build.", required=True)
parser.add_argument("--cache", help="Path to the cache directory.", required=True)
args = parser.parse_args()

if args.command != 'fetch' and args.command != 'store':
    print('command must be either fetch or store')
    exit(1)

def exit_unless_exists_and_is_dir(p):
    if not os.path.exists(p):
        print('{0} does not exist'.format(p))
        exit(1)

    if not os.path.isdir(p):
        print('{0} is not a directory'.format(p))
        exit(1)

exit_unless_exists_and_is_dir(args.source)
exit_unless_exists_and_is_dir(args.cache)
exit_unless_exists_and_is_dir(args.build)

hasher = hashlib.md5()

# Hash the contents of the directory tree
exclude_prefixes = ('__', '.')  # exclusion prefixes
for root, dirs, files in os.walk(args.source, topdown=True):
    for name in files:
        print('hashing ' + name)
        file_name = (os.path.join(root, name))
        with open(str(file_name), 'rb') as a_file:
            buf = a_file.read()
            hasher.update(buf)

cache_dir_name = hasher.hexdigest()
print('Source directories hash {0}'.format(cache_dir_name))

cache_dir_path = os.path.join(args.cache, cache_dir_name)

def get_dir_size(start_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def shrink_cache(cache_dir):
    cache_size = get_dir_size(args.cache)
    # Repeat until cache size is under 1GB
    while cache_size > 1e+9:
        # Get the dirs in the cache sorted by oldest first
        cache_dirs = sorted([(f.path, os.stat(f.path)) for f in os.scandir(cache_dir) if f.is_dir()], key=lambda dir: dir[1].st_ctime)
        # Purge the oldest
        print('Purging {0}'.format(cache_dirs[0][0]))
        shutil.rmtree(cache_dirs[0][0])
        cache_size = get_dir_size(args.cache)
    print('Cache size {0}'.format(cache_size))

if args.command == 'fetch':
    # Is a directory with that hash in the cache dir?
    if os.path.isdir(cache_dir_path):
        # Yes, so copy the contents to the build output dir
        print('Fetching from {0} to {1}'.format(cache_dir_path, args.build))
        copy_tree(cache_dir_path, args.build)
    else:
        # Nope
        print('Not in cache:' + cache_dir_name)
        exit(1)
elif args.command == 'store':
    print('Storing')
    copy_tree(args.build, cache_dir_path)
    shrink_cache(args.cache)
else:
    print('Unknown command {0}'.format(args.command))
