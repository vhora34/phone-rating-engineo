import unittest
from dxomark_relative import relative_indicator, reference_for

REF = {'score': 175, 'metric':'camera', 'protocol':'camera_v6',
       'source_url':'https://www.dxomark.com/example/', 'as_of':'2026-11-14'}

class RelativeDXOMARKTests(unittest.TestCase):
    def test_screenshot_arithmetic(self):
        result = relative_indicator(164, REF, 'camera', 'camera_v6')
        self.assertTrue(result['available'])
        self.assertEqual(result['relative_percent'], 93.7)
        self.assertFalse(result['is_quality_rating'])

    def test_protocol_mismatch_refused(self):
        self.assertFalse(relative_indicator(164, REF, 'camera', 'camera_v5')['available'])

    def test_metric_mismatch_refused(self):
        self.assertFalse(relative_indicator(170, REF, 'photo', 'camera_v6')['available'])

    def test_missing_provenance_refused(self):
        self.assertFalse(relative_indicator(164, {**REF, 'source_url': ''}, 'camera', 'camera_v6')['available'])

    def test_above_reference_not_clamped(self):
        self.assertEqual(relative_indicator(180, REF, 'camera', 'camera_v6')['relative_percent'], 102.9)

    def test_no_reference_configured(self):
        self.assertIsNone(reference_for({}, 'camera', 'camera_v6'))

if __name__ == '__main__': unittest.main()
