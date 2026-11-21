import json
import pathlib
import tempfile
import unittest
from validate_optimizer_preflight import validate_registry

class OptimizerPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / 'registry.json'

    def _write(self, cards):
        self.path.write_text(json.dumps({'cards': cards}), encoding='utf-8')

    def test_exact_ids_pass_even_if_set_code_not_RAD(self):
        self._write([{'public_code': 'RAD-149/167', 'set_code': 'Unspecified'},
                     {'public_code': 'RAD-041/167', 'set_code': 'Unspecified'}])
        report=validate_registry(self.path,expected_count=2,required=('RAD-149/167','RAD-041/167'))
        self.assertEqual(report['registered_print_codes'],2)
        self.assertFalse(report['full_radiance_supported'])

    def test_missing_required_card_fails_clearly(self):
        self._write([{'public_code': 'RAD-149/167'}])
        with self.assertRaisesRegex(ValueError,'Missing pinned Radiance'):
            validate_registry(self.path,expected_count=1,required=('RAD-149/167','RAD-041/167'))

    def test_wrong_registry_size_fails(self):
        self._write([{'public_code': 'RAD-149/167'}])
        with self.assertRaisesRegex(ValueError,'Expected 988 compiled cards'):
            validate_registry(self.path,required=('RAD-149/167',))

    def test_missing_cards_list_fails(self):
        self.path.write_text('{"registry": []}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'cards list'):
            validate_registry(self.path,expected_count=0,required=())

    def test_duplicate_required_id_fails(self):
        self._write([{'public_code':'RAD-149/167'},{'public_code':'RAD-149/167'}])
        with self.assertRaisesRegex(ValueError,'Ambiguous pinned Radiance'):
            validate_registry(self.path,expected_count=2,required=('RAD-149/167',))

    def test_blank_public_codes_allowed_for_unrelated_cards(self):
        self._write([{'public_code':''},{'public_code':None},{},
                     {'public_code':'RAD-149/167'}])
        report=validate_registry(self.path,expected_count=4,required=('RAD-149/167',))
        self.assertEqual(report['registered_print_codes'],1)
        self.assertEqual(report['definitions_without_print_code'],3)

    def test_duplicate_unrelated_print_code_does_not_block_required(self):
        self._write([{'public_code':'OLD-002'},{'public_code':'OLD-002'},
                     {'public_code':'RAD-149/167'}])
        report=validate_registry(self.path,expected_count=3,required=('RAD-149/167',))
        self.assertEqual(report['registered_print_codes'],3)

if __name__ == '__main__': unittest.main()
