"""
Create boilerplate library structures from typical templates.
"""
import os
import sys
import textwrap

from . import incorporator, versioning


class TemplateMaker:
    def __init__(self, path, args={}):
        self.path = path
        self.args = args

    def prepare_path(self):
        if os.path.exists(self.path):
            if os.listdir(self.path):
                raise Exception("target path not empty, cowardly refusing to create bootstrap files")
        else:
            os.makedirs(self.path)

    def put_file(self, subpath, template, extra_args={}):
        fn = os.path.abspath(os.path.join(self.path, *subpath.split("/")))
        if not os.path.exists(os.path.dirname(fn)):
            os.makedirs(os.path.dirname(fn))
        template = textwrap.dedent(template)[1:-1]
        args = self.args.copy()
        args.update(extra_args)
        open(fn, "w").write(template % args)


def new_library(path, args):
    tm = TemplateMaker(path, args)
    tm.prepare_path()
    tm.put_file("README.md", """
        # %(libname)s
        
        %(descline)s
        
        ## Installation
        
        Install using:
        
            pip install %(libname)s
        
        Or clone this repo and run:
        
            python setup.py install
    
        ## Contact the author
        
        Contact %(author)s at %(author_email)s
            
    """)
    tm.put_file("setup.py", """
        import os
        
        
        %(incorporator_bootstrap_block)s
        
        
        quicklib.setup(
            name='%(libname)s',
            url="%(url)s",
            author='%(author)s',
            author_email='%(author_email)s',
            description='%(libname)s: %(descline)s',
            license='Copyright ACME Inc. (or) MIT',
            classifiers=[
                'Programming Language :: Python',
                'Development Status :: 4 - Beta',
                'Natural Language :: English',
                # ...
                # discover more at https://packaging.python.org/tutorials/distributing-packages/#classifiers
            ],
            version_module_paths=[
                os.path.join(os.path.dirname(__file__), "%(pkgname)s", "version.py"),
            ],
        )
    """, dict(
        incorporator_bootstrap_block=incorporator.create_bootstrap_block(),
    ))
    tm.put_file("%(pkgname)s/version.py" % args, """
        %(version_block)s
    """, dict(
        version_block=versioning.create_version_block()
    ))
    tm.put_file("%(pkgname)s/__init__.py" % args, """
    """)

def get_args():
    args = {}
    print("Library and package names:")
    print("  - the library name is what we use in 'pip install ...'")
    print("  - the package name is what we use in 'from ... import ...'")
    while True:
        args['libname'] = input("library name (e.g. mylibrary): ")
        if args['libname']:
            break
        else:
            print("library name cannot be left empty")
    args['pkgname'] = input("library name (e.g. mypackage, leave empty to reuse library name): ") or args['libname']
    args['descline'] = input("optional - describe your library in one line: ") or "Library description here"
    args['url'] = input("optional - url of website, documentation, repo etc: ") or "https://example.com/projects/%s" % args["libname"]
    args['author'] = input("optional - author name (person or company): ") or "Dr. contributor (or) Company Inc."
    args['author_email'] = input("optional - author contact email: ") or "you@example.com"
    return args


if __name__ == '__main__':
    # TODO: create a real script with argparse
    if os.listdir("."):
        print("error: run this script in an empty folder to bootstrap a new library there")
        sys.exit(1)
    args = get_args()
    new_library('.', args)
