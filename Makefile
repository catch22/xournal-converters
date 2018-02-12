.PHONY: upload-release

all:

upload-release:
	rm -rf dist
	python -c "import wheel, pypandoc, twine"  # check upload dependencies
	python -c "import subprocess; version = subprocess.check_output('python setup.py --version', shell=True).strip(); assert b'dev' not in version, 'trying to upload dev release (%s)' % version"
	python setup.py sdist bdist_wheel
	#python setup.py upload
	twine upload dist/* --sign

pretty:
	yapf -ri *.py xournal_converters

lint:
	flake8 --ignore E401,E265,E501 *.py xournal_converters
