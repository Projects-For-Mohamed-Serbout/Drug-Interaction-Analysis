"""Setup script for the Python project."""

from setuptools import setup, find_packages

setup(
    name='Drug-Interaction-Analysis',
    version='1.0.0',
    description='Efficient Drug Interaction Analysis using NoSQL Databases and NLP Techniques for Enhanced Patient Safety',
    author='Mohamed Serbout',
    author_email='m.serbout7@outlook.com',
    packages=find_packages(),
    install_requires=[
        'pylint',
        'pytest'
    ],
    python_requires='>=3.9',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
