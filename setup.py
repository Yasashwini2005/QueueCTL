from setuptools import setup, find_packages

setup(
    name='queuectl',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click==8.1.7',
        'colorama==0.4.6',
        'tabulate==0.9.0',
    ],
    entry_points={
        'console_scripts': [
            'queuectl=queuectl.cli:main',
        ],
    },
    author='Your Name',
    description='CLI-based background job queue system',
    python_requires='>=3.7',
)