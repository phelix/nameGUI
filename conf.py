import argparse

def get_args(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument('--datadir',
                   help="Specify the nameGUI data directory.")

    parser.add_argument('--namecoindatadir',
                   help="Specify the Namecoin data directory.")

    return parser.parse_args(args)

if __name__ == '__main__':  # test
    import sys

    arguments = None
    if not sys.argv[1:]:
        arguments = (r'--namecoindatadir=.',)        
        print "using fabricated arguments:", arguments

    args = get_args(arguments)
    print "namecoindatadir:", args.namecoindatadir
