from setuptools import setup
import yaml


def readme():
    with open('README.md', 'r') as fp:
        return fp.read()


def requirements():
    with open('requirements.txt', 'r') as fp:
        return fp.read().split()


def version():
    with open('.gitlab-ci.yml', 'r') as fp:
        return yaml.safe_load(fp)['variables']['PACKAGE_VERSION']


setup(
    author='Andrew Poltavchenko',
    author_email='pa@yourserveradmin.com',
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    description='Python module and tool to simplify time entries export from Toggl into Project Laboratory',
    entry_points={
        'console_scripts':
            [
                'toggl2pl=toggl2pl.__main__:main'
            ]
    },
    include_package_data=True,
    install_requires=requirements(),
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
    url='https://github.com/pa-yourserveradmin-com/toggl2pl',
    version=version(),
)
