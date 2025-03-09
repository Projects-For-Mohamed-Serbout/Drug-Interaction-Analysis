"""Setup script for the Python project."""

from setuptools import setup, find_packages

setup(
    name='my_python_project',
    version='1.0.0',
    description='A sample Python project',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'pylint',
        'pytest'
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'my_command=my_package.module:main_function'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
