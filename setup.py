from setuptools import setup, find_packages

setup(
    name='pg_index_insight',
    version='0.1',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),  # Read requirements from file
    entry_points={
        'console_scripts': [
            'pg_index_insight = pg_index_insight.cli:main',
        ],
    },
)
