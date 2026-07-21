from setuptools import setup, find_packages

setup(
    name="agent-haul-os-stable",
    version="1.0.0",
    description="Modular portable desktop GUI for multi-forwarder reverse-search and freight calculation",
    author="GitReverse Community",
    author_email="community@gitreverse.dev",
    url="https://github.com/gitreverse/agent-haul-os-stable",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "customtkinter==5.2.1",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "pandas==2.1.4",
        "pillow==10.2.0",
    ],
    entry_points={
        "console_scripts": [
            "agent-haul-os=main_desktop:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment :: GUI",
    ],
    keywords="shopping agent freight calculator reverse-search spreadsheet parser customtkinter",
    project_urls={
        "Bug Reports": "https://github.com/gitreverse/agent-haul-os-stable/issues",
        "Source": "https://github.com/gitreverse/agent-haul-os-stable",
    },
)
