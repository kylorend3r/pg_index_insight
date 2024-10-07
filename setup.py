from setuptools import setup, find_packages

setup(
    name='pg_index_insight',  # The name of your package
    version='0.1.0',  # Initial version
    author='Huseyin Demir',
    author_email='huseyin.d3r@gmail.com',
    description='A Python CLI tool to analyze PostgreSQL indexes',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/kylorend3r/pg_index_insightt',  # Link to your project
    packages=find_packages(),
    install_requires=[
        'click',  # List your dependencies here
        'psycopg2',
        'tabulate'
    ],
    entry_points={
        'console_scripts': [
            'pg_index_insight = pg_index_insight.cli:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',  # Python version compatibility
)