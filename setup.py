from setuptools import setup

setup(
    name='toggl2pl',
    version='1.0.1',
    packages=[
        'toggl2pl'
    ],
    scripts=[
        'scripts/toggl2pl'
    ],
    url='https://git-y.yourserveradmin.com/pa/toggl2pl',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    author='Andrew Poltavchenko',
    author_email='pa@yourserveradmin.com',
    description='Python module and tool to simplify import of time entries from Toggl into Project Laboratory',
    long_description='README',
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts':
            [
                'toggl2pl=toggl2pl.__main__:main'
            ]
    },
    include_package_data=True,
)
