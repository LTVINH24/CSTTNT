# Project 1 - Let's chase Pac-man!

## Important Note

- To run the levels:

  ```bash
  python -m src.levels.<level_name>
  ```

  - For example: `python -m src.levels.ghost_parade` or `python -m src.levels.level_template` (both should be working fine).

- To implement a new pathfinding algorithm:

  - Create a function in a new file in the `src/pathfinding` directory (e.g., `depth_first_search_pathfinder.py`), using the `src/pathfinding/path_finder_template.py` as a template.
  - To add the test level, create a new file in the `src/levels` directory (e.g., `depth_first_search.py`), using the `src/levels/level_template.py` as a template (you only need to change the `path_finder` param in the `build_path_dispatcher` function call).

- For permormance assessment, you `src/pathfinding/pathfinding_monitor.py` and adjust as you need.

- _Remember to create a new branch for each new feature you want to implement. Pull request to the `main` branch when you are done._ :smiley:

## To-dos:

- Add the visualization for the path found.
- Moving the pacman using `maze_graph`.
- Ghost/pacman collision detection.
- Ghosts colliding with other ghosts.
- Ghost and player spawn-point separation.
- All levels accessible from the main menu.
- Higher pixel resolution for better visualization (e.g., 32x32 instead of 16x16).
- Animation for pacman (not really needed, but it would be nice to have).

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
