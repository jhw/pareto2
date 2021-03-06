"""
- https://stackoverflow.com/questions/50585246/pip-install-creates-only-the-dist-info-not-the-package
- https://stackoverflow.com/questions/32688688/how-to-write-setup-py-to-include-a-git-repo-as-a-dependency
- https://stackoverflow.com/questions/1612733/including-non-python-files-with-setup-py
"""

import os, setuptools

with open("README.md", "r") as fh:
    long_description=fh.read()

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

"""
- https://stackoverflow.com/a/59109622/124179
"""

def format_dependencies(root="requirements.txt"):
    def clean_row(fn):
        def wrapped(row):
            return fn(row.replace(" ", "").split("#")[0])
        return wrapped
    def is_git(row):
        return row.startswith("git")
    @clean_row
    def format_git(row):
        pkgname=row.split("@")[1].split("/")[-1].split(".")[0]
        return "%s@%s" % (pkgname, row)
    @clean_row
    def format_pip(row):
        return row
    def format_dep(row):
        return format_git(row) if is_git(row) else format_pip(row)
    return [format_dep(row)
            for row in open(root).read().split("\n")
            if (row!='' and
                not row.startswith("#"))]

setuptools.setup(
    name="pareto2",
    version="0.1.8",
    author="jhw",
    author_email="justin.worrall@gmail.com",
    description="OTP for serverless",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhw/pareto2",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # packages=setuptools.find_packages(),
    packages=filter_packages("pareto2"),
    install_requires=format_dependencies(),
    # https://stackoverflow.com/a/57932258/124179
    setup_requires=['setuptools_scm'],
    include_package_data=True
)
