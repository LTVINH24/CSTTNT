# Project 1 - Let's chase Pac-man!

## Installation Guide

### Pre-requisites

- Python (version `3.13.2` should be fine) and pip (should be installed with Python)
- _(Remember to add the Python installation path to your system's PATH variable)_

### Steps to install

1. **Clone the repository and navigate to the project directory:**

```bash
git clone https://github.com/LTVINH24/CSTTNT.git
cd CSTTNT
```

2. **Create a virtual environment:**

```bash
python -m venv .venv
```

> [!Tip]
> If you create a new virtual environment using VSCode, you can select to install the dependencies using the `requirements.txt` file\
> (_and you can skip step 3 and step 4 mentioned below_).

3. **Activate the virtual environment:**

- On Windows:

```bash
.venv\Scripts\activate
```

- On macOS/Linux:

```bash
source .venv/bin/activate
```

4. **Install the required packages** _(in the `.venv` terminal)_ :

```bash
pip install -r requirements.txt
```

5. _To run the game, use the following command:_

```bash
python -m src.main
```

6. _If you want to include an external package to the project, consider update the `requirements.txt` file using the following command:_

```bash
pip freeze > requirements.txt
```

## References

- Assets link: https://pixelaholic.itch.io/pac-man-game-art

## Notes:

- **_Consider install `Pylint` to enforce good coding practices._**
