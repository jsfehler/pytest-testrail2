from setuptools import setup


def read_file(filename: str):
    with open(filename) as f:
        return f.read()


setup(
    name='pytest-testrail2',
    description='A pytest plugin to upload results to TestRail.',
    long_description=read_file('README.rst'),
    version='1.0.1',
    author='Joshua Fehler',
    url='http://github.com/jsfehler/pytest-testrail2/',
    packages=[
        'pytest_testrail',
    ],
    package_dir={'pytest_testrail': 'pytest_testrail'},
    install_requires=[
        'pytest>=7.2.0,<8.0',
        'requests>=2.20.0,<3.0',
        'inori>=0.0.8,<1.0',
        'filelock>=3.6.0,<4.0',
    ],
    include_package_data=True,
    entry_points={'pytest11': ['pytest-testrail = pytest_testrail.plugin']},
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
