#!/usr/bin/bash
PATH=$PATH:/usr/bin
qpid-config --durable add queue agie_inbound_control
qpid-config --durable add queue agie_inbound_data
qpid-config --durable add exchange direct agie_inbound -a localhost:5672
qpid-config --durable bind agie_inbound agie_inbound_control agie_inbound_control
qpid-config --durable add exchange direct agie_inbound_d -a localhost:5672
qpid-config --durable bind agie_inbound_d agie_inbound_data agie_inbound_data
qpid-config --durable add exchange direct agie_outbound_d -a localhost:5672
qpid-config --durable add exchange direct agie_alt -a localhost:5672
qpid-config --durable bind agie_alt agie_inbound_data agie_data_net1
qpid-config --durable bind agie_alt agie_inbound_data agie_data_net2
qpid-config --durable add queue app1
qpid-config --durable add queue app2
qpid-config --durable bind agie_inbound_d  agie_inbound_data app1
qpid-config --durable bind agie_inbound_d  agie_inbound_data app2
