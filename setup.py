import setuptools


with open("README.md", "r", encoding='UTF-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="jlrpy",
    version="1.7.0",
    author="ardevd",
    author_email="5gk633atf@relay.firefox.com",
    description="Control your Jaguar I-Pace",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ardevd/jlrpy",
    py_modules=['jlrpy'],
    install_requires=['requests>=2.26.0'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
    ],
)
