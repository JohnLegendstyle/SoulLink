import os,struct,tempfile,time,unittest
from pathlib import Path
from soullink.live_position import MAGIC,parse_position,read_position

class LivePositionTests(unittest.TestCase):
    def test_reads_checked_position(self):
        raw=MAGIC+struct.pack('<iiiii',33,704,422,1,8)
        self.assertEqual(parse_position(raw,1234),{'mapId':33,'x':704,'y':422,'direction':1,'capturedAt':1234})
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'live.position';path.write_bytes(raw)
            self.assertEqual(read_position(path)['mapId'],33)
            os.utime(path,(time.time()-11,)*2)
            with self.assertRaises(ValueError):read_position(path)

    def test_rejects_corrupt_or_impossible_values(self):
        for raw in (b'',b'BADPOS00'+struct.pack('<iiiii',33,1,1,1,1),MAGIC+struct.pack('<iiiii',-1,1,1,1,1),MAGIC+struct.pack('<iiiii',33,1,1,9,1)):
            with self.assertRaises(ValueError):parse_position(raw,1)

if __name__=='__main__':unittest.main()
