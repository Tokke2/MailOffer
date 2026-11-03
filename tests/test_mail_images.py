import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from core.mail_images import queue_images, pending_requests, read_request, finish_request, image_extension

ROOT = Path(__file__).resolve().parents[1]
PNG = b'\x89PNG\r\n\x1a\n' + b'example-data'


def image(name='photo.png', data=PNG):
    return {'name': name, 'data': base64.b64encode(data).decode()}


class MailImagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_queue_read_and_acknowledge_without_reimport(self):
        self.assertEqual(queue_images(self.base, [image()], 'A subject')['count'], 1)
        requests = pending_requests(self.base)
        self.assertEqual(len(requests), 1)
        subject, paths = read_request(requests[0])
        self.assertEqual(subject, 'A subject')
        self.assertEqual(Path(paths[0]).read_bytes(), PNG)
        finish_request(requests[0], 'imported')
        self.assertEqual(pending_requests(self.base), [])
        self.assertEqual(Path(paths[0]).read_bytes(), PNG)

    def test_safe_unique_names_keep_images_with_identical_original_names(self):
        queue_images(self.base, [image('../../photo.exe'), image('../../photo.exe')])
        _, paths = read_request(pending_requests(self.base)[0])
        self.assertNotEqual(paths[0], paths[1])
        for path in paths:
            self.assertEqual(Path(path).suffix, '.png')
            self.assertIn(self.base / '.data/mail-images', Path(path).parents)

    def test_invalid_image_or_base64_does_not_publish_partial_batch(self):
        for data in ([image(), image(data=b'not an image')], [{'name': 'bad.png', 'data': '!!!!'}]):
            with self.assertRaises(ValueError):
                queue_images(self.base, data)
            self.assertEqual(pending_requests(self.base), [])

    def test_image_formats_are_restricted(self):
        for data, extension in ((b'\xff\xd8\xffrest', '.jpg'), (b'GIF89a', '.gif'),
                                (b'RIFF0000WEBPdata', '.webp'), (b'BMrest', '.bmp'), (b'II*\x00rest', '.tiff')):
            self.assertEqual(image_extension(data), extension)
        with self.assertRaises(ValueError):
            image_extension(b'<svg><script>bad</script></svg>')

    def test_count_and_size_limits(self):
        with self.assertRaises(ValueError):
            queue_images(self.base, [image()] * 11)
        with self.assertRaises(ValueError):
            queue_images(self.base, [])
        with mock.patch('core.mail_images.MAX_FILE', 10), self.assertRaises(ValueError):
            queue_images(self.base, [image()])
        with mock.patch('core.mail_images.MAX_TOTAL', len(PNG)), self.assertRaises(ValueError):
            queue_images(self.base, [image(), image()])

    def test_modified_local_image_is_rejected(self):
        queue_images(self.base, [image()])
        request = pending_requests(self.base)[0]
        _, paths = read_request(request)
        Path(paths[0]).write_bytes(PNG + b'tampered')
        with self.assertRaises(ValueError):
            read_request(request)

    def test_manifest_path_traversal_is_rejected(self):
        queue_images(self.base, [image()])
        request = pending_requests(self.base)[0]
        manifest = json.loads(request.read_text())
        manifest['images'][0]['name'] = '../../private.png'
        request.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            read_request(request)

    def test_new_jobs_do_not_overwrite_existing_images_or_contacts(self):
        contact = self.base / 'adresslistor/contacts.json'
        contact.parent.mkdir()
        contact.write_text('original')
        queue_images(self.base, [image()])
        queue_images(self.base, [image()])
        self.assertEqual(len(pending_requests(self.base)), 2)
        self.assertEqual(contact.read_text(), 'original')

    def test_cancelled_request_is_not_prompted_again(self):
        queue_images(self.base, [image()])
        request = pending_requests(self.base)[0]
        finish_request(request, 'dismissed')
        self.assertEqual(pending_requests(self.base), [])

    def test_redirected_inbox_is_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        try:
            (self.base / '.data').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValueError):
            queue_images(self.base, [image()])
        self.assertEqual(list(outside.iterdir()), [])

    def test_native_bridge_action_and_capability(self):
        spec = importlib.util.spec_from_file_location('image_native_test', ROOT / 'thunderbird/native_host.py')
        host = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(host)
        with mock.patch.object(host, 'APP_ROOT', self.base):
            self.assertIn('import_images', host.handle({'action': 'ping', 'protocol_version': 1})['capabilities'])
            result = host.handle({'action': 'import_images', 'protocol_version': 1, 'images': [image()], 'subject': 'Imported'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['count'], 1)
        self.assertEqual(len(pending_requests(self.base)), 1)
