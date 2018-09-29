from setuptools import setup

setup(
    name='standups',
    version='0.1.0',
    author='The Servo Project Developers',
    url='https://github.com/servo/standups/',
    description='A service that tracks team status reports.',

    packages=['standups'],
    install_requires=[
        'flask',
        'tinydb',
    ],
    entry_points={
        'console_scripts': [
            'standups=standups.flask_server:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
