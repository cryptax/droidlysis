import unittest
from droidconfig import generalconfig

'''
To run tests:
source ./venv/bin/activate
python3 setup.py develop
cd tests
python3 ./droidconfig_test.py
'''


class DroidConfigTest(unittest.TestCase):
    def test_general_config(self):
        config = generalconfig(filename='../conf/general.conf', verbose=True)

    def test_bad_config(self):
        self.assertRaises(FileNotFoundError,
                          generalconfig,
                          '../conf/doesnotexist.conf')

if __name__ == '__main__':
    unittest.main()
