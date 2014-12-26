from setuptools import setup, find_packages
from codecs import open
from os.path import abspath, dirname, join

with open(join(abspath(dirname(__file__)), 'README.md'), encoding='utf-8') as fp:
  long_description = fp.read()

setup(
  name='xournal-converters',
  version='0.0.1',
  description='Python scripts for converting Xournal documents to HTML and PDF.',
  long_description=long_description,
  url='https://github.com/catch22/xournal-converters',
  author='Michael Walter',
  author_email='michael.walter@gmail.com',
  license='MIT',
  classifiers=[
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2',
  ],
  install_requires=['reportlab'],
  packages=find_packages(),
  entry_points={
    'console_scripts': [
      'xoj2pdf=xournal_converters.pdf:main',
      'xoj2html=xournal_converters.html:main',
    ],
  },
)
