#!/usr/bin/env python3
"""Setup script for VMU Pro SD Save Importer"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='vmupro-importer',
    version='1.0.0',
    description='Automatically organize Dreamcast VMU saves for VMU Pro',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='8BitMods Community',
    url='https://github.com/yourusername/VMUPro_SDSaveImporter',
    license='MIT',

    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['data/*.json'],
    },

    install_requires=[
        'click>=8.0.0',
        'colorama>=0.4.4',
        'tqdm>=4.65.0',
        'pandas>=1.5.0',
        'requests>=2.28.0',
    ],

    entry_points={
        'console_scripts': [
            'vmupro-import=vmupro_importer:main',
        ],
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    python_requires='>=3.8',

    keywords='dreamcast vmu vmupro saves retro gaming',
)
