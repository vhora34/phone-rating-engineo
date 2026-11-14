import unittest
from owner_feedback import validate_feedback, feedback_for_model, discover_youtube_reviews

IDS = {'Gyan Therapy':'UC_test_gyan', 'GeekyRanjit':'UC_test_geeky'}
ENTRY = {'model_slug':'samsung_galaxy_s25','url':'https://www.youtube.com/watch?v=12345678901',
         'finding':'Reviewer reports noticeable warmth after extended gaming', 'pillar':'performance',
         'reviewer':'Gyan Therapy','channel_id':'UC_test_gyan','verified_from_content':True}

class FeedbackTests(unittest.TestCase):
    def test_allowed_youtube(self):
        self.assertTrue(validate_feedback(ENTRY,'youtube',IDS))
    def test_wrong_channel_rejected(self):
        self.assertFalse(validate_feedback({**ENTRY,'channel_id':'imposter'},'youtube',IDS))
    def test_unverified_rejected(self):
        self.assertFalse(validate_feedback({**ENTRY,'verified_from_content':False},'youtube',IDS))
    def test_reddit_url_and_verification(self):
        e={**ENTRY,'url':'https://www.reddit.com/r/Android/comments/abc/test/'}
        self.assertTrue(validate_feedback(e,'reddit'))
        self.assertFalse(validate_feedback({**e,'url':'https://example.com/post'},'reddit'))
    def test_model_filter(self):
        data={'youtube':[ENTRY], 'reddit':[]}
        self.assertEqual(len(feedback_for_model(data,'samsung_galaxy_s25',IDS)['youtube']),1)
        self.assertEqual(len(feedback_for_model(data,'apple_iphone_16',IDS)['youtube']),0)
    def test_no_api_credentials_no_request(self):
        self.assertEqual(discover_youtube_reviews('',IDS,'Galaxy S25'),[])
    def test_channel_id_checked_in_api_response(self):
        class FakeResponse:
            def raise_for_status(self): pass
            def json(self):
                return {'items':[{'id':{'videoId':'12345678901'},'snippet':{'channelId':'imposter'}},
                                 {'id':{'videoId':'abcdefghijk'},'snippet':{'channelId':'UC_test_gyan','title':'Review'}}]}
        class FakeSession:
            def get(self,*args,**kwargs): return FakeResponse()
        out=discover_youtube_reviews('key',IDS,'Galaxy S25',session=FakeSession())
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['reviewer'],'Gyan Therapy')

if __name__=='__main__': unittest.main()
