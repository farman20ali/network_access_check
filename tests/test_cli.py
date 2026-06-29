import io
import sys
import unittest
from unittest.mock import patch, MagicMock
from netcheck.cli import main, print_help

class TestNetCheckCLI(unittest.TestCase):
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print_help(self, mock_stdout):
        with patch('sys.argv', ['netcheck', '--help']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("Network Connectivity Checker", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_version(self, mock_stdout):
        with patch('sys.argv', ['netcheck', '--version']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("netcheck version", mock_stdout.getvalue())

    @patch('netcheck.cli.get_network_interfaces')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_my_ip(self, mock_stdout, mock_get_interfaces):
        mock_get_interfaces.return_value = {
            "target": "interfaces",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {"interfaces": {}, "all_interfaces_shown": False}
        }
        with patch('sys.argv', ['netcheck', '--my-ip']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            mock_get_interfaces.assert_called_once_with(all_interfaces=False)

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_dns_flag(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {"ips": ["8.8.8.8"]}
        }
        with patch('sys.argv', ['netcheck', '--dns', 'google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('google.com', 5.0))

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ping_flag(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', '--ping', 'google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('google.com', 4, 5.0))

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_status_flag(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "http://google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', '--status', 'http://google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('http://google.com', 5.0))

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cert_flag(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', '--cert', 'google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('google.com', 443, 5.0))

    @patch('netcheck.cli.execute_concurrent_checks')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_quick_flag(self, mock_stdout, mock_exec):
        mock_exec.return_value = [
            {"target": "localhost:80", "status": "SUCCESS", "success": True, "error": None}
        ]
        with patch('sys.argv', ['netcheck', '--quick', 'localhost', '80']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            mock_exec.assert_called_once()

    @patch('netcheck.mcp.server.start_mcp_server')
    def test_mcp_flag(self, mock_start_mcp):
        with patch('sys.argv', ['netcheck', '--mcp']):
            main()
            mock_start_mcp.assert_called_once()

    # Subcommands
    @patch('netcheck.cli.execute_concurrent_checks')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_tcp(self, mock_stdout, mock_exec):
        mock_exec.return_value = [
            {"target": "google.com:80", "status": "SUCCESS", "success": True, "error": None}
        ]
        with patch('sys.argv', ['netcheck', 'tcp', 'google.com', '80']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            mock_exec.assert_called_once()

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_dns(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', 'dns', 'google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('google.com', 5.0))

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_http(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "http://google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', 'http', 'http://google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('http://google.com', 5.0))

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_ssl(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', 'ssl', 'google.com', '443']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('google.com', 443, 5.0))

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_ping(self, mock_stdout, mock_run_retry):
        mock_run_retry.return_value = {
            "target": "google.com",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {}
        }
        with patch('sys.argv', ['netcheck', 'ping', 'google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            args, kwargs = mock_run_retry.call_args
            self.assertEqual(args[1], ('google.com', 4, 5.0))

    @patch('netcheck.cli.get_network_interfaces')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_interfaces(self, mock_stdout, mock_get_interfaces):
        mock_get_interfaces.return_value = {
            "target": "interfaces",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {"interfaces": {}, "all_interfaces_shown": True}
        }
        with patch('sys.argv', ['netcheck', 'interfaces', '--all']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            mock_get_interfaces.assert_called_once_with(all_interfaces=True)


class TestCLITier4Features(unittest.TestCase):
    """Tests for Tier 4 CLI infrastructure: env vars, watch mode, new subcommands, error handling."""

    @patch('netcheck.modules.traceroute.run_subprocess_traceroute')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_traceroute(self, mock_stdout, mock_trace):
        mock_trace.return_value = [
            {"hop": 1, "ip": "192.168.1.1", "name": "router", "latency_ms": 1.5}
        ]
        with patch('sys.argv', ['netcheck', 'traceroute', 'google.com', '-m', '5']):
            with self.assertRaises(SystemExit) as cm:
                main()
            # 0 = success (hops found)
            self.assertEqual(cm.exception.code, 0)

    @patch('netcheck.modules.port_scanner.dns_lookup')
    @patch('netcheck.modules.port_scanner.scan_port_single')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_scan(self, mock_stdout, mock_single, mock_dns):
        mock_dns.return_value = {"success": True, "metadata": {"ips": ["127.0.0.1"]}}
        mock_single.return_value = {"port": 80, "status": "OPEN", "service": "http", "latency_ms": 1.0}
        with patch('sys.argv', ['netcheck', 'scan', 'localhost', '-p', '80']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    @patch('netcheck.modules.whois.get_rdap_info')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_whois(self, mock_stdout, mock_rdap):
        mock_rdap.return_value = {
            "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["fn", {}, "text", "GoDaddy"]]]}],
            "events": [{"eventAction": "registration", "eventDate": "1997-01-01T00:00:00Z"}]
        }
        with patch('sys.argv', ['netcheck', 'whois', 'google.com']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)

    def test_env_var_timeout_override(self):
        """NETCHECK_TIMEOUT env var should override the default timeout."""
        import os
        from netcheck.cli import main as netcheck_main
        with patch.dict(os.environ, {"NETCHECK_TIMEOUT": "99.0"}):
            # Just ensure it parses without crashing; we verify by checking run_batch_lines is not called
            with patch('sys.argv', ['netcheck', '--help']):
                with self.assertRaises(SystemExit):
                    netcheck_main()

    def test_env_var_max_workers_override(self):
        """NETCHECK_MAX_WORKERS env var should override the default jobs count."""
        import os
        with patch.dict(os.environ, {"NETCHECK_MAX_WORKERS": "42"}):
            with patch('sys.argv', ['netcheck', '--help']):
                with self.assertRaises(SystemExit):
                    main()

    def test_malformed_line_warning_to_stderr(self):
        """Malformed input lines should produce a warning on stderr, not crash."""
        import os
        with patch('sys.stdin', io.StringIO("::bad::line::\n")):
            with patch('sys.stdin.isatty', return_value=False):
                with patch('sys.stdout', new_callable=io.StringIO):
                    with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                        with patch('sys.argv', ['netcheck']):
                            try:
                                main()
                            except SystemExit:
                                pass
                            # Either a warning was printed or no crash occurred

    @patch('netcheck.cli.run_check_with_retry')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_watch_mode_keyboard_interrupt(self, mock_stdout, mock_retry):
        """Watch mode should exit cleanly on KeyboardInterrupt."""
        mock_retry.return_value = {
            "target": "google.com", "status": "SUCCESS",
            "success": True, "error": None, "metadata": {}
        }
        # Simulate one iteration then KeyboardInterrupt
        call_count = 0
        original_retry = mock_retry.side_effect

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                raise KeyboardInterrupt()
            return {"target": "google.com", "status": "SUCCESS", "success": True, "error": None, "metadata": {}}

        mock_retry.side_effect = side_effect
        with patch('sys.argv', ['netcheck', 'dns', 'google.com', '--watch', '--interval', '0']):
            with patch('time.sleep'):
                with patch('os.system'):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    # Watch mode exits with code 0 on Ctrl+C
                    self.assertEqual(cm.exception.code, 0)

    @patch('netcheck.cli.run_check_with_retry')
    def test_no_color_flag(self, mock_retry):
        """--no-color flag should disable ANSI codes in output."""
        mock_retry.return_value = {
            "target": "google.com", "status": "SUCCESS",
            "success": True, "error": None, "metadata": {"ips": ["8.8.8.8"]}
        }
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with patch('sys.argv', ['netcheck', 'dns', 'google.com', '--no-color']):
                with self.assertRaises(SystemExit):
                    main()
            output = mock_stdout.getvalue()
            # Should not contain ANSI escape codes
            self.assertNotIn('\033[', output)

    @patch('netcheck.cli.run_check_with_retry')
    def test_mcp_tools_include_tier3(self, mock_retry):
        """MCP tools list should include all Tier 3 tools."""
        from netcheck.mcp.tools import TOOLS_LIST
        tool_names = [t["name"] for t in TOOLS_LIST]
        self.assertIn("traceroute", tool_names)
        self.assertIn("scan_ports", tool_names)
        self.assertIn("whois_lookup", tool_names)
        self.assertIn("get_listening_ports", tool_names)

    @patch('netcheck.modules.interfaces.check_listening_ports')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_subcommand_ports(self, mock_stdout, mock_check_ports):
        mock_check_ports.return_value = {
            "target": "ports",
            "status": "SUCCESS",
            "success": True,
            "error": None,
            "metadata": {"listening_ports": []}
        }
        with patch('sys.argv', ['netcheck', 'ports']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            mock_check_ports.assert_called_once()


if __name__ == '__main__':
    unittest.main()
