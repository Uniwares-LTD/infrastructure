"""Real Docker deletion on an explicitly opted-in disposable Linux runner.

A loopback-only synthetic registry serves tiny inert images; no provider credentials
or application images are used. Only references created by this test are removed.
"""
import copy
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch
from test_image_maintenance import CONFIG
import image_maintenance as m


def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def layer(name, content):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as archive:
        item = tarfile.TarInfo(name)
        item.size = len(content)
        archive.addfile(item, io.BytesIO(content))
    raw = stream.getvalue()
    return raw, gzip.compress(raw)


@unittest.skipUnless(os.environ.get('RETENTION_DISPOSABLE_DOCKER') == '1',
                     'Requires an explicitly selected disposable Docker daemon')
class DockerIntegrationTests(unittest.TestCase):
    def test_real_shared_layers_references_stopped_container_and_deletion(self):
        if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):
            self.fail('Use the disposable runner default local Docker daemon')
        m.run(['docker', 'info', '--format', '{{.DockerRootDir}}'])
        blobs, manifests = {}, {}
        class Registry(BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.do_GET()
            def do_GET(self):
                if self.path in ('/v2/', '/v2'):
                    body, kind = b'{}', 'application/json'
                elif '/blobs/' in self.path:
                    body, kind = blobs[self.path.split('/blobs/')[1]], 'application/octet-stream'
                elif '/manifests/' in self.path:
                    body = manifests[self.path.split('/manifests/')[1]]
                    kind = 'application/vnd.docker.distribution.manifest.v2+json'
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header('Docker-Distribution-API-Version', 'registry/2.0')
                self.send_header('Content-Type', kind)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Docker-Content-Digest', sha(body))
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(body)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Registry)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        repo = 'localhost:' + str(server.server_port) + '/retention-' + uuid.uuid4().hex
        references, container = [], None
        base, base_gzip = layer('shared-layer.txt', uuid.uuid4().hex.encode())
        blobs[sha(base_gzip)] = base_gzip
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for name in ('state', 'apps/app', 'releases/app/staging/releases'):
                    (root / name).mkdir(parents=True)
                config = copy.deepcopy(CONFIG)
                config['projects']['app']['imageRepository'] = repo
                config['projects']['app']['environments'] = {'staging': 'staging'}
                engine = m.Maintenance(config, state=root/'state', apps=root/'apps', releases=root/'releases')
                ledger = {'version': 1, 'activations': []}
                for number in range(1, 8):
                    extra, zipped = layer('release.txt', str(number).encode())
                    blobs[sha(zipped)] = zipped
                    image_config = m.canonical({'architecture': 'amd64', 'os': 'linux',
                        'config': {'Cmd': ['/inert-fixture']},
                        'rootfs': {'type': 'layers', 'diff_ids': [sha(base), sha(extra)]},
                        'history': [{'created_by': 'synthetic'}, {'created_by': 'synthetic'}]})
                    blobs[sha(image_config)] = image_config
                    manifest = m.canonical({'schemaVersion': 2,
                        'mediaType': 'application/vnd.docker.distribution.manifest.v2+json',
                        'config': {'mediaType': 'application/vnd.docker.container.image.v1+json',
                                   'size': len(image_config), 'digest': sha(image_config)},
                        'layers': [{'mediaType': 'application/vnd.docker.image.rootfs.diff.tar.gzip',
                                    'size': len(data), 'digest': sha(data)} for data in (base_gzip, zipped)]})
                    tag = 'release-' + str(number)
                    manifests[tag] = manifests[sha(manifest)] = manifest
                    reference = repo + '@' + sha(manifest)
                    references.extend([repo + ':' + tag, reference])
                    pulled = subprocess.run(['docker', 'pull', repo + ':' + tag],
                        capture_output=True, text=True, timeout=60, env=m.ENV)
                    self.assertEqual(pulled.returncode, 0, 'Synthetic loopback image pull: ' + pulled.stderr)
                    snapshot = format(number, '040x') + '.fixture'
                    path = root/'releases/app/staging/releases'/snapshot
                    path.mkdir()
                    (path/'compose.env').write_text('DEPLOY_ENV=staging\nIMAGE_DIGEST=' + reference +
                        '\nRELEASE_COMMIT=' + format(number, '040x') + '\n')
                    ledger['activations'].append({'environment': 'staging', 'snapshot': snapshot,
                        'image': reference, 'commit': format(number, '040x'),
                        'activatedAt': int(time.time()) - (40-number)*86400})
                (root/'apps/app/image-release-ledger.json').write_text(json.dumps(ledger))
                selected = root/'releases/app/staging'
                (selected/'current').symlink_to(selected/'releases'/ledger['activations'][6]['snapshot'])
                (selected/'previous').symlink_to(selected/'releases'/ledger['activations'][2]['snapshot'])
                container = m.run(['docker', 'create', ledger['activations'][0]['image']]).strip()
                shared = repo + '-other:shared'
                m.run(['docker', 'tag', ledger['activations'][1]['image'], shared])
                references.append(shared)
                # Root trust has separate real-filesystem tests; temporary paths need
                # not be installed under /opt to exercise the real Docker boundary.
                with patch.object(m, 'trusted'):
                    preview = engine.preview('app')
                    self.assertEqual({x['id'] for x in preview['plan']['candidates']},
                        {m.run(['docker', 'image', 'inspect', '--format', '{{.Id}}',
                                ledger['activations'][3]['image']]).strip()})
                    result = engine.apply('app', preview)
                    self.assertEqual(result['status'], 'completed')
                    self.assertTrue(result['removed'])
                    for number in (0, 1, 2, 4, 5, 6):
                        m.run(['docker', 'image', 'inspect', '--format', '{{.Id}}',
                               ledger['activations'][number]['image']])
                    with self.assertRaises(m.MaintenanceError):
                        m.run(['docker', 'image', 'inspect', '--format', '{{.Id}}',
                               ledger['activations'][3]['image']])
                    self.assertEqual(engine.preview('app')['plan']['candidates'], [])
        finally:
            if container:
                subprocess.run(['docker', 'rm', container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for reference in reversed(references):
                subprocess.run(['docker', 'image', 'rm', reference],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

