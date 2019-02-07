import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jlrpy",
    version="1.1.0",
    author="Edvard Holst",
    author_email="edvard.holst@gmail.com",
    description="Communicate and control your Jaguar I-Pace",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ardevd/jlrpy",
    py_modules=['jlrpy'],
    install_requires=[
        'uuid',
        'datetime',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
