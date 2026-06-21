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

if __name__ == '__main__':
    unittest.main()
