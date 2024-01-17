# e7awg_sw

## With Pip/Pipenv

### Requirements

- Python3 (3.9.18)
- pip (>= 23.2.1)
- pipenv (>= 2023.2.18)
- pyenv (>= 2.3.27-5-gf7f09650)

### Setup

For example,

```
% cd ${TMPDIR}
% git clone https://github.com/e-trees/e7awg_sw # use HTTPS
% git clone git@github.com:e-trees/e7awg_sw.git # or use SSH
% cd ${PIPENVDIR}
% pipenv shell
% pipenv install ${TMPDIR}/python/qube_lsi
```

## Standalone

### Requirements

- Python3 (3.9.18)
- pip (>= 23.2.1)
- pipenv (>= 2023.2.18)
- pyenv (>= 2.3.27-5-gf7f09650)
  - libssl-dev (Ubuntu 20.04)

### Setup

```
$ pipenv shell
$ pipenv install
```

If you don't have Python 3.9.18, the Python will be installed by `pyenv`.






