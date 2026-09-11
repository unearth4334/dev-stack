#!/usr/bin/env python3
"""Collect private pilot configuration; optionally check Portainer without deploying."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path, PurePosixPath
import re
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import warnings

ROOT = Path(__file__).resolve().parent.parent
# key: (prompt, validator, suggested value). None means an unanswered inventory item.
FIELDS = {
    'portainer': {
        'url': ('Portainer HTTPS origin', 'https', None),
        'control_environment': ('Exact QNAP environment name', 'text', 'local'),
        'worker_environment': ('Exact dev-host environment name', 'text', 'dev-host'),
        'credential_profile': ('Portainer deploy credential profile name', 'name', 'pilot'),
        'ca_bundle': ('Local CA bundle path (optional; ? selects system trust)', 'local_file', None),
    },
    'access': {
        'qnap_ssh': ('QNAP SSH config alias (on this workstation)', 'alias', None),
        'dev_host_ssh': ('dev-host SSH config alias (on this workstation)', 'alias', None),
        'controller_worker_ssh': ('dev-host service SSH alias (as configured on QNAP)', 'alias', None),
        'private_route': ('Private route (VPN/LAN name or description)', 'text', None),
        'phone_os': ('Phone OS and version', 'text', None),
        'termius_version': ('Termius version', 'text', None),
        'mosh_udp_start': ('First private mosh UDP port', 'port', 60000),
        'mosh_udp_end': ('Last private mosh UDP port', 'port', 60010),
    },
    'hosts': {
        'dev_host_os': ('dev-host OS/version (unknown is OK)', 'text', None),
        'qnap_os': ('QNAP OS/version', 'text', None),
        'qnap_arch': ('QNAP CPU architecture', 'text', None),
        'qnap_available_ram_gib': ('QNAP RAM available for pilot, GiB', 'positive', None),
        'dev_host_free_disk_gib': ('dev-host free workspace disk, GiB', 'positive', None),
    },
    'storage': {
        'workspace_root': ('Absolute workspace root on dev-host', 'remote_path', None),
        'control_root': ('Absolute control-state root on QNAP', 'remote_path', None),
        'results_root': ('Absolute private results root on QNAP', 'remote_path', None),
        'backup_root': ('Absolute backup destination on QNAP (separate from live data)', 'remote_path', None),
        'retention_days': ('Captured artifact retention in days', 'positive', 30),
        'minimum_free_disk_gib': ('Stop admissions below free disk GiB', 'positive', 20),
    },
    'agents': {
        'codex_auth': ('Codex authentication: subscription or api', 'auth', None),
        'claude_auth': ('Claude authentication: subscription or api', 'auth', None),
        'git_auth': ('Fixture Git authentication: public, ssh or https-token', 'git_auth', None),
    },
    'fixture': {
        'repository': ('Trusted fixture repository URL (no credentials)', 'git_url', None),
        'base_commit': ('Fixture immutable base commit (40 or 64 hex characters)', 'commit', None),
        'verification_argv': ('Fixture check as JSON argv, e.g. ["python3","-m","unittest"]', 'argv', None),
        'needs_container_builds': ('Fixture requires Docker builds: yes or no', 'yes_no', None),
        'allowed_egress': ('Approved outbound hosts as JSON list (no wildcard)', 'hosts', None),
    },
    'capacity': {
        'initial_workers': ('Initial concurrent workers', 'workers', 2),
        'maximum_workers': ('Maximum pilot workers', 'workers', 5),
        'task_memory_gib': ('Ordinary task RAM limit, GiB', 'positive', 4),
        'task_cpus': ('Ordinary task CPU quota', 'positive', 2),
        'aggregate_memory_gib': ('Aggregate task RAM allowance including sidecars, GiB', 'positive', 40),
        'host_reserve_gib': ('Host/existing-services RAM reserve, GiB', 'positive', 16),
        'support_reserve_gib': ('Support/headroom RAM reserve, GiB', 'positive', 8),
        'heavy_builds': ('Maximum simultaneous heavy builds', 'positive', 1),
        'task_deadline_minutes': ('Active-work budget per attempt, minutes (excludes quota/input waits; not session lifetime)', 'positive', 120),
    },
}
OPTIONAL = {('portainer', 'ca_bundle')}
NATIVE_BACKENDS = {
    'keyring.backends.SecretService', 'keyring.backends.kwallet',
    'keyring.backends.libsecret', 'keyring.backends.macOS', 'keyring.backends.Windows',
}


class ConfigError(Exception):
    pass


def validate_value(kind, value):
    if value is None:
        return None
    if kind in {'positive', 'port', 'workers'}:
        if type(value) is not int:
            raise ConfigError('Enter an integer.')
        maximum = {'positive': 1000000, 'port': 65535, 'workers': 5}[kind]
        minimum = 2 if kind == 'workers' else 1
        if not minimum <= value <= maximum:
            raise ConfigError(f'Enter an integer from {minimum} to {maximum}.')
        return value
    if kind in {'argv', 'hosts'}:
        if not isinstance(value, list) or (kind == 'argv' and not value) or not all(isinstance(v, str) and v.strip() for v in value):
            raise ConfigError('Enter a JSON array of nonempty strings; verification argv must not be empty.')
        if any(any(ord(c) < 32 or ord(c) == 127 for c in v) for v in value):
            raise ConfigError('Control characters are not allowed.')
        if kind == 'hosts' and any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', v) for v in value):
            raise ConfigError('Use host names or IPv4 addresses; no schemes, ports or wildcards.')
        return value
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ConfigError('Enter nonempty text without control characters.')
    value = value.strip()
    if kind in {'name', 'alias'} and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value):
        raise ConfigError('Use a name starting with a letter/digit, then letters, digits, underscores or hyphens (max 64).')
    if kind in {'https', 'git_url'}:
        # SCP-style SSH URLs are allowed only for Git; passwords/options are not.
        if kind == 'git_url' and re.fullmatch(r'[A-Za-z0-9_-]+@[A-Za-z0-9.-]+:[A-Za-z0-9_./-]+', value):
            return value
        try:
            parsed = urllib.parse.urlsplit(value)
            valid_port = parsed.port is None or 1 <= parsed.port <= 65535
        except ValueError:
            raise ConfigError('Invalid URL.') from None
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.query or parsed.fragment or not valid_port
                or any(c.isspace() for c in value)):
            raise ConfigError('Use an HTTPS URL without credentials, query or fragment (Git also accepts user@host:path).')
        if kind == 'https' and parsed.path not in {'', '/'}:
            raise ConfigError('Portainer URL must be an origin without a path.')
        return value.rstrip('/')
    if kind == 'remote_path':
        path = PurePosixPath(value)
        if not path.is_absolute() or path == PurePosixPath('/') or '..' in path.parts:
            raise ConfigError('Use an absolute remote directory other than /, without .. components.')
        return str(path)
    if kind == 'local_file':
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ConfigError('Use an absolute local path.')
        return str(path)
    if kind == 'commit' and not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', value):
        raise ConfigError('Use a full immutable Git commit ID; leave unknown rather than supplying a branch.')
    choices = {'auth': {'subscription', 'api'}, 'git_auth': {'public', 'ssh', 'https-token'}, 'yes_no': {'yes', 'no'}}
    if kind in choices and value not in choices[kind]:
        raise ConfigError('Choose: ' + ', '.join(sorted(choices[kind])))
    return value


def validate_profile(profile):
    if not isinstance(profile, dict) or set(profile) - set(FIELDS):
        raise ConfigError('Profile has unknown sections or is not an object.')
    for section, values in profile.items():
        if not isinstance(values, dict) or set(values) - set(FIELDS[section]):
            raise ConfigError(f'{section}: unknown fields or invalid object; secrets are not profile fields.')
        for key, value in values.items():
            try:
                normalized = validate_value(FIELDS[section][key][1], value)
            except ConfigError as exc:
                raise ConfigError(f'{section}.{key}: {exc}') from None
            if normalized != value:
                raise ConfigError(f'{section}.{key}: use canonical form (no trailing URL slash or surrounding whitespace).')
    def value(section, key):
        return profile.get(section, {}).get(key)
    def greater(section, low, high):
        a, b = value(section, low), value(section, high)
        return a is not None and b is not None and a > b
    if greater('access', 'mosh_udp_start', 'mosh_udp_end'):
        raise ConfigError('Mosh UDP range is reversed.')
    if greater('capacity', 'initial_workers', 'maximum_workers'):
        raise ConfigError('Initial workers exceed maximum workers.')
    c = profile.get('capacity', {})
    if all(c.get(k) is not None for k in ('initial_workers', 'task_memory_gib', 'aggregate_memory_gib')):
        if c['initial_workers'] * c['task_memory_gib'] > c['aggregate_memory_gib']:
            raise ConfigError('Initial ordinary workers exceed the aggregate RAM allowance.')
    if all(c.get(k) is not None for k in ('aggregate_memory_gib', 'host_reserve_gib', 'support_reserve_gib')):
        if sum(c[k] for k in ('aggregate_memory_gib', 'host_reserve_gib', 'support_reserve_gib')) > 64:
            raise ConfigError('RAM allocation exceeds the reported 64 GiB host.')
    if greater('capacity', 'heavy_builds', 'maximum_workers'):
        raise ConfigError('Heavy-build concurrency exceeds maximum workers.')
    p = profile.get('portainer', {})
    if p.get('control_environment') and p.get('control_environment') == p.get('worker_environment'):
        raise ConfigError('Control and worker environments must be distinct.')
    storage = profile.get('storage', {})
    paths = [PurePosixPath(storage[k]) for k in ('control_root', 'results_root', 'backup_root') if storage.get(k)]
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(paths) for b in paths[i + 1:]):
        raise ConfigError('QNAP control, results and backup directories must not overlap.')


def profiles_path():
    base = os.environ.get('DEV_STACK_CONFIG_HOME')
    if base:
        directory = Path(base).expanduser()
    else:
        directory = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))).expanduser() / 'dev-stack'
    if not directory.is_absolute():
        raise ConfigError('Configuration home must be an absolute path.')
    path = directory / 'profiles.json'
    if path.is_symlink():
        raise ConfigError('Refusing a symlink profiles file.')
    resolved = path.resolve()
    # Some managed workspaces place empty .git guard directories in home/tmp.
    # Real repositories have a HEAD file or a worktree/submodule .git file.
    in_git = any((parent / '.git').is_file() or (parent / '.git' / 'HEAD').is_file() for parent in resolved.parents)
    if ROOT in resolved.parents or in_git:
        raise ConfigError('Private profiles must live outside Git repositories.')
    return path


def load_document(path):
    if not path.exists():
        return {'schema_version': 1, 'profiles': {}}
    if not path.is_file():
        raise ConfigError('Profile path is not a regular file.')
    if os.name == 'posix' and (path.stat().st_mode & 0o077 or path.stat().st_uid != os.getuid()):
        raise ConfigError('Profile file must be owned by this user and have mode 600 (chmod 600 the profile file).')
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError):
        raise ConfigError('Profile file is not valid UTF-8 JSON; existing data was not changed.') from None
    if (not isinstance(document, dict) or set(document) != {'schema_version', 'profiles'}
            or type(document['schema_version']) is not int or document['schema_version'] != 1
            or not isinstance(document['profiles'], dict)):
        raise ConfigError('Unsupported profile schema; existing data was not changed.')
    for name, profile in document['profiles'].items():
        validate_value('name', name)
        validate_profile(profile)
    return document


def save_document(path, document):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.profiles-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def prompt_value(label, kind, default):
    while True:
        display = json.dumps(default) if isinstance(default, list) else str(default) if default is not None else 'unknown'
        raw = input(f'{label} [{display}]: ').strip()
        if raw == '?':
            return None
        if not raw:
            return default
        try:
            parsed = json.loads(raw) if kind in {'positive', 'port', 'workers', 'argv', 'hosts'} else raw
            return validate_value(kind, parsed)
        except (ValueError, ConfigError) as exc:
            print(str(exc) if isinstance(exc, ConfigError) else 'Enter valid JSON (integer or array as requested).')


def configure(path, document, name, section):
    if not sys.stdin.isatty():
        raise ConfigError('configure requires an interactive terminal; use documented JSON for managed setup.')
    print('No deployment. Values stay in your private profile. Do not paste secrets into these fields.')
    print('Enter keeps the shown value; ? clears it to unknown. Ctrl-C cancels without saving.')
    profile = json.loads(json.dumps(document['profiles'].get(name, {})))
    for group in ([section] if section else FIELDS):
        print(f'\n{group.upper()}')
        values = profile.setdefault(group, {})
        for key, (label, kind, default) in FIELDS[group].items():
            values[key] = prompt_value(label, kind, values.get(key, default))
    validate_profile(profile)
    document['profiles'][name] = profile
    save_document(path, document)
    print(f'\nSaved private profile {name}: {path}')
    print('Next: doctor for missing settings; credentials for optional native-keyring storage.')


def native_keyring():
    try:
        import keyring
        backend = keyring.get_keyring()
        if type(backend).__module__ not in NATIVE_BACKENDS or float(backend.priority) <= 0:
            return None
        return keyring
    except Exception:
        return None


def credential_spec(profile, name, kind):
    if kind == 'portainer':
        config = profile.get('portainer', {})
        credential_profile, url = config.get('credential_profile'), config.get('url')
        if not credential_profile or not url:
            raise ConfigError('Configure portainer.url and portainer.credential_profile first.')
        specific = 'PORTAINER_API_KEY_' + re.sub('[^A-Za-z0-9]', '_', credential_profile).upper()
        return (specific, 'PORTAINER_API_KEY'), 'portainer-deploy', f'{credential_profile}@{url}'
    env = {'openai': 'OPENAI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY', 'github': 'GH_TOKEN'}[kind]
    return (env,), 'dev-stack', f'{name}:{kind}'


def secret_input(label):
    if not sys.stdin.isatty():
        raise ConfigError('Secret input requires an interactive terminal.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            value = getpass.getpass(label)
        except getpass.GetPassWarning:
            raise ConfigError('Hidden input unavailable; refusing echoed secret input.') from None
    if not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ConfigError('Secret must be nonempty and contain no control characters.')
    return value


def credentials(profile, name, kind):
    variables, service, account = credential_spec(profile, name, kind)
    keyring = native_keyring()
    if keyring is None:
        raise ConfigError('No supported native keyring. Use an environment variable (precedence order): ' + ', '.join(variables) + '. No plaintext fallback.')
    secret = secret_input(f'{kind} credential (stored in native OS keyring): ')
    try:
        keyring.set_password(service, account, secret)
    except Exception:
        raise ConfigError('Native keyring storage failed; no plaintext fallback.') from None
    print('Credential saved in native OS keyring; no secret written to configuration.')
    if any(os.environ.get(variable) for variable in variables):
        print('An environment credential is set and takes precedence over the stored value.')


def resolve_secret(profile, name, kind):
    variables, service, account = credential_spec(profile, name, kind)
    for variable in variables:
        if os.environ.get(variable):
            return os.environ[variable]
    keyring = native_keyring()
    if keyring:
        try:
            value = keyring.get_password(service, account)
        except Exception:
            raise ConfigError('Native keyring lookup failed.') from None
        if value:
            return value
    raise ConfigError('Missing credential. Set an environment variable (precedence order): ' + ', '.join(variables) + '; or use credentials with a native keyring.')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ConfigError('Portainer redirected the request; use its final HTTPS origin. Credential was not forwarded.')


def check_portainer(profile, secret):
    config = profile.get('portainer', {})
    for key in ('url', 'control_environment', 'worker_environment'):
        if not config.get(key):
            raise ConfigError('Missing portainer.' + key)
    if not secret or any(ord(c) < 32 or ord(c) == 127 for c in secret):
        raise ConfigError('Invalid credential format.')
    try:
        context = ssl.create_default_context(cafile=config.get('ca_bundle'))
    except (OSError, ssl.SSLError):
        raise ConfigError('Cannot load CA trust. TLS verification is required.') from None
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
    request = urllib.request.Request(config['url'] + '/api/endpoints', headers={'X-API-Key': secret, 'Accept': 'application/json'}, method='GET')
    try:
        with opener.open(request, timeout=20) as response:
            body = response.read(4 * 1024 * 1024 + 1)
        if len(body) > 4 * 1024 * 1024:
            raise ConfigError('Portainer response exceeded the diagnostic size limit.')
        endpoints = json.loads(body)
    except urllib.error.HTTPError as exc:
        raise ConfigError(f'Portainer HTTP {exc.code}; response body suppressed.') from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise ConfigError('Portainer connection, TLS or JSON check failed; remote diagnostics suppressed.') from None
    if not isinstance(endpoints, list):
        raise ConfigError('Portainer endpoint response is not a list.')
    ids = []
    for role, expected_type in (('control_environment', 1), ('worker_environment', 4)):
        matches = [e for e in endpoints if isinstance(e, dict) and e.get('Name') == config[role]]
        if len(matches) != 1:
            raise ConfigError(f'{role}: expected exactly one exact-name match; found {len(matches)}.')
        endpoint = matches[0]
        if type(endpoint.get('Id')) is not int or endpoint['Id'] <= 0 or type(endpoint.get('Type')) is not int or endpoint['Type'] != expected_type:
            raise ConfigError(f'{role}: unexpected endpoint ID/type for the pilot topology.')
        if type(endpoint.get('Status')) is not int or endpoint['Status'] != 1:
            raise ConfigError(f'{role}: environment is not reported up.')
        if expected_type == 4:
            # Current API nests Edge settings; older releases exposed AsyncMode at root.
            edge = endpoint.get('Edge', {})
            if not isinstance(edge, dict):
                raise ConfigError(f'{role}: invalid Edge metadata.')
            modes = [source['AsyncMode'] for source in (endpoint, edge) if 'AsyncMode' in source]
            if any(type(mode) is not bool or mode for mode in modes):
                raise ConfigError(f'{role}: invalid or asynchronous Edge mode.')
        ids.append(endpoint['Id'])
    if len(set(ids)) != 2:
        raise ConfigError('Control and worker resolved to the same endpoint.')
    print('Portainer: exact distinct Docker-local and Docker-Edge environment records matched; reported up.')
    print('No stacks inspected or changed. Standard-mode behavior, Docker access and private SSH/mosh still need live verification.')


def doctor(profile, name, live=False, prompt_key=False):
    missing = []
    for group, fields in FIELDS.items():
        for key in fields:
            if profile.get(group, {}).get(key) is None and (group, key) not in OPTIONAL:
                missing.append(f'{group}.{key}')
    for field in missing:
        print('MISSING ' + field)
    ca = profile.get('portainer', {}).get('ca_bundle')
    if ca and not Path(ca).is_file():
        raise ConfigError('portainer.ca_bundle does not name a local regular file.')
    print(f'Configuration: {len(missing)} unanswered required fields. Values and secrets omitted.')
    if live:
        secret = secret_input('Portainer API key (this check only; not stored): ') if prompt_key else resolve_secret(profile, name, 'portainer')
        check_portainer(profile, secret)
    print('Live host/auth/fixture, resource limits, SSH host keys and mosh checks remain Phase 0/1 work.')
    if profile.get('fixture', {}).get('needs_container_builds') == 'yes':
        print('BLOCKER: choose and verify a separate builder/VM boundary before this fixture runs.')
    return 1 if missing else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='pilot', help='private profile name (default: pilot)')
    sub = parser.add_subparsers(dest='command', required=True)
    config = sub.add_parser('configure', help='interactive, resumable non-secret setup')
    config.add_argument('--section', choices=FIELDS)
    sub.add_parser('fields', help='list input fields and suggested non-secret defaults')
    diagnostic = sub.add_parser('doctor', help='local validation; no network unless --portainer')
    diagnostic.add_argument('--portainer', action='store_true', help='GET exact environment records with TLS verification')
    diagnostic.add_argument('--prompt-key', action='store_true', help='hidden one-time key input; requires --portainer')
    credential = sub.add_parser('credentials', help='hidden native-keyring storage; no file fallback')
    credential.add_argument('kind', choices=('portainer', 'openai', 'anthropic', 'github'))
    args = parser.parse_args(argv)
    try:
        validate_value('name', args.profile)
        if args.command == 'fields':
            for section, fields in FIELDS.items():
                for key, (label, kind, default) in fields.items():
                    print(f'{section}.{key}: {label}; type={kind}; suggested={json.dumps(default)}')
            return 0
        if args.command == 'doctor' and args.prompt_key and not args.portainer:
            raise ConfigError('--prompt-key requires --portainer.')
        path = profiles_path()
        document = load_document(path)
        if args.command == 'configure':
            configure(path, document, args.profile, args.section)
            return 0
        profile = document['profiles'].get(args.profile)
        if profile is None:
            raise ConfigError('Profile missing. Run configure first.')
        if args.command == 'credentials':
            credentials(profile, args.profile, args.kind)
            return 0
        return doctor(profile, args.profile, args.portainer, args.prompt_key)
    except (ConfigError, OSError) as exc:
        # OS/keyring/network exception bodies can contain local metadata or credentials.
        print('error: ' + (str(exc) if isinstance(exc, ConfigError) else 'Local file or I/O operation failed.'), file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled; incomplete configuration was not saved.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
