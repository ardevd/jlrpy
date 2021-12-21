import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jlrpy",
    version="1.4.1",
    author="Edvard",
    author_email="5gk633atf@relay.firefox.com",
    description="Control your Jaguar I-Pace",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ardevd/jlrpy",
    py_modules=['jlrpy'],
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
    ],
)
