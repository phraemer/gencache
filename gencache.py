# Probably exists already but rolled my own.
# Get new versions here https://github.com/phraemer/gencache
# Store or fetch from a cache a the result of a build of some directory tree's contents.
# The key to the cache is a hash of the directory tree's contents.

import argparse
import hashlib
import os
import pathlib
import shutil
import sys
import uuid
from distutils.dir_util import copy_tree

parser = argparse.ArgumentParser()
parser.add_argument(
    "--command", help="'fetch' to fetch from the cache, 'store' to store.", required=True)
parser.add_argument(
    "--source", help="Path to the source code directory (or directories) that generate the build.", nargs='+', required=True)
parser.add_argument(
    "--build", help="Path to the output dir of the build.", required=True)
parser.add_argument(
    "--cache", help="Path to the cache directory.", required=True)
parser.add_argument("--maxcache", help="Size limit for the cache directory in GB.",
                    nargs='?', const=1, type=int, default=25)
parser.add_argument("--verbose", help="Verbose output.",
                    nargs='?',  type=bool, default=False)
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


exit_unless_exists_and_is_dir(args.cache)

hasher = hashlib.md5()

# Hash the contents of the directory tree
for source_dir in args.source:
    if args.verbose:
        print('Source dir: {0}'.format(source_dir))
    exit_unless_exists_and_is_dir(source_dir)
    for root, dirs, files in os.walk(source_dir, topdown=True):
        dirs.sort()
        files.sort()
        for name in [f for f in files if not (f.startswith('.') or f.startswith('__'))]:
            if args.verbose:
                print('hashing: {0}'.format(name))
            file_name = (os.path.join(root, name))
            with open(str(file_name), 'rb') as a_file:
                buf = a_file.read()
                hasher.update(buf)

cache_dir_name = hasher.hexdigest()
print('Source directories hash {0}'.format(cache_dir_name))

cache_dir_path = os.path.join(args.cache, cache_dir_name)
cache_dir_tmp_path = cache_dir_path + str(uuid.uuid4())

def get_dir_size(start_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def shrink_cache(cache_dir):
    print('Shrinking cache if needed')
    cache_size = get_dir_size(args.cache)
    # Repeat until cache size is under maxcache
    while cache_size > (1e+9 * args.maxcache):
        # Get the dirs in the cache sorted by oldest first
        cache_dirs = sorted([(f.path, os.stat(f.path)) for f in os.scandir(
            cache_dir) if f.is_dir()], key=lambda dir: dir[1].st_ctime)
        # Purge the oldest
        print('Purging {0}'.format(cache_dirs[0][0]))
        shutil.rmtree(cache_dirs[0][0])
        cache_size = get_dir_size(args.cache)
    print('Cache size {0}'.format(cache_size))

def copy_dir_tree(src_dir, dst_dir):
    if sys.platform == 'win32':
        pathlib.Path(dst_dir).mkdir(parents=True, exist_ok=True)
        os.system('xcopy /Y /I /E "{0}" "{1}"'.format(src_dir, dst_dir))
    else:
        copy_tree(src_dir, dst_dir.build)

if args.command == 'fetch':
    # Is a directory with that hash in the cache dir?
    if os.path.isdir(cache_dir_path):
        # Yes, so copy the contents to the build output dir
        print('Fetching from {0} to {1}'.format(cache_dir_path, args.build))
        copy_dir_tree(cache_dir_path, args.build)
        # Update the modification time on the directory to make cache ejection LRU
        os.utime(cache_dir_path)
    else:
        # Nope
        print('Not in cache: {0}'.format(cache_dir_name))
        exit(1)
elif args.command == 'store':
    # If we can't create the dest dir then another process is probably storing right now
    try:
        pathlib.Path(cache_dir_path).mkdir(parents=True)
    except OSError as ex:
        print('"{0}" is already in the cache or currently being stored.'.format(cache_dir_path))
    print('Storing from {0} in temp dir {1}'.format(args.build, cache_dir_tmp_path))
    exit_unless_exists_and_is_dir(args.build)
    # Copy to a temp dir
    copy_dir_tree(args.build, cache_dir_tmp_path)
    # Rename the temp dir to the hash name
    # Don't know yet how to atomically replace the destination dir on Windows network shares
    shutil.rmtree(cache_dir_path)
    os.rename(cache_dir_tmp_path, cache_dir_path)
    shrink_cache(args.cache)
else:
    print('Unknown command {0}'.format(args.command))
