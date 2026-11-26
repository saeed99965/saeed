import unittest
from datetime import datetime,timedelta,timezone
from deadgroupfinder.core import normalize_telegram_link,inactivity_status
from deadgroupfinder.db import Database
class CoreTests(unittest.TestCase):
 def test_public_link(self): self.assertEqual(normalize_telegram_link('https://t.me/fun_group').normalized_link,'https://t.me/fun_group')
 def test_invite_link(self): self.assertEqual(normalize_telegram_link('https://t.me/+abcDEF123').invite_hash,'abcDEF123')
 def test_reject_channel_post_link(self): self.assertIsNone(normalize_telegram_link('https://t.me/s/channelname'))
 def test_no_history_before_monitoring(self):
  now=datetime(2026,11,26,tzinfo=timezone.utc); start=now-timedelta(days=7); r=inactivity_status(None,start,now=now); self.assertEqual(r['status'],'NO_MESSAGE_OBSERVED')
 def test_inactive_boundary(self):
  now=datetime(2026,11,26,tzinfo=timezone.utc); r=inactivity_status(now-timedelta(days=2),None,now=now); self.assertEqual(r['status'],'INACTIVE')
 def test_db_deduplicates(self):
  db=Database(':memory:'); self.assertTrue(db.candidate('https://t.me/fun_group','fun_group','Fun','test')); self.assertFalse(db.candidate('https://t.me/fun_group','fun_group','Fun','test')); db.db.close()
if __name__=='__main__': unittest.main()
