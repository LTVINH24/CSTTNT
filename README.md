# Project 1 - Let's chase Pac-man!

## Installation Guide

### Pre-requisites

- Python (version `3.13.2` should be fine) and pip (should be installed with Python)
- _(Remember to add the Python installation path to your system's PATH variable)_

### Steps to install and run the code

1. **Open folder 22120363_22120378_22120387_22120434_22120443**

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

5. **To run the game, use these following commands:**
_Level 1: Blue Ghost (Inky) – Breadth-First Search (BFS)_

```bash
python -m src.levels.breadth_first_search
```

_Level 2: Pink Ghost (Pinky) – Depth-First Search (DFS)_

```bash
python -m src.levels.depth_first_search
```

_Level 3: Orange Ghost (Clyde) – Uniform-Cost Search (UCS)_

```bash
python -m src.levels.uniform_cost_search
```

_Level 4: Red Ghost (Blinky) – A* Search (A*)_

```bash
python -m src.levels.a_star_search
```

_Level 5: Parallel Execution_

```bash
python -m src.levels.ghost_official_assembly
```
>  **Note:** Since the ghosts BFS, UCS, and A* reach Pacman faster, there are some cases where DFS cannot reach Pacman.  
> As a result, DFS ends up looping around trying to find a way. This is not a bug.

_Level 6: User-Controlled Pac-Man_

```bash
python -m src.levels.pacman_move
```

7. **For evaluating and comparing the performance of those algorithms, you can run:** `python -m src.tests.test_main`. 

  - This will display a list of algorithms, and you can select any algorithms to test. 
  - The program will automatically run 5 different test cases with various spawn positions of Pacman and Ghost.
  - These are 5 sceniors:
    * 1. Minimum Euclidean distance between spawn points.
    * 2. Maximum Euclidean distance between spawn points.
    * 3. Second smallest Euclidean distance.
    * 4. Minimum X-axis difference between spawn points.
    * 5. Pacman at highest position (min Y), Ghost at lowest position (max Y).
  - You will recieve file *.csv in folder `results\` after run one algorithms.

- For visualization:

  - After you test all 4 algorithms and receive 4 file *.csv in folder `results\`, you can open this location `tests\` to run file `visualization.ipynb` using Jupyter Notebook or JupyterLab and receive the inspects about the strengths and weaknesses of each pathfinding algorithms in different scenarios.

8. _If you want to include an external package to the project, consider update the `requirements.txt` file using the following command:_

```bash
pip freeze > requirements.txt
```

## References

- Assets link: https://pixelaholic.itch.io/pac-man-game-art

## Notes:

- **_Consider install `Pylint` to enforce good coding practices._**

## Report and Youtube link:

- **_Report link:_**  <https://docs.google.com/document/d/1jXCxDf31eSMlfZARareK2gSF7EgZmWJm/edit?usp=sharing&ouid=106570760457542661537&rtpof=true&sd=true>.
- **_Youtube link:_** <https://www.youtube.com/watch?v=p8pXfaaCk3Y>.