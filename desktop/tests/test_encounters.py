"""Synthetic Gen-IV location parsing, including every encrypted block order."""
import struct
import unittest
from soullink.save_reader import _pokemon,_crypt,BLOCK_POSITION


def synthetic(order=0,extended=177,legacy=3002,egg=0,is_egg=False):
    plain=bytearray(236);pid=(order<<13)|3
    struct.pack_into('<I',plain,0,pid);struct.pack_into('<H',plain,8,25)
    struct.pack_into('<I',plain,0x38,(1<<30) if is_egg else 0)
    struct.pack_into('<HH',plain,0x44,egg,extended)
    struct.pack_into('<H',plain,0x80,legacy);plain[0x5F]=8;plain[0x8C]=5
    struct.pack_into('<HH',plain,0x8E,20,20)
    crc=sum(struct.unpack('<64H',plain[8:136]))&65535;struct.pack_into('<H',plain,6,crc)
    raw=bytearray(plain)
    for logical,slot in enumerate(BLOCK_POSITION[order]):raw[8+slot*32:40+slot*32]=plain[8+logical*32:40+logical*32]
    _crypt(raw,8,136,crc);_crypt(raw,136,236,pid)
    return bytes(raw)


class EncounterTests(unittest.TestCase):
    def test_locations_survive_every_block_order_party_and_boxes(self):
        for order in range(24):
            raw=synthetic(order)
            for size,party in ((236,True),(136,False)):
                p=_pokemon(raw[:size],party)
                self.assertEqual(p.met_location,177);self.assertEqual(p.origin_game,8)
                self.assertFalse(p.is_egg);self.assertEqual(p.api()['metLocation'],177)
    def test_fallback_unknown_and_egg_provenance(self):
        self.assertEqual(_pokemon(synthetic(extended=0,legacy=149),True).met_location,149)
        self.assertIsNone(_pokemon(synthetic(extended=0,legacy=0),True).met_location)
        p=_pokemon(synthetic(egg=2000,is_egg=True),True)
        self.assertTrue(p.is_egg);self.assertEqual(p.egg_location,2000)


if __name__=='__main__':unittest.main()
