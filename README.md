# ZenPacks.daviswr.Cisco.IOS.CPU

ZenPack to model & monitor CPUs in a Cisco IOS device via CISCO-PROCESS-MIB

## Usage

This ZenPack overwrites the CPU monitoring template at the /Network/Cisco device class, but doesn't (yet) modify the modeler plugins configured there, so it's up to you to apply the `daviswr.snmp.CiscoCpuMap` modeler (and copy the monitoring template to the correct location[s] if your Cisco gear doesn't live in that device class).
