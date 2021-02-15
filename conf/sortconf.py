import argparse
import configparser

DEFAULTSECT = 'default'

def get_arguments():
    parser =  argparse.ArgumentParser(description="Sort conf files by alphabetic order of sections", prog='sortconf')
    parser.add_argument('-i', '--input', help='Input conf file', action='store', default='./kit.conf')
    parser.add_argument('-o', '--output', help='Output file', action='store', default='./sorted.conf')
    parser.add_argument('-v', '--verbose', help='get more detailed messages', action='store_true')
    args = parser.parse_args()
    return args
    

class OrderedRawConfigParser( configparser.RawConfigParser ):
    """
    Overload standart Class ConfigParser.RawConfigParser
    """
    def __init__( self, defaults = None, dict_type = dict ):
        configparser.RawConfigParser.__init__( self, defaults = None, dict_type = dict )

        def write(self, fp):
            """Write an .ini-format representation of the configuration state."""
            if self._defaults:
                fp.write("[%s]\n" % DEFAULTSECT)
                for key in sorted( self._defaults ):                
                    fp.write( "%s = %s\n" % (key, str( self._defaults[ key ] ).replace('\n', '\n\t')) )
                    fp.write("\n")
            for section in self._sections:
                fp.write("[%s]\n" % section)
                for key in sorted( self._sections[section] ): 
                    if key != "__name__":
                        fp.write("%s = %s\n" %
                                 (key, str( self._sections[section][ key ] ).replace('\n', '\n\t')))    
                fp.write("\n")

def main():
    args = get_arguments()
    parser = OrderedRawConfigParser()
    parser.read(args.input)
    output = open(args.output,'w')
    parser.write(output)
    output.close()
    
    
if __name__ == "__main__":
    main()
