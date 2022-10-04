# Binsize tool

Tool for analyzing the sizes of symbols in binaries.

It can be used to find out which symbols are taking up the most space in a binary.

It requires `bloaty` and `nm` tools to be installed.

It analyzes the `.elf` file and optionally also the `.map` file from the binary creation process.

## Tool basic usage

Installable by `pip install binsize` - see [PyPI](https://pypi.org/project/binsize/).

Installing this package creates `binsize` command, which has a lot of subcommands seeable by `binsize --help`. For example

```bash
$ binsize get firmware.elf -d
$ binsize compare firmware.elf other_firmware.elf
$ binsize tree firmware.elf
```

`--help` can be used even on the subcommands, for example `binsize get --help` - to see all available options.

Result will be usually printed into terminal, unless specifying `--output` option which some commands support.

## Setting root directory
To resolve all the files properly, the project's root directory needs to be set correctly.

There are couple of possibilities how to do it.

In the end, all of them are changing the `root` value in `settings.json`, from where everything else gets the value. It needs to be an absolute path.

`settings.json` will be created in a user's home directory, based on `platformdirs` library (`~/.config/binsize/settings.json` on `linux`).

### Manually
Just modifying the `root` in the `settings.json` file.

### Via environmental variable
`BINSIZE_ROOT_DIR` env variable is checked and when not empty, it will set the root directory.

e.g. `BINSIZE_ROOT_DIR=/home/user/project binsize tree /path/to/file.elf`

### Via CLI argument
`binsize` accepts `-r / --root-dir` argument, which can be used to set the root directory.

It has lower priority than the environmental variable.

e.g. `binsize -r /home/user/project tree /path/to/file.elf`

### Via exposed function
`binsize` exposes `set_root_dir` function, which can be called from any `python` script.

e.g. `binsize.set_root_dir("/home/user/project")`

---

TODO: document all the CLI commands, exportable symbols, basic functioning, ways to extend it, etc.
