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
python -c 'import minimalpkg.__version__; print("minimalpkg version:", minimalpkg.__version__.__version__)'
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
python -c 'import manifested.__version__; print("manifested version:", manifested.__version__.__version__)'
manifested-show-text | grep "The text here is displayed when running manifested-show-text"
# this is broken, reactivate when manifest=... works for excluding files
# manifested-verify-exclusion
popd
cd ..
