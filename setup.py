"""Main setup for submitting to PyPi"""
import setuptools


def main():
    """Main setup for submitting to PyPi"""
    with open("README.md", "r") as fh:
        long_description = fh.read()

    setuptools.setup(
        name="flask_opencv_streamer",
        version="1.4",
        url="https://github.com/oitsjustjose/Flask-OpenCV-Streamer",
        author="Jose Stovall",
        author_email="stovallj1995@gmail.com",
        description="A Python package for easily streaming OpenCV footage, even with authentication",
        long_description=long_description,
        long_description_content_type="text/markdown",
        license="GNU General Public License 3",
        packages=setuptools.find_packages(),
        install_requires=["cryptography", "flask", "opencv-python"],
    )


if __name__ == "__main__":
    main()
