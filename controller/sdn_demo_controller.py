

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types


class SDNDemoController(app_manager.RyuApp):
    """A simple L2 learning switch with optional ICMP filtering."""

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # Flip this to True to see the ICMP block flourish in action.
    BLOCK_ICMP_DEMO = False

    def __init__(self, *args, **kwargs):
        super(SDNDemoController, self).__init__(*args, **kwargs)
        # Per-switch MAC learning table: {dpid: {mac: port}}
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Runs once, when a switch first connects to this controller.
        We install a single low-priority "table-miss" rule that sends any
        unmatched packet to the controller, so we can learn from it.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Priority 0, match anything, action: send to controller.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, priority=0, match=match, actions=actions)

        self.logger.info("Switch %s connected. Table-miss rule installed.",
                         datapath.id)

        # Optional flourish: drop ICMP between 10.0.0.1 and 10.0.0.3.
        # Higher priority than the L2 learning rules, so it wins.
        if self.BLOCK_ICMP_DEMO:
            self.install_icmp_block(datapath, '10.0.0.1', '10.0.0.3')
            self.install_icmp_block(datapath, '10.0.0.3', '10.0.0.1')
            self.logger.info("ICMP block installed: h1 <-> h3 cannot ping.")

    def install_icmp_block(self, datapath, src_ip, dst_ip):
        """Install a high-priority drop rule for ICMP between two hosts."""
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            eth_type=0x0800,   # IPv4
            ip_proto=1,        # ICMP
            ipv4_src=src_ip,
            ipv4_dst=dst_ip,
        )
        # Empty action list = drop the packet.
        self.add_flow(datapath, priority=100, match=match, actions=[])

    def add_flow(self, datapath, priority, match, actions):
        """Wrap the OpenFlow boilerplate for installing one rule."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Called every time a switch sees a packet with no matching rule.
        Learn where the source MAC is reachable, then either send the
        packet out the known port for the destination, or flood it if
        we haven't seen that destination yet.
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP topology-discovery frames.
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        src = eth.src
        dst = eth.dst
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Learn: the source MAC is reachable via in_port.
        self.mac_to_port[dpid][src] = in_port

        # Look up where the destination MAC lives, or flood.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # If we know the destination, install a rule so we don't have
        # to be asked again for this flow.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(
                in_port=in_port, eth_src=src, eth_dst=dst)
            self.add_flow(datapath, priority=1, match=match, actions=actions)

        # Send the original packet on its way.
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=msg.data,
        )
        datapath.send_msg(out)