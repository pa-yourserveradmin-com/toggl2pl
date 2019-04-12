from setuptools import setup
import yaml


def readme():
    with open('README.md', 'r') as fp:
        return fp.read()


def version():
    with open('.gitlab-ci.yml', 'r') as fp:
        return yaml.safe_load(fp)['variables']['PACKAGE_VERSION']


setup(
    author='Andrew Poltavchenko',
    author_email='pa@yourserveradmin.com',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    description='Python module and tool to simplify time entries export from Toggl into Project Laboratory',
    entry_points={
        'console_scripts':
            [
                'toggl2pl=toggl2pl.__main__:main'
            ]
    },
    include_package_data=True,
    install_requires=[
        'requests',
        'tabulate',
        'tqdm',
        'yaml'
    ],
    license='MIT',
    long_description=readme(),
    long_description_content_type='text/markdown',
    name='toggl2pl',
    packages=[
        'toggl2pl'
    ],
    scripts=[
        'scripts/toggl2pl'
    ],
    url='https://git-y.yourserveradmin.com/pa/toggl2pl',
    version=version(),
)
