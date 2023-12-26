import setuptools, os

with open("README.md", "r") as fh:
    long_description=fh.read()

with open('requirements.txt', 'r') as f:
    requirements=f.read().splitlines()

def filter_packages(root):
    def filter_packages(root, packages):
        packages.append(root.replace("/", "."))
        for path in os.listdir(root):
            if path=="__pycache__":
                continue
            newpath="%s/%s" % (root, path)
            if os.path.isdir(newpath):
                filter_packages(newpath, packages)
    packages=[]
    filter_packages(root, packages)
    return packages
    
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
    # - setuptools.find_packages() is completely broken
    # packages=setuptools.find_packages(),
    packages=filter_packages("pareto2"),
    install_requires=requirements,
    # - https://stackoverflow.com/a/57932258/124179
    # - to include yaml files
    # setup_requires=['setuptools_scm'],
    include_package_data=True
)
