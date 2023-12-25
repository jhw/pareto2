import setuptools, os

with open("README.md", "r") as fh:
    long_description=fh.read()

with open('requirements.txt', 'r') as f:
    requirements=f.read().splitlines()

"""
- because setuptools.find_packages() is useless and broken
"""

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
    # packages=setuptools.find_packages(),
    # packages=filter_packages("pareto2"),
    packages=["pareto2"],
    # package_data={"pareto2", ["**/*.yaml"]},
    install_requires=requirements,
    include_package_data=True
)
