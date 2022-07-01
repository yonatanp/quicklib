print("examplemodule2 being imported")

def example_function_2():
    print("example_function_2 running")


if __name__ == '__main__':
    print("examplemodule2 main running")
    # this gets created by our setup script
    try:
        from .__version__ import __version__
    except ImportError:
        __version__ = "<working locally>"
    print("examplepackage2 version:", __version__)
    # are we in a or b variant?
    try:
        import a_only
        print("we are in '2a' variant")
    except:
        pass
    try:
        import b_only
        print("we are in '2b' variant")
    except:
        pass
