from setuptools import setup
import yaml

with open('.gitlab-ci.yml', 'r') as fp:
    version = yaml.safe_load(fp)['variables']['PACKAGE_VERSION']

with open('README.md', 'r') as fp:
    long_description = fp.read()

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
    long_description=long_description,
    long_description_content_type='text/markdown',
    name='toggl2pl',
    packages=[
        'toggl2pl'
    ],
    scripts=[
        'scripts/toggl2pl'
    ],
    url='https://git-y.yourserveradmin.com/pa/toggl2pl',
    version=version,
)
