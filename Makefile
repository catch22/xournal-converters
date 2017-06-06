.PHONY: upload-release

all:

upload-release:
	python -c "import wheel, pypandoc"  # check upload dependencies
	python -c "import subprocess; version = subprocess.check_output('python setup.py --version', shell=True).strip(); assert 'dev' not in version.decode(), 'trying to upload dev release (%s)' % version"
	python setup.py sdist bdist_wheel
	#python setup.py upload
	twine upload dist/* --sign
