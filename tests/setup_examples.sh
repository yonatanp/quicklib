#!/usr/bin/env bash
set -e

cd $(dirname $0)/../examples

pip_uninstall_examples() {
    for pkg in examplelibrary examplelibrary_2a examplelibrary_2b minimal manifested; do
        pip uninstall -y $pkg || true
    done
}

# examplelibrary
cd examplelibrary
rm -rf build dist
pip_uninstall_examples
python setup.py sdist
pip install dist/examplelibrary-*.tar.gz
pushd /tmp
python -c 'import examplepackage.examplemodule; examplepackage.examplemodule.example_function(); print(examplepackage.examplemodule)'
examplescript foo bar baz | grep "doing something on \['foo', 'bar', 'baz'\]"
popd
cd ..

# examplelibrary_2a
cd examplelibrary2
rm -rf build dist
pip_uninstall_examples
python setup_examplelibrary_2a.py sdist
pip install dist/examplelibrary_2a-*.tar.gz
pushd /tmp
python -c 'import examplepackage2; print(examplepackage2)'
examplescript2a | grep "we are in '2a' variant"
popd
cd ..

# examplelibrary_2b
cd examplelibrary2
rm -rf build dist
pip_uninstall_examples
python subdir/setup_examplelibrary_2b.py sdist
pip install dist/examplelibrary_2b-*.tar.gz
pushd /tmp
python -c 'import examplepackage2; print(examplepackage2)'
examplescript2b | grep "we are in '2b' variant"
popd
cd ..

# minimal (using quicklib-setup)
cd minimal
rm -rf build dist
pip_uninstall_examples
quicklib-setup sdist
pip install dist/minimal-*.tar.gz
pushd /tmp
python -c 'from __future__ import print_function; import minimalpkg.__version__; print("minimalpkg version:", minimalpkg.__version__.__version__)'
how-minimal | grep "so minimal"
popd
cd ..

# manifested
cd manifested
rm -rf build dist
pip_uninstall_examples
quicklib-setup sdist
pip install dist/manifested-*.tar.gz
pushd /tmp
python -c 'from __future__ import print_function; import manifested.__version__; print("manifested version:", manifested.__version__.__version__)'
manifested-show-text | grep "The text here is displayed when running manifested-show-text"
# this is broken, reactivate when manifest=... works for excluding files
# manifested-verify-exclusion
popd
cd ..

# locking
cd locking
rm -rf build dist
quicklib-setup sdist
pip install dist/app-lib-*.tar.gz
pushd /tmp
lockapp
popd
pip uninstall -y app-lib
quicklib-lock sdist --find-links ./dist
pip install dist/locked-app-lib-*.tar.gz --find-links ./dist
pushd /tmp
lockapp
pip freeze | grep "^app-lib=="
pip freeze | grep "^locked-app-lib=="
pip uninstall -y app-lib
pip uninstall -y locked-app-lib
popd
cd ..

# locking a public external library
cd locking_external
rm -rf build dist
quicklib-lock sdist
pip install dist/frozen-dill-*.tar.gz
pushd /tmp
pip freeze | grep "^dill==0.2.5$"
pip freeze | grep "^frozen-dill==0.2.5+"
# XXX: this dependency is only installed on windows, replace dill with another example
# pip freeze | grep "^pyreadline==2.1$"
# pip uninstall -y dill frozen-dill pyreadline
pip uninstall -y dill frozen-dill
popd
# now install an even older version with cmdline argument
rm -rf build dist
quicklib-lock sdist --version 0.2
pip install dist/frozen-dill-*.tar.gz
pushd /tmp
pip freeze | grep "^dill==0.2$"
pip freeze | grep "^frozen-dill==0.2+"
# XXX: this dependency is only installed on windows, replace dill with another example
# if { pip freeze | grep "pyreadline"; }; then false; fi
pip uninstall -y dill frozen-dill
popd
cd ..
