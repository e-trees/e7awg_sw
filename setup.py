import setuptools
 
setuptools.setup(
    name="e7awg_sw",
    version="1.0",
    author="e-trees.Japan, Inc.",
    author_email="labo@e-trees.jp",
    description="e7awg manipulator",
    long_description="e7awg manipulator",
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GPL",
        "Operating System :: OS Independent",
    ],
    install_requires=["numpy", "matplotlib", "pylabrad"],
)
