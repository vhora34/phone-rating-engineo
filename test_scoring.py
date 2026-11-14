import unittest
from catalog import load_catalog, slugify_model, price_bracket, bracket_averages
from scoring import resolve_pillars, rate_phone, classify_phone, value_verdict, load_evidence

SRC = {'title':'Independent lab review', 'url':'https://example.org/review'}

def record(score): return {'score':score,'note':'Independent measured result','sources':[SRC]}

class RatingTests(unittest.TestCase):
    def setUp(self):
        self.phone = {'brand':'Samsung','model':'Galaxy S25 Ultra','id':'samsung_galaxy_s25_ultra',
                      'specs':{'processor':'Snapdragon Test','ram_gb':'12','storage_gb':'256',
                               'battery_mah':'5000','charging_w':'45W','display_type':'AMOLED 120Hz',
                               'rear_camera':'50MP','primary_camera_sensor':'Sensor A'},
                      'launch_price':80000,'bracket':'Flagship'}
        self.evidence = {'models':{},'components':{'chipsets':{},'camera_sensors':{}}}
    def test_slug(self):
        self.assertEqual(slugify_model('Samsung','Galaxy S25 Ultra 12GB RAM 256GB Storage'),'samsung_galaxy_s25_ultra')
        self.assertEqual(slugify_model('Samsung','Samsung Galaxy S25 Ultra (12GB RAM / 256GB Storage)'),'samsung_galaxy_s25_ultra')
        self.assertEqual(slugify_model('OnePlus','13R 8/128'),'oneplus_13r')
    def test_catalog_and_brackets(self):
        phones=load_catalog()
        self.assertGreater(len(phones),300)
        self.assertEqual(len(phones),len({p['id'] for p in phones}))
        self.assertEqual(price_bracket(14000),'Budget')
        self.assertEqual(price_bracket(35000),'Upper Mid-Range')
        self.assertEqual(bracket_averages([{'id':'x','bracket':'Budget'},{'id':'y','bracket':'Budget'}],{'x':7,'y':8}),{'Budget':7.5})
    def test_tier1(self):
        self.evidence['models'][self.phone['id']]={p:record(8.5) for p in ('performance','camera','battery','display')}
        r=rate_phone(self.phone,self.evidence,12,256)
        self.assertTrue(all(t==1 for t in r['tiers'].values()))
        self.assertEqual(r['confidence'],'High (Lab & Review Verified)')
        self.assertEqual(len([e for e in r['audit_trail'] if e['tier']==1]),4)
    def test_tier2(self):
        self.evidence['components']['chipsets']['Snapdragon Test']={'performance':record(9)}
        self.evidence['components']['camera_sensors']['Sensor A']={'camera':record(8)}
        r=rate_phone(self.phone,self.evidence,12,256)
        self.assertEqual(r['tiers']['performance'],2)
        self.assertEqual(r['tiers']['camera'],2)
        self.assertEqual(r['confidence'],'Low (Raw Specs Only)')  # battery and display still spec-only
    def test_tier3_and_missing(self):
        r=rate_phone(self.phone,self.evidence,12,256)
        self.assertTrue(all(t==3 for t in r['tiers'].values()))
        self.assertIsNotNone(r['overall_rating'])
        empty={**self.phone,'specs':{}}
        r=rate_phone(empty,self.evidence,12,256)
        self.assertIsNone(r['overall_rating'])
        self.assertEqual(r['category'],'Insufficient Data')
    def test_bad_unsourced_evidence(self):
        self.evidence['models'][self.phone['id']]={'performance':{'score':10,'note':'unsupported'}}
        self.assertEqual(resolve_pillars(self.phone,self.evidence)[1]['performance'],3)
    def test_relative_categories(self):
        self.assertEqual(classify_phone(dict(performance=8,camera=8,battery=8,display=8),8,'Budget'),'Budget All-Rounder')
        self.assertIn('Battery Champion',classify_phone(dict(performance=5,camera=5,battery=9,display=5),6,'Budget'))
        self.assertIn('Camera-Centric',classify_phone(dict(performance=6,camera=9,battery=6,display=6),6.75,'Flagship'))
    def test_value_tags(self):
        self.assertEqual(value_verdict(8.5,7.8,11000,10000)['value_tag'],'Category Killer / Best Value Variant')
        self.assertEqual(value_verdict(8.5,8.1,12500,10000)['value_tag'],'Great Phone, Overpriced Variant')
        self.assertEqual(value_verdict(6,7,10000,10000)['value_tag'],'Overpriced for the Market')
        self.assertEqual(value_verdict(8,8,10000,10000,True)['value_tag'],'Bottlenecked Variant')
        self.assertEqual(value_verdict(8,8,10000,10000)['value_tag'],'Fair Market Value')
        self.assertEqual(value_verdict(8,None,10000,10000)['value_tag'],'Insufficient Market Evidence')
    def test_variant(self):
        a=rate_phone(self.phone,self.evidence,6,64)
        b=rate_phone(self.phone,self.evidence,12,256)
        self.assertLess(a['scores']['performance'],b['scores']['performance'])
        self.assertTrue(a['bottleneck'])
    def test_evidence_structure(self):
        data=load_evidence()
        self.assertIn('models',data)
        self.assertIn('components',data)

if __name__=='__main__': unittest.main()
