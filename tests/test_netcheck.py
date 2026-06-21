import unittest
import socket
import urllib.request
import urllib.error
import io
from concurrent.futures import TimeoutError
from unittest.mock import patch, MagicMock

# Import our library modules
from netcheck.utils.normalize import normalize_host, parse_line_to_raw_host_port
from netcheck.utils.range_expanders import expand_ip_range, expand_port_range
from netcheck.utils.cache import Cache
from netcheck.utils.timeout import run_with_timeout
from netcheck.utils.retry import with_retry, retry_call
from netcheck.cli import run_check_with_retry
from netcheck.modules.dns import dns_lookup
from netcheck.modules.tcp import check_tcp_connect
from netcheck.modules.http import check_http_status
from netcheck.modules.ssl import check_ssl_certificate
from netcheck.modules.ping import ping_host
from netcheck.modules.interfaces import get_network_interfaces, get_active_local_ip
from netcheck.mcp.tools import call_tool, TOOLS_LIST

class TestNetCheckUtilities(unittest.TestCase):
    def test_normalize_host(self):
        self.assertEqual(normalize_host("https://google.com/path?q=1"), "google.com")
        self.assertEqual(normalize_host("http://api.example.com:8443/v1"), "api.example.com")
        self.assertEqual(normalize_host("192.168.1.1:80"), "192.168.1.1")
        self.assertEqual(normalize_host("example.com"), "example.com")
        self.assertEqual(normalize_host(""), "")

    def test_parse_line_to_raw_host_port(self):
        self.assertEqual(parse_line_to_raw_host_port("http://192.168.1.1:8080/path"), ("192.168.1.1", "8080"))
        self.assertEqual(parse_line_to_raw_host_port("https://google.com/"), ("google.com", "443"))
        self.assertEqual(parse_line_to_raw_host_port("192.168.1.1-10 80"), ("192.168.1.1-10", "80"))
        self.assertEqual(parse_line_to_raw_host_port("[fe80::1]:80"), ("fe80::1", "80"))
        self.assertEqual(parse_line_to_raw_host_port("google.com,80,443"), ("google.com", "80,443"))
        self.assertEqual(parse_line_to_raw_host_port("google.com/path"), ("google.com", "80"))
        self.assertEqual(parse_line_to_raw_host_port(" # comment line "), ("", ""))

    def test_expand_ip_range(self):
        self.assertEqual(expand_ip_range("192.168.1.1"), ["192.168.1.1"])
        self.assertEqual(expand_ip_range("192.168.1.1-3"), ["192.168.1.1", "192.168.1.2", "192.168.1.3"])
        # CIDR /30 has 2 usable host IPs
        self.assertEqual(expand_ip_range("192.168.1.0/30"), ["192.168.1.1", "192.168.1.2"])

    def test_expand_port_range(self):
        self.assertEqual(expand_port_range("80"), [80])
        self.assertEqual(expand_port_range("80,443"), [80, 443])
        self.assertEqual(expand_port_range("8000-8003"), [8000, 8001, 8002, 8003])
        self.assertEqual(expand_port_range("80,8000-8002,443"), [80, 8000, 8001, 8002, 443])

    def test_cache_ttl(self):
        cache = Cache(default_ttl=0.1)
        cache.set("key", "val")
        self.assertEqual(cache.get("key"), "val")
        import time
        time.sleep(0.15)
        self.assertIsNone(cache.get("key"))

    def test_timeout_mechanism(self):
        def slow_func():
            import time
            time.sleep(0.5)
            return "done"
            
        # Should complete if timeout is high
        self.assertEqual(run_with_timeout(1.0, slow_func), "done")
        
        # Should raise TimeoutError if timeout is low
        with self.assertRaises(TimeoutError):
            run_with_timeout(0.1, slow_func)

    def test_retry_mechanism(self):
        calls = 0
        @with_retry(retries=3, delay=0.01)
        def fail_twice():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("temporary error")
            return "success"
            
        self.assertEqual(fail_twice(), "success")
        self.assertEqual(calls, 3)

