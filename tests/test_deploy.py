"""Synthetic control-protocol and bundle boundary checks; no host mutations."""
import base64
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

bootstrap = module('bootstrap-deploy')
dispatch = module('deploy-dispatch')

class DeployTests(unittest.TestCase):
    def test_only_bounded_staging_operations(self):
        request = dict(version=1, project='unibase', environment='staging', action='check', configurationHash='a'*64)
        dispatch.validate_request(request)
        for key,value in [('version',True),('project','../elsewhere'),('environment','production'),('action','setup'),('configurationHash','a'*65)]:
            with self.subTest(key=key), self.assertRaises(ValueError): dispatch.validate_request({**request,key:value})
        with self.assertRaises(ValueError): dispatch.validate_request({**request,'command':'sh'})
        release={**request,'action':'deploy','commit':'b'*40,'image':'ghcr.io/test/unibase@sha256:'+'c'*64}
        dispatch.validate_request(release)
        with self.assertRaises(ValueError): dispatch.validate_request({**release,'image':'ghcr.io/test/unibase:latest'})

    def test_registered_config_and_image_bind_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); registry=root/'registry'; registry.mkdir()
            source=root/'control'/'unibase'/('b'*64); (source/'deploy/environments').mkdir(parents=True)
            config={'deployment':{'imageRepository':'ghcr.io/test/unibase'}}
            (source/'deploy/environments/staging.json').write_text(json.dumps(config))
            (source/'project.config.json').write_text('{"slug":"unibase"}')
            (registry/'unibase.json').write_text(json.dumps({'revision':'b'*64}))
            request=dict(version=1,project='unibase',environment='staging',action='deploy',configurationHash=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest(),image='ghcr.io/test/unibase@sha256:'+'c'*64,commit='d'*40)
            with patch.object(dispatch,'REGISTRY',registry), patch.object(dispatch,'CONTROL',root/'control'), patch.object(dispatch,'trusted'):
                command=dispatch.command(request)
                self.assertEqual(command[:2],['/bin/bash',str(source/'scripts/deploy/vps.sh')])
                self.assertEqual(command[2:5],['deploy','staging','--apply'])
                for change in ({'configurationHash':'0'*64},{'image':'ghcr.io/other/app@sha256:'+'c'*64}):
                    with self.assertRaises(ValueError): dispatch.command({**request,**change})

    def test_public_key_cannot_inject_ssh_options(self):
        key='ssh-ed25519 '+base64.b64encode(b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20'+b'a'*32).decode()
        self.assertEqual(bootstrap.public_key(key+' comment'),key)
        for value in ('command="sh" '+key,key+'\n'+key,'ssh-ed25519 YQ=='):
            with self.assertRaises(ValueError): bootstrap.public_key(value)

    def test_bundle_rejects_paths_links_and_checksum(self):
        for name,kind in [('src/safe.txt',tarfile.REGTYPE),('../escape',tarfile.REGTYPE),('src/link',tarfile.SYMTYPE),('src/.env',tarfile.REGTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary); archive=root/'input.tar'; destination=root/'out'; destination.mkdir()
                with tarfile.open(archive,'w') as tar:
                    member=tarfile.TarInfo(name); member.type=kind; member.size=1 if kind==tarfile.REGTYPE else 0
                    tar.addfile(member,io.BytesIO(b'x') if member.size else None)
                digest=hashlib.sha256(archive.read_bytes()).hexdigest()
                if name=='src/safe.txt':
                    extracted=bootstrap.extract(archive,digest,destination)
                    self.assertEqual((extracted/name).read_text(),'x')
                    before=bootstrap.tree_contents(extracted); (extracted/name).write_text('changed')
                    self.assertNotEqual(bootstrap.tree_contents(extracted),before)
                else:
                    with self.assertRaises(ValueError): bootstrap.extract(archive,digest,destination)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); archive=root/'input.tar'; archive.write_bytes(b'wrong'); destination=root/'out'; destination.mkdir()
            with self.assertRaises(ValueError): bootstrap.extract(archive,'0'*64,destination)

if __name__=='__main__': unittest.main()
