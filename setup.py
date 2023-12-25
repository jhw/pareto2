import setuptools

with open("README.md", "r") as fh:
    long_description=fh.read()

with open('requirements.txt', 'r') as f:
    requirements=f.read().splitlines()
    
setuptools.setup(
    name="pareto2",
    version="0.7.0",
    author="jhw",
    author_email="justin.worrall@gmail.com",
    description="An SDK for serverless apps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhw/pareto2",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    install_requires=requirements,
    include_package_data=True
)
