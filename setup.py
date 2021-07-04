setup(
    name="SAFARI-detect",
    version="1.0.0",
    description="SAFARI data analysis application",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/SINS-Lab/SEA-SAFARI",
    author="Patrick Johnson",
    author_email="prjohns@clemson.edu",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    packages=["data_files","spec_files"],
    include_package_data=True,
    install_requires=[
        "matplotlib", "scipy", "numpy"
    ],
    entry_points={"console_scripts": ["safari_detect=safari_detect.__main__:spawn_gui"]},
)