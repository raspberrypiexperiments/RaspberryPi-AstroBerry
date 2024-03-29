# RaspberryPi-AstroBerry

## Overview

This repository provides desktop GUI for Raspberry Pi HQ Camera. As a unique feature it delivers manual
control for shutter speed and ISO and enables shooting pictures in extremely dark conditions
(astrophotography).

## Dependencies

This repository depends on
[RaspberryPi-gst-rpicamsrc](https://github.com/raspberrypiexperiments/RaspberryPi-gst-rpicamsrc.git)
repository.

## Known supported Raspberry Pi

* Raspberry Pi 3B,
* Raspberry Pi 3A+.

## Known supported OS

* Bullseye.

## Installation

Installation procedure:

```bash
git clone --recurse-submodules -j$(nproc) \
    https://github.com/raspberrypiexperiments/RaspberryPi-AstroBerry.git
```
```bash
cd RaspberryPi-AstroBerry
```
```
make install
```

Optional:

```bash
make install_updater
```

## Uninstallation

Uninstallation procedure:

```bash
make uninstall
```
```bash
cd ..
```
```bash
rm -rf RaspberryPi-AstroBerry
```

Optional:

```bash
make uninstall_updater
```

## License

MIT License

Copyright (c) 2022-2023 Marcin Sielski <marcin.sielski@gmail.com>
