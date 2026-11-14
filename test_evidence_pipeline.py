import unittest
from evidence_pipeline import validate_observation, import_rows, validate_database

GOOD = {'brand':'Samsung','model':'Galaxy S25 Ultra','pillar':'battery','source':'phonearena','metric':'browsing_endurance','value':'20.82','unit':'hours','url':'https://example.org/test','tested_on':'2026-01-02','variant':'12/256','test_conditions':'web browsing','notes':'example test fixture only'}

class PipelineTests(unittest.TestCase):
    def test_valid(self): self.assertEqual(validate_observation(GOOD), [])
    def test_missing_url(self): self.assertTrue(validate_observation({**GOOD,'url':''}))
    def test_bad_value(self): self.assertTrue(validate_observation({**GOOD,'value':'nan'}))
    def test_reject_converted_score(self): self.assertTrue(validate_observation({**GOOD,'metric':'our_score'}))
    def test_import_and_deduplicate(self):
        data, result = import_rows({'models':{},'components':{}}, [GOOD, GOOD])
        self.assertEqual(result['accepted'],1)
        self.assertEqual(result['duplicates'],1)
        self.assertEqual(len(data['models']['samsung_galaxy_s25_ultra']['observations']),1)
        self.assertEqual(validate_database(data),[])
    def test_reject_does_not_mutate(self):
        original={'models':{},'components':{}}
        updated, result=import_rows(original,[{**GOOD,'value':'oops'}])
        self.assertEqual(result['accepted'],0)
        self.assertEqual(original,{'models':{},'components':{}})

if __name__=='__main__': unittest.main()
