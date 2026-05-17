# Software Defined Networks: A Module for SIT202

A learning module for Deakin's SIT202 (Computer Networks and Communication)
covering Software Defined Networks (SDN), built as a 3.2HD submission.

## What's here

- **[module.md](module.md)** — the written module. Start here if you want
  to learn SDN.
- **[controller/sdn_demo_controller.py](controller/sdn_demo_controller.py)** —
  a working Ryu OpenFlow 1.3 controller that powers the practical
  demonstration. A learning switch with an optional ICMP-block rule that
  shows network behaviour can be changed by editing a Python file.
- **[lab-setup.md](lab-setup.md)** — how to reproduce the lab environment
  (Mininet + Ryu + Wireshark on Ubuntu 24.04 ARM, running in UTM on an
  Apple Silicon Mac).
- **[figures/](figures/)** — diagrams used in the written module.
- **[reflection.md](reflection.md)** — personal reflection on the project.

## Video tutorial

A walk-through of the practical demonstration, recorded for this module:
**[YouTube link here once uploaded]**

The video covers:
1. An empty OpenFlow switch with no rules and no controller.
2. Bringing the network to life by starting a Ryu controller.
3. Inspecting the flow table to see what the controller installed.
4. Watching the OpenFlow exchange between switch and controller in Wireshark.
5. Changing network behaviour by editing a Python file (the ICMP-block flourish).

## Quick start

If you just want to try the demo:

```bash
# Terminal A
source ~/ryu-env/bin/activate
ryu-manager controller/sdn_demo_controller.py

# Terminal B
sudo mn --topo single,3 --controller=remote --switch ovs,protocols=OpenFlow13
mininet> pingall
```

Full setup instructions for a clean environment are in [lab-setup.md](lab-setup.md).

## Author

Bill Zica, Deakin University Software Engineering, 2026.
Built for SIT202 3.2HD Collaborative Learning Initiative.