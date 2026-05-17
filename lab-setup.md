# Lab Setup

Reproducible steps for the Mininet + Ryu + Wireshark environment used in
this module. Tested on Ubuntu 24.04 ARM64 running in UTM on an Apple
Silicon Mac (M1).

## Prerequisites

- Apple Silicon Mac (or any host capable of running Ubuntu 24.04 ARM64).
- UTM 4.x or VirtualBox.
- Ubuntu 24.04 Desktop ARM64 ISO from `cdimage.ubuntu.com/releases/24.04/release/`.
- VM allocated at least 2 CPUs, 4 GB RAM, 30 GB disk.

## 1. System packages

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch wireshark tshark \
    git curl build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libncurses-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
sudo usermod -aG wireshark $USER
```

When the Wireshark installer asks whether non-root users can capture
packets, answer **Yes**. Log out and back in for the group change to apply.

## 2. Python 3.9 via pyenv

Ryu 4.34 is the last release, has been unmaintained since 2020, and does
not work on Python 3.10 or later because of changes in `eventlet`. Ubuntu
24.04 ships Python 3.12 by default, so we install 3.9 alongside it.

```bash
curl -fsSL https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
exec $SHELL

pyenv install 3.9.19
```

## 3. Ryu in a venv

```bash
pyenv shell 3.9.19
python -m venv ~/ryu-env
source ~/ryu-env/bin/activate
pip install "pip<23"
pip install "setuptools<58" "wheel<0.40"
pip install --no-build-isolation ryu==4.34 eventlet==0.30.2
```

Verify:
```bash
ryu-manager --version
# Should print: ryu-manager 4.34
```

The pinned versions (`pip<23`, `setuptools<58`, `eventlet==0.30.2`) are
required. Each addresses a specific incompatibility between Ryu and
modern Python tooling. Skipping any of them produces a different error.

## 4. Run the demo

In two terminals:

```bash
# Terminal A
source ~/ryu-env/bin/activate
cd path/to/sit202-sdn-module
ryu-manager controller/sdn_demo_controller.py
```

```bash
# Terminal B
sudo mn --topo single,3 --controller=remote --switch ovs,protocols=OpenFlow13
mininet> pingall
```

Expect `0% dropped`. Edit `BLOCK_ICMP_DEMO = True` in the controller
script and restart Ryu to see the ICMP-block flourish (h1 and h3 can no
longer ping each other, h2 is unaffected).