class TestNetCheckModules(unittest.TestCase):
    @patch("socket.getaddrinfo")
    def test_dns_lookup_success(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ]
        
        res = dns_lookup("example.com")
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("93.184.216.34", res["metadata"]["ips"])

    @patch("socket.getaddrinfo")
    def test_dns_lookup_failure(self, mock_getaddrinfo):
        mock_getaddrinfo.side_effect = socket.gaierror("dns failure")
        res = dns_lookup("nonexistent.invalid")
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "FAILED")

    @patch("socket.socket")
    @patch("netcheck.modules.tcp.dns_lookup")
    def test_tcp_connect_success(self, mock_dns, mock_socket):
        mock_dns.return_value = {
            "success": True,
            "metadata": {"ips": ["93.184.216.34"]}
        }
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        
        res = check_tcp_connect("example.com", 80)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "SUCCESS")

    @patch("urllib.request.urlopen")
    def test_http_status_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.geturl.return_value = "http://example.com"
        mock_resp.info.return_value = {"Content-Length": "100"}
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        res = check_http_status("http://example.com")
        self.assertTrue(res["success"])
        self.assertEqual(res["metadata"]["status_code"], 200)

    @patch("urllib.request.urlopen")
    def test_http_status_failure(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://example.com", 404, "Not Found", {}, None
        )
        
        res = check_http_status("http://example.com")
        self.assertFalse(res["success"])
        self.assertEqual(res["metadata"]["status_code"], 404)

    def test_interfaces_listing(self):
        res = get_network_interfaces()
        self.assertTrue(res["success"])
        self.assertIn("primary_ip", res["metadata"])
        self.assertIn("interfaces", res["metadata"])

class TestMCPIntegration(unittest.TestCase):
    def test_mcp_tools_list(self):
        tool_names = [t["name"] for t in TOOLS_LIST]
        self.assertIn("check_tcp_connectivity", tool_names)
        self.assertIn("check_http_status", tool_names)
        self.assertIn("get_network_interfaces", tool_names)

    @patch("netcheck.mcp.tools.dns_lookup")
    def test_mcp_tool_call(self, mock_dns):
        mock_dns.return_value = {
            "success": True,
            "status": "SUCCESS",
            "metadata": {"ips": ["1.1.1.1"]}
        }
        res = call_tool("dns_lookup", {"host": "one.one.one.one"})
        self.assertIn("content", res)
        # Verify content text is a valid json matching success output
        content_text = res["content"][0]["text"]
        parsed = json_data = json_loads_or_none(content_text)
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed["success"])

def json_loads_or_none(s):
    import json
    try:
        return json.loads(s)
    except Exception:
        return None

