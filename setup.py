from setuptools import setup

setup(
    name="mermaid-changelog",
    description="",
    version="0.2.3",
    py_modules=["mermaid_changelog"],
    install_requires=["boto3==1.21.31", "py-trello==0.15.0"],
    entry_points="""
        [console_scripts]
        chlog=mermaid_changelog:main
    """,
)
