"""Boundary and workflow tests; no real credentials, network or hosts required."""
import contextlib
import copy
import getpass
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.request

import dev_stack as ds


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.path = self.directory / 'profiles.json'
        self.profile = {'portainer': {'url': 'https://portainer.example.test:9443', 'control_environment': 'local', 'worker_environment': 'dev-host', 'credential_profile': 'pilot'}}

    def test_rejects_unsafe_inputs_without_echo(self):
        for kind, value in [('https', 'http://host'), ('https', 'https://user:secret@host'), ('https', 'https://host/path'), ('https', 'https://host:99999'), ('https', 'https://host?key=secret'), ('alias', '-oProxyCommand=bad'), ('remote_path', '/'), ('remote_path', '/srv/../etc'), ('workers', True), ('workers', 6), ('positive', 0), ('argv', 'sh -c bad'), ('argv', ['echo', '\n']), ('commit', 'main'), ('auth', 'oauth-token')]:
            with self.subTest(kind=kind, value=value):
                with self.assertRaises(ds.ConfigError) as error:
                    ds.validate_value(kind, value)
                self.assertNotIn('secret', str(error.exception))

    def test_cross_field_budget_and_paths(self):
        invalid = [
            {'capacity': {'initial_workers': 5, 'maximum_workers': 2}},
            {'capacity': {'initial_workers': 2, 'task_memory_gib': 8, 'aggregate_memory_gib': 4}},
            {'capacity': {'aggregate_memory_gib': 50, 'host_reserve_gib': 16, 'support_reserve_gib': 8}},
            {'access': {'mosh_udp_start': 60010, 'mosh_udp_end': 60000}},
            {'storage': {'control_root': '/data/live', 'backup_root': '/data/live/backup'}},
            {'portainer': {'control_environment': 'same', 'worker_environment': 'same'}},
        ]
        for profile in invalid:
            with self.subTest(profile=profile), self.assertRaises(ds.ConfigError):
                ds.validate_profile(profile)

    def test_unknown_secret_fields_and_schema_rejected(self):
        for document in [
            {'schema_version': True, 'profiles': {}},
            {'schema_version': 2, 'profiles': {}},
            {'schema_version': 1, 'profiles': {'pilot': {'portainer': {'api_key': 'sentinel-secret'}}}},
        ]:
            ds.save_document(self.path, document)
            with self.assertRaises(ds.ConfigError) as error:
                ds.load_document(self.path)
            self.assertNotIn('sentinel-secret', str(error.exception))
            self.assertEqual(json.loads(self.path.read_text()), document)

    def test_private_permissions_atomic_replace_and_roundtrip(self):
        document = {'schema_version': 1, 'profiles': {'pilot': self.profile, 'other': {}}}
        ds.save_document(self.path, document)
        if os.name == 'posix':
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(ds.load_document(self.path), document)
        with mock.patch.object(ds.os, 'replace', side_effect=OSError):
            with self.assertRaises(OSError):
                ds.save_document(self.path, {'new': 'data'})
        self.assertEqual(ds.load_document(self.path), document)
        self.assertEqual(list(self.directory.iterdir()), [self.path])

    @unittest.skipUnless(os.name == 'posix', 'POSIX permissions')
    def test_read_refuses_public_permissions(self):
        ds.save_document(self.path, {'schema_version': 1, 'profiles': {}})
        self.path.chmod(0o644)
        with self.assertRaises(ds.ConfigError):
            ds.load_document(self.path)

    def test_git_and_symlink_paths_refused(self):
        repo = self.directory / 'repo'
        repo.mkdir()
        (repo / '.git').mkdir()
        (repo / '.git' / 'HEAD').write_text('ref: refs/heads/main\n')
        with mock.patch.dict(os.environ, {'DEV_STACK_CONFIG_HOME': str(repo / 'local')}):
            with self.assertRaises(ds.ConfigError):
                ds.profiles_path()
        self.path.symlink_to(self.directory / 'target')
        with mock.patch.dict(os.environ, {'DEV_STACK_CONFIG_HOME': str(self.directory)}):
            with self.assertRaises(ds.ConfigError):
                ds.profiles_path()

    def test_empty_managed_git_guard_does_not_block_config(self):
        (self.directory / '.git').mkdir()
        with mock.patch.dict(os.environ, {'DEV_STACK_CONFIG_HOME': str(self.directory / 'config')}):
            self.assertEqual(ds.profiles_path(), self.directory / 'config' / 'profiles.json')

    def test_section_reconfiguration_preserves_other_data_and_clear(self):
        document = {'schema_version': 1, 'profiles': {'pilot': copy.deepcopy(self.profile), 'other': {'hosts': {'qnap_os': 'test-os'}}}}
        # Keep URL/names/profile, explicitly clear the optional CA path.
        document['profiles']['pilot']['portainer']['ca_bundle'] = '/old/ca.pem'
        with mock.patch.object(ds.sys.stdin, 'isatty', return_value=True), mock.patch('builtins.input', side_effect=['', '', '', '', '?']), contextlib.redirect_stdout(io.StringIO()):
            ds.configure(self.path, document, 'pilot', 'portainer')
        saved = ds.load_document(self.path)
        self.assertIsNone(saved['profiles']['pilot']['portainer']['ca_bundle'])
        self.assertEqual(saved['profiles']['other'], document['profiles']['other'])
        self.assertEqual(saved['profiles']['pilot']['portainer']['url'], self.profile['portainer']['url'])

    def test_interrupt_leaves_saved_profile_unchanged(self):
        document = {'schema_version': 1, 'profiles': {'pilot': self.profile}}
        ds.save_document(self.path, document)
        original = self.path.read_bytes()
        with mock.patch.object(ds.sys.stdin, 'isatty', return_value=True), mock.patch('builtins.input', side_effect=KeyboardInterrupt), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                ds.configure(self.path, document, 'pilot', 'portainer')
        self.assertEqual(self.path.read_bytes(), original)

    def test_doctor_is_offline_and_never_reads_keyring_by_default(self):
        with mock.patch.object(ds, 'resolve_secret') as secret, mock.patch.object(ds, 'check_portainer') as network, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(ds.doctor(self.profile, 'pilot'), 1)
        secret.assert_not_called()
        network.assert_not_called()
        self.assertIn('MISSING access.qnap_ssh', output.getvalue())
        self.assertNotIn(self.profile['portainer']['url'], output.getvalue())

    def test_credential_precedence_and_compatible_keyring_account(self):
        variables, service, account = ds.credential_spec(self.profile, 'different', 'portainer')
        self.assertEqual(service, 'portainer-deploy')
        self.assertEqual(account, 'pilot@https://portainer.example.test:9443')
        with mock.patch.dict(os.environ, {variables[0]: 'specific', variables[1]: 'generic'}, clear=True), mock.patch.object(ds, 'native_keyring') as vault:
            self.assertEqual(ds.resolve_secret(self.profile, 'different', 'portainer'), 'specific')
        vault.assert_not_called()

    def test_missing_native_keyring_never_prompts_or_writes(self):
        with mock.patch.object(ds, 'native_keyring', return_value=None), mock.patch.object(ds, 'secret_input') as prompt:
            with self.assertRaises(ds.ConfigError):
                ds.credentials(self.profile, 'pilot', 'portainer')
        prompt.assert_not_called()
        self.assertFalse(self.path.exists())

    def test_keyring_storage_no_plaintext_and_suppressed_error(self):
        keyring = mock.Mock()
        with mock.patch.object(ds, 'native_keyring', return_value=keyring), mock.patch.object(ds, 'secret_input', return_value='sentinel-secret'), contextlib.redirect_stdout(io.StringIO()) as output:
            ds.credentials(self.profile, 'pilot', 'portainer')
            keyring.set_password.assert_called_once_with('portainer-deploy', 'pilot@https://portainer.example.test:9443', 'sentinel-secret')
            keyring.set_password.side_effect = RuntimeError('sentinel-secret')
            with self.assertRaises(ds.ConfigError) as error:
                ds.credentials(self.profile, 'pilot', 'portainer')
        self.assertNotIn('sentinel-secret', output.getvalue() + str(error.exception))
        self.assertFalse(self.path.exists())

    def test_hidden_input_failure_is_not_echoed(self):
        with mock.patch.object(ds.sys.stdin, 'isatty', return_value=True), mock.patch.object(ds.getpass, 'getpass', side_effect=getpass.GetPassWarning):
            with self.assertRaises(ds.ConfigError):
                ds.secret_input('secret: ')

    def response_check(self, payload):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        opener = mock.Mock()
        opener.open.return_value = response
        return opener

    def good_endpoints(self):
        return [{'Name': 'local', 'Id': 1, 'Type': 1, 'Status': 1}, {'Name': 'dev-host', 'Id': 2, 'Type': 4, 'Status': 1, 'Edge': {'AsyncMode': False}}]

    def test_portainer_only_gets_endpoints(self):
        opener = self.response_check(self.good_endpoints())
        with mock.patch.object(ds.urllib.request, 'build_opener', return_value=opener), contextlib.redirect_stdout(io.StringIO()) as output:
            ds.check_portainer(self.profile, 'sentinel-secret')
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(request.full_url, 'https://portainer.example.test:9443/api/endpoints')
        self.assertEqual(opener.open.call_count, 1)
        self.assertNotIn('sentinel-secret', output.getvalue())

    def test_portainer_ambiguity_wrong_type_status_id_and_async_fail(self):
        for changes in [{'Type': 2}, {'Status': 2}, {'Id': 1}, {'Id': True}, {'Status': True}, {'AsyncMode': True}, {'Edge': None}, {'Edge': {'AsyncMode': 'false'}}, {'Edge': {'AsyncMode': True}}]:
            payload = self.good_endpoints()
            payload[1].update(changes)
            with self.subTest(changes=changes), mock.patch.object(ds.urllib.request, 'build_opener', return_value=self.response_check(payload)), self.assertRaises(ds.ConfigError):
                ds.check_portainer(self.profile, 'secret')
        payload = self.good_endpoints()
        payload.append(payload[1])
        with mock.patch.object(ds.urllib.request, 'build_opener', return_value=self.response_check(payload)), self.assertRaises(ds.ConfigError):
            ds.check_portainer(self.profile, 'secret')

    def test_http_failure_body_cannot_leak_credential(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError('https://host', 403, 'sentinel-secret', {}, io.BytesIO(b'sentinel-secret'))
        with mock.patch.object(ds.urllib.request, 'build_opener', return_value=opener), self.assertRaises(ds.ConfigError) as error:
            ds.check_portainer(self.profile, 'sentinel-secret')
        self.assertEqual(str(error.exception), 'Portainer HTTP 403; response body suppressed.')

    def test_redirect_rejected_before_followup(self):
        handler = ds.NoRedirect()
        request = urllib.request.Request('https://first.example', headers={'X-API-Key': 'secret'})
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code), self.assertRaises(ds.ConfigError):
                handler.redirect_request(request, None, code, 'redirect', {}, 'https://other.example')


if __name__ == '__main__':
    unittest.main()