class TestFormatterOutputs(unittest.TestCase):
    def setUp(self):
        # Sample metadata representing the 5 different checks
        self.interfaces_result = {
            "target": "interfaces",
            "status": "SUCCESS",
            "success": True,
            "metadata": {
                "primary_ip": "192.168.1.5",
                "gateway_ip": "192.168.1.1",
                "gateway_dev": "eth0",
                "public_ip": "8.8.8.8",
                "all_interfaces_shown": False,
                "interfaces": {
                    "eth0": {
                        "ipv4": ["192.168.1.5"],
                        "ipv6": ["fe80::1"],
                        "status": "UP"
                    }
                }
            }
        }
        
        self.dns_result = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "latency_ms": 12.5,
            "metadata": {
                "resolved_host": "google.com",
                "ips": ["142.250.190.46"],
                "aliases": ["www.google.com"],
                "reverse_dns": "dns.google"
            }
        }
        
        self.http_result = {
            "target": "http://example.com",
            "status": "SUCCESS",
            "success": True,
            "latency_ms": 45.2,
            "metadata": {
                "status_code": 200,
                "redirect_url": None,
                "size_bytes": 1256,
                "headers": {"content-type": "text/html"}
            }
        }
        
        self.ssl_result = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "latency_ms": 110.0,
            "metadata": {
                "subject": {"commonName": "google.com"},
                "issuer": {"organizationName": "Google Trust Services"},
                "valid_from": "2026-01-01",
                "valid_until": "2026-12-31",
                "days_until_expiry": 200,
                "expired": False,
                "sans": ["google.com", "www.google.com"]
            }
        }
        
        self.ping_result = {
            "target": "8.8.8.8",
            "status": "SUCCESS",
            "success": True,
            "latency_ms": 15.1,
            "metadata": {
                "host": "8.8.8.8",
                "packets_sent": 4,
                "packets_received": 4,
                "packet_loss_pct": 0.0,
                "min_rtt_ms": 14.0,
                "avg_rtt_ms": 15.0,
                "max_rtt_ms": 16.0
            }
        }

    def test_json_formatting(self):
        from netcheck.utils.formatters import format_json
        import json
        
        # Test Interfaces JSON
        res_json = json.loads(format_json([self.interfaces_result]))
        self.assertEqual(res_json["type"], "interfaces")
        self.assertEqual(res_json["primary_ip"], "192.168.1.5")
        
        # Test DNS JSON
        res_json = json.loads(format_json([self.dns_result]))
        self.assertEqual(res_json["type"], "dns")
        self.assertEqual(res_json["target"], "google.com")
        self.assertEqual(res_json["resolved_host"], "google.com")
        
        # Test HTTP JSON
        res_json = json.loads(format_json([self.http_result]))
        self.assertEqual(res_json["type"], "http")
        self.assertEqual(res_json["status_code"], 200)
        
        # Test SSL JSON
        res_json = json.loads(format_json([self.ssl_result]))
        self.assertEqual(res_json["type"], "ssl")
        self.assertEqual(res_json["days_until_expiry"], 200)
        
        # Test Ping JSON
        res_json = json.loads(format_json([self.ping_result]))
        self.assertEqual(res_json["type"], "ping")
        self.assertEqual(res_json["packet_loss_pct"], 0.0)

    def test_csv_formatting(self):
        from netcheck.utils.formatters import format_csv
        import csv
        
        # Test Interfaces CSV
        csv_out = format_csv([self.interfaces_result])
        reader = csv.reader(io.StringIO(csv_out))
        rows = list(reader)
        self.assertEqual(rows[0], ["Interface", "IPv4", "IPv6", "Status", "Default_Gateway", "Public_IP"])
        self.assertEqual(rows[1][0], "eth0")
        
        # Test DNS CSV
        csv_out = format_csv([self.dns_result])
        reader = csv.reader(io.StringIO(csv_out))
        rows = list(reader)
        self.assertEqual(rows[0], ["Target", "Resolved_Host", "IP", "Reverse_DNS", "Success", "Latency_MS", "Error"])
        self.assertEqual(rows[1][1], "google.com")
        
        # Test HTTP CSV
        csv_out = format_csv([self.http_result])
        reader = csv.reader(io.StringIO(csv_out))
        rows = list(reader)
        self.assertEqual(rows[0], ["Target", "Status_Code", "Redirect_URL", "Size_Bytes", "Success", "Latency_MS", "Error"])
        self.assertEqual(rows[1][1], "200")
        
        # Test SSL CSV
        csv_out = format_csv([self.ssl_result])
        reader = csv.reader(io.StringIO(csv_out))
        rows = list(reader)
        self.assertEqual(rows[0], ["Target", "Subject_CN", "Issuer_O", "Valid_From", "Valid_Until", "Days_Until_Expiry", "Expired", "Success", "Latency_MS", "Error"])
        self.assertEqual(rows[1][1], "google.com")
        self.assertEqual(rows[1][2], "Google Trust Services")
        
        # Test Ping CSV
        csv_out = format_csv([self.ping_result])
        reader = csv.reader(io.StringIO(csv_out))
        rows = list(reader)
        self.assertEqual(rows[0], ["Target", "Host", "Packets_Sent", "Packets_Received", "Packet_Loss_Pct", "Min_RTT_MS", "Avg_RTT_MS", "Max_RTT_MS", "Success", "Latency_MS", "Error"])
        self.assertEqual(rows[1][4], "0.0")

    def test_xml_formatting(self):
        from netcheck.utils.formatters import format_xml
        import xml.etree.ElementTree as ET
        
        # Test Interfaces XML
        xml_out = format_xml([self.interfaces_result])
        root = ET.fromstring(xml_out)
        self.assertEqual(root.tag, "network_interfaces")
        self.assertEqual(root.find("primary_ip").text, "192.168.1.5")
        
        # Test DNS XML
        xml_out = format_xml([self.dns_result])
        root = ET.fromstring(xml_out)
        self.assertEqual(root.tag, "dns_lookup")
        self.assertEqual(root.find("resolved_host").text, "google.com")
        
        # Test HTTP XML
        xml_out = format_xml([self.http_result])
        root = ET.fromstring(xml_out)
        self.assertEqual(root.tag, "http_check")
        self.assertEqual(root.find("status_code").text, "200")
        
        # Test SSL XML
        xml_out = format_xml([self.ssl_result])
        root = ET.fromstring(xml_out)
        self.assertEqual(root.tag, "ssl_check")
        self.assertEqual(root.find("subject_cn").text, "google.com")
        
        # Test Ping XML
        xml_out = format_xml([self.ping_result])
        root = ET.fromstring(xml_out)
        self.assertEqual(root.tag, "ping_check")
        self.assertEqual(root.find("packet_loss_pct").text, "0.0")

if __name__ == "__main__":
    unittest.main()
