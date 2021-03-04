from setuptools import setup, find_packages
# To use a consistent encoding
from os import path
from itertools import chain


# Get the long description from the README file
def get_long_description():
    with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'),
              encoding='utf-8') as f:
        lines = f.readlines()
        i = -1
        while '=====' not in lines[i]:
            i -= 1
        return "".join(lines[:i])


setup(
    name='uhm',
    version='0.0.4',
    description='Code to remove filler words from videos',
    long_description=get_long_description(),
    project_urls={
        'Source': 'https://github.com/adammoss/uhm',
        'Tracker': 'https://github.com/adammoss/uhm/issues',
        'Licensing': 'https://github.com/adammoss/uhm/blob/master/LICENCE.txt'
    },
    author='Adam Moss',
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Astronomy',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    python_requires='>=3.6.1',
    packages=find_packages(),
    install_requires=['numpy>=1.12.0', 'matplotlib>=3.3.4', 'ibm-watson>=5.1.0', 'librosa>=0.8.0'],
    entry_points={
        'console_scripts': [
            'deuhm=uhm.deuhm:run',
        ],
    },
)
