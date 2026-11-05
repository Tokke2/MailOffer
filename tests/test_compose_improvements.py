import ast
import __future__
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
from core.compose_helpers import duplicate_recipients, contact_duplicate_groups, merge_contact_rows, dropped_local_files
from core.compose_draft import save_draft, read_draft

ROOT = Path(__file__).resolve().parents[1]


class ComposeImprovementTests(unittest.TestCase):
    def test_recipient_overlap_case_insensitive_and_within_list(self):
        result = duplicate_recipients({'Till': ['Person <A@example.com>', 'b@example.com'], 'Bcc': ['a@EXAMPLE.com', 'a@example.com']})
        self.assertEqual(result, {'a@example.com': ['Till', 'Bcc', 'Bcc']})
        self.assertEqual(duplicate_recipients({'Till': ['a@example.com'], 'Bcc': ['b@example.com']}), {})

    def test_suggest_only_full_name_and_company_matches(self):
        rows = [dict(email='a@example.com', name=' Anna  Andersson ', company='Firman'),
                dict(email='b@example.com', name='anna andersson', company='FIRMAN'),
                dict(email='c@example.com', name='Anna Andersson', company='Annan'),
                dict(email='d@example.com', name='Anna Andersson', company='')]
        self.assertEqual(contact_duplicate_groups(rows), [rows[:2]])
        self.assertEqual(contact_duplicate_groups([{'email': 'a@x.com'}, {'email': 'b@x.com'}]), [])

    def test_merge_keeps_primary_address_language_and_unions_categories(self):
        primary = dict(email='a@example.com', name='Anna', company='A', language='en', categories=['X'])
        other = dict(email='b@example.com', name='Anna', company='A', language='sv', categories=['Y'], group='Z')
        merged = merge_contact_rows(primary, [other])
        self.assertEqual(merged['email'], primary['email'])
        self.assertEqual(merged['language'], 'en')
        self.assertEqual(merged['categories'], ['X', 'Y', 'Z'])
        self.assertEqual(primary['categories'], ['X'])

    def test_draft_roundtrip_exact_text_no_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.data/draft.json'
            state = dict(subject='  Ämne  ', body='\nText\n', free_text='', to=['a@example.com'],
                         bcc=[], to_lang={'a@example.com': 'en'}, replacements={'reg': 'ABC123'},
                         attachment_paths=['C:/foto.jpg'], profile_id='profile1',
                         password='secret', sender_profile={'password': 'secret'})
            save_draft(path, state)
            restored = read_draft(path)
            self.assertEqual(restored['body'], '\nText\n')
            self.assertEqual(restored['subject'], '  Ämne  ')
            self.assertNotIn('secret', path.read_text())
            self.assertEqual(restored['attachment_paths'], ['C:/foto.jpg'])
            self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_invalid_draft_does_not_overwrite_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'draft.json'
            save_draft(path, {'body': 'Keep'})
            for state in ({'to': 'not-a-list'}, {'replacements': {'x': {'password': 'bad'}}}, {'body': 10}):
                with self.assertRaises(ValueError):
                    save_draft(path, state)
                self.assertEqual(read_draft(path), {'body': 'Keep'})
            with mock.patch('core.update_session.os.replace', side_effect=OSError('disk full')), self.assertRaises(OSError):
                save_draft(path, {'body': 'Changed'})
            self.assertEqual(read_draft(path), {'body': 'Keep'})

    def test_drop_rejects_remote_urls_and_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'photo.png'
            file.write_bytes(b'test')
            class Url:
                def __init__(self, path, local=True): self.path, self.local = path, local
                def isLocalFile(self): return self.local
                def toLocalFile(self): return str(self.path)
            self.assertEqual(dropped_local_files([Url('https://example.com', False), Url(directory), Url(file)]), [str(file)])

    def test_contact_store_merge_is_backed_up_and_rolls_back_failed_save(self):
        # Execute the actual model classes, without importing Qt in headless CI.
        source = (ROOT / 'script/contacts_ui.py').read_text()
        tree = ast.parse(source)
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name in ('Contact', 'ContactStore')]
        scope = dict(dataclass=dataclass, field=field, Path=Path, threading=threading,
                     json=json, log=logging.getLogger('contact-test'))
        exec(compile(ast.Module(body=classes, type_ignores=[]), '<contact-model>', 'exec', flags=__future__.annotations.compiler_flag), scope)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'contacts.json'
            rows = [dict(email='a@example.com', name='Anna', company='A', categories=['X']),
                    dict(email='b@example.com', name='Anna', company='A', categories=['Y'])]
            path.write_text(json.dumps({'contacts': rows}))
            store = scope['ContactStore'](path)
            before = path.read_bytes()
            with mock.patch.object(store, '_save_locked', return_value=False), self.assertRaises(OSError):
                store.merge_duplicates(['a@example.com', 'b@example.com'], 'a@example.com')
            self.assertEqual(store.count(), 2)
            self.assertEqual(path.read_bytes(), before)
            backup = store.merge_duplicates(['a@example.com', 'b@example.com'], 'a@example.com')
            self.assertEqual(backup.read_bytes(), before)
            self.assertEqual(store.count(), 1)
            self.assertEqual(store.get('a@example.com').categories, ['X', 'Y'])
            self.assertIsNone(store.get('b@example.com'))

    def test_draft_lifecycle_and_recipient_warning_wired_before_send(self):
        source = (ROOT / 'ui/main_window.py').read_text()
        tree = ast.parse(source)
        main = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'MainWindow')
        methods = {n.name: ast.get_source_segment(source, n) for n in main.body if isinstance(n, ast.FunctionDef)}
        self.assertIn('start(2000)', methods['_setup_draft_autosave'])
        self.assertIn('not self.isVisible()', methods['_autosave_draft'])
        self.assertIn('_send_busy', methods['_autosave_draft'])
        self.assertIn('_draft_pending', methods['_begin_send'])
        self.assertLess(methods['_begin_send'].index('duplicate_recipients'), methods['_begin_send'].index('_confirm_send'))
        self.assertIn('_discard_sent_draft', methods['_handle_send_done'])
        self.assertNotIn('_discard_sent_draft', methods['_handle_send_err'])
