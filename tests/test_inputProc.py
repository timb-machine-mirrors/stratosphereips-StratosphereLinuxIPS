import pytest
from tests.module_factory import ModuleFactory
from io import StringIO
from unittest.mock import patch
from slips_files.core.input import Input
import shutil
import os
import json


@pytest.mark.parametrize(
    'input_type,input_information',
    [('pcap', 'dataset/test12-icmp-portscan.pcap')],
)
def test_handle_pcap_and_interface(
    input_type, input_information, mock_rdb
):
    # no need to test interfaces because in that case read_zeek_files runs in a loop and never returns
    input = ModuleFactory().create_inputProcess_obj(input_information, input_type, mock_rdb)
    input.zeek_pid = 'False'
    input.is_zeek_tabs = False
    assert input.handle_pcap_and_interface() is True
    # delete the zeek logs created
    shutil.rmtree(input.zeek_dir)


@pytest.mark.parametrize(
    'zeek_dir, is_tabs',
    [
        ('dataset/test10-mixed-zeek-dir/', False), # tabs
        ('dataset/test9-mixed-zeek-dir/', True), # json
    ],
)
def test_is_growing_zeek_dir(
     zeek_dir: str, is_tabs: bool,  mock_rdb
):
    input = ModuleFactory().create_inputProcess_obj(zeek_dir, 'zeek_folder', mock_rdb)
    mock_rdb.get_all_zeek_file.return_value = [os.path.join(zeek_dir, 'conn.log')]

    assert input.read_zeek_folder() is True



@pytest.mark.parametrize(
    'path, expected_val',
    [
        ('dataset/test10-mixed-zeek-dir/conn.log', True), # tabs
        ('dataset/test9-mixed-zeek-dir/conn.log', False), # json
    ],
)
def test_is_zeek_tabs_file(path: str, expected_val: bool, mock_rdb):
    input = ModuleFactory().create_inputProcess_obj(path, 'zeek_folder', mock_rdb)
    assert input.is_zeek_tabs_file(path) == expected_val


@pytest.mark.parametrize(
    'input_information,expected_output',
    [
        ('dataset/test10-mixed-zeek-dir/conn.log', True), #tabs
        ('dataset/test9-mixed-zeek-dir/conn.log', True), # json
        ('dataset/test9-mixed-zeek-dir/conn', False), # json
        ('dataset/test9-mixed-zeek-dir/x509.log', False), # json
    ],
)
def test_handle_zeek_log_file(
    input_information, mock_rdb, expected_output
):
    input = ModuleFactory().create_inputProcess_obj(input_information, 'zeek_log_file', mock_rdb)
    assert input.handle_zeek_log_file() == expected_output


@pytest.mark.skipif(
    'nfdump' not in shutil.which('nfdump'), reason='nfdump is not installed'
)
@pytest.mark.parametrize(
    'input_information', [('dataset/test1-normal.nfdump')]
)
def test_handle_nfdump(
    input_information, mock_rdb
):
    input = ModuleFactory().create_inputProcess_obj(input_information, 'nfdump', mock_rdb)
    assert input.handle_nfdump() is True



@pytest.mark.parametrize(
    'input_type,input_information',
    [
        ('binetflow', 'dataset/test2-malicious.binetflow'),
        ('binetflow', 'dataset/test5-mixed.binetflow'),
    ],
)
#                                                           ('binetflow','dataset/test3-mixed.binetflow'),
#                                                           ('binetflow','dataset/test4-malicious.binetflow'),
def test_handle_binetflow(
    input_type, input_information, mock_rdb
):
    input = ModuleFactory().create_inputProcess_obj(input_information, input_type, mock_rdb)
    with patch.object(input, 'get_flows_number', return_value=5):
        assert input.handle_binetflow() is True


@pytest.mark.parametrize(
    'input_information',
    [('dataset/test6-malicious.suricata.json')],
)
def test_handle_suricata(
    input_information, mock_rdb
):
    inputProcess = ModuleFactory().create_inputProcess_obj(input_information, 'suricata', mock_rdb)
    assert inputProcess.handle_suricata() is True

@pytest.mark.parametrize(
    'line_type, line',
    [
        ('zeek', '{"ts":271.102532,"uid":"CsYeNL1xflv3dW9hvb","id.orig_h":"10.0.2.15","id.orig_p":59393,'
                 '"id.resp_h":"216.58.201.98","id.resp_p":443,"proto":"udp","duration":0.5936019999999758,'
                 '"orig_bytes":5219,"resp_bytes":5685,"conn_state":"SF","missed_bytes":0,"history":"Dd",'
                 '"orig_pkts":9,"orig_ip_bytes":5471,"resp_pkts":10,"resp_ip_bytes":5965}'),
        ('suricata', '{"timestamp":"2021-06-06T15:57:37.272281+0200","flow_id":2054715089912378,"event_type":"flow",'
                     '"src_ip":"193.46.255.92","src_port":49569,"dest_ip":"192.168.1.129","dest_port":8014,'
                     '"proto":"TCP","flow":{"pkts_toserver":2,"pkts_toclient":2,"bytes_toserver":120,"bytes_toclient":120,"start":"2021-06-07T15:45:48.950842+0200","end":"2021-06-07T15:45:48.951095+0200","age":0,"state":"closed","reason":"shutdown","alerted":false},"tcp":{"tcp_flags":"16","tcp_flags_ts":"02","tcp_flags_tc":"14","syn":true,"rst":true,"ack":true,"state":"closed"},"host":"stratosphere.org"}'),
        ('argus', '2019/04/05 16:15:09.194268,0.031142,udp,10.8.0.69,8278,  <->,8.8.8.8,53,CON,0,0,2,186,64,1,'),
     ],
)

def test_read_from_stdin(line_type: str, line: str, mock_rdb):
    # slips supports reading zeek json conn.log only using stdin,
    # tabs aren't supported
    input = ModuleFactory().create_inputProcess_obj(
        line_type, 'stdin', mock_rdb, line_type=line_type,
        )
    with patch.object(input, 'stdin', return_value=[line, 'done\n']):
        # this function will give the line to profiler
        assert input.read_from_stdin()
        line_sent : dict = input.profiler_queue.get()
        # in case it's a zeek line, it gets sent as a dict
        expected_received_line = json.loads(line) if line_type is 'zeek' else line
        assert line_sent['line']['data'] == expected_received_line
        assert line_sent['line']['line_type'] == line_type
        assert line_sent['input_type'] == 'stdin'






