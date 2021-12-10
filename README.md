# Corpalizer
#### Created by Sam Xifaras for CS3200 Database Design

### Contents
* [About the Project](#1-about-the-project)
* [How to Run the App](#2-how-to-run-the-app)

## 1. About the Project
Read the original proposal [here](https://docs.google.com/document/d/13BBvZktMfOu3Z7d5VEU8aZa-Elv1IkQoPJYXr7gq_l4/edit?usp=sharing), and read the final report [here](https://docs.google.com/document/d/1aQUGsqzdQs1JsQLwHd72P8X1lMnRD-y4onxBiEZpeps/edit?usp=sharing)

## 2. How to Run the App
Clone this repository or unpack the zip archive from the `final-submission` tag, and then run the following commands.
I would recommend running the frontend and backend commands in two separate shells.
This guide assumes that you have a running MySQL instance with an imported schema of the Corpalizer database. 
If you do not have this dump, feel free to contact me at [s.xifaras999@gmail.com](mailto:s.xifaras999@gmail.com).
This guide also assumes you are on a Unix-like system, such as Mac or Linux. 

In case the following steps don't work as expected, here is the setup of my machine:
* `python` 3.8.9, `pip` 21.3.1 ([download](https://www.python.org/downloads/))
* `node` 12.18.3, `npm` 6.14.6 ([download](https://nodejs.org/en/download/))
* `yarn` 1.22.10 (optional, install with `npm install --global yarn` once node is installed)

Versions of packages can be found in `frontend/package.json` and `backend/requirements.txt`.

**In `backend/`:**
1. If you would like to create a virtual environment, run the following, if not, skip to step 4
1. `python -m venv venv`
1. `source ./venv/bin/activate`. To deactivate the virtual environment later, run `deactivate` in the same terminal.
1. `pip install -r requirements.txt`
1. `mkdir -p documents`. This will create the folder where document uploads are stored if it doesn't exist already. 
1. `cp src/config.example.py src/config.py`
1. Open up the newly created `src/config.py` and fill in the credentials to connect to your MySQL instance. There should be no need to change the default `DOCUMENTS_DIR` variable.
1. Run the app with `python src/main.py`, and keep an eye out for the like that looks like this: `* Running on http://127.0.0.1:<port_number>/ (Press CTRL+C to quit)`. The port number will probably be 5000. Save this information for the frontend setup.

**In `frontend/`:**
1. `npm i` installs dependencies, or if you have yarn, `yarn` also works.
1. `cp .env.example .env`
1. Populate the newly created `.env` file with the scheme, host, and port information from the last step of the backend setup.
1. Run the app with `npm run start` or `yarn start`.

