# e7awg_sw

### Requirements

- Python3 (3.9.18)
- pyenv (>= 2.3.27-5-gf7f09650)
- Pipenv (>= 2023.2.18)
- Pip (>= 23.2.1)

### Setup

```
% mkdir -p <YOUR_WORK_DIR>
% cd <YOUR_WORK_DIR>
% pyenv install 3.9.18
% pyenv global 3.9.18
% pip install --upgrade pip # should be installed pip >= 23.2.1
% git clone https://github.com/e-trees/e7awg_sw # use HTTPS
% git clone git@github.com:e-trees/e7awg_sw.git # or use SSH
% cd e7awg_sw
% pipenv sync
% pipenv shell

# Make a directory to put the lock files used by e7awgsw library in the way of (1) or (2).

## (1) Make a directory and set the E7AWG_HW_LOCKDIR environment variable to it's path.
% mkdir dir-path
% export E7AWG_HW_LOCKDIR="dir-path"

## (2) Make a directory with the path /usr/local/etc/e7awg_hw/lock
% mkdir /usr/local/etc/e7awg_hw/lock
```
