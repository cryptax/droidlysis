import unittest
import tempfile
import shutil
from droidlysis3 import process_file
from droidconfig import generalconfig

class DroidLysisTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_process_file(self):
        config = generalconfig(filename='../conf/general.conf', verbose=False)
        process_file(config=config,
                     infile='./apk/ph0wn-musicalear.apk',
                     outdir=self.test_dir)


if __name__ == '__main__':
    unittest.main()
