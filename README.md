# gencache
General caching script

```
usage: gencache.py [-h] --command COMMAND --source SOURCE [SOURCE ...] --build
                   BUILD --cache CACHE [--maxcache [MAXCACHE]]
                   [--verbose [VERBOSE]]

  -h, --help            show this help message and exit
  --command COMMAND     'fetch' to fetch from the cache, 'store' to store.
  --source SOURCE [SOURCE ...]
                        Path to the source code directory (or directories)
                        that generate the build.
  --build BUILD         Path to the output dir of the build.
  --cache CACHE         Path to the cache directory.
  --maxcache [MAXCACHE]
                        Size limit for the cache directory in GB.
  --verbose [VERBOSE]   Verbose output.
```

Example usage:

```bat
python gencache.py --command fetch --source c:\lib_repo\my_sources --build c:\lib_repo\build_output_dir --cache c:\my_cache_dir
if !errorlevel! equ 0 (
    echo Fetched from cache.
    exit /b 0
)
echo Not in cache so build
c:\lib_repo\my_sources\build.bat --output c:\lib_repo\build_output_dir

rem Store in the cache
python gencache.py --command store --source c:\lib_repo\my_sources --build c:\lib_repo\build_output_dir --cache c:\my_cache_dir
```

If after storing the cache exceeds the max cache size it will delete the least recently fetched directories in the cache one at a time until the size is under the max.

Note you can pass multiple directories to `--source`
