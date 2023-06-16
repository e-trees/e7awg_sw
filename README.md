# e7awg_sw

## With Pip/Pipenv

### Requirements

- Python3 (+3.9)

### Setup

For example,

```
% cd ${TMPDIR}
% git clone https://github.com/e-trees/e7awg_sw # use HTTPS
% git clone git@github.com:e-trees/e7awg_sw.git # or use SSH
% cd ${PIPENVDIR}
% pipenv shell
% pipenv install ${TMPDIR}/python/qube_lsi

# Make a directory to put the lock files used by e7awgsw library in the way of (1) or (2).

## (1) Make a directory and set the E7AWG_HW_LOCKDIR environment variable to it's path.
% mkdir dir-path
% export E7AWG_HW_LOCKDIR="dir-path"

## (2) Make a directory with the path /usr/local/etc/e7awg_hw/lock
% mkdir /usr/local/etc/e7awg_hw/lock
```

## Standalone

### Requirements

- Python3 (+3.9)
- pipenv
- pyenv
  - libssl-dev (Ubuntu 20.04)

### Setup

```
$ pipenv shell
$ pipenv install

# Make a directory to put the lock files used by e7awgsw library in the way of (1) or (2).

## (1) Make a directory and set the E7AWG_HW_LOCKDIR environment variable to it's path.
% mkdir dir-path
% export E7AWG_HW_LOCKDIR="dir-path"

## (2) Make a directory with the path /usr/local/etc/e7awg_hw/lock
% mkdir /usr/local/etc/e7awg_hw/lock
```

If you don't have Python 3.9.10, the Python will be installed by `pyenv`.






