from setuptools import setup

setup(
    name="mermaid-changelog",
    description="",
    version="0.2.2",
    py_modules=["mermaid_changelog"],
    install_requires=["boto3==1.9.195", "py-trello==0.15.0"],
    entry_points="""
        [console_scripts]
        chlog=mermaid_changelog:main
    """,
)
