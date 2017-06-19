from setuptools import setup
from os.path import abspath, dirname, join
import ast, io, re

# determine __version__ from pw.py source (adapted from mitsuhiko)
VERSION_RE = re.compile(r'__version__\s+=\s+(.*)')

with io.open('xournal_converters/__init__.py', encoding='utf-8') as fp:
    version_code = VERSION_RE.search(fp.read()).group(1)
    version = str(ast.literal_eval(version_code))

# read long description and convert to RST
long_description = io.open(
    join(dirname(abspath(__file__)), 'README.md'), encoding='utf-8').read()
try:
    import pypandoc
    long_description = pypandoc.convert(long_description, 'rst', format='md')
except ImportError:
    pass

# invoke setuptools
setup(
    name='xournal-converters',
    version=version,
    description='Python scripts for converting '
    'Xournal documents to HTML and PDF.',
    long_description=long_description,
    url='https://github.com/catch22/xournal-converters',
    author='Michael Walter',
    author_email='michael.walter@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
    ],
    install_requires=['click', 'reportlab', 'PyPDF2'],
    extras_require={
        'dev': ['pypandoc', 'wheel', 'yapf', 'flake8'],
    },
    packages=['xournal_converters'],
    entry_points={
        'console_scripts': [
            'xoj2pdf = xournal_converters.pdf:main',
            'xoj2html = xournal_converters.html:main',
        ],
    }, )
