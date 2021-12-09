# Corpalizer
#### Created by Sam Xifaras for CS3200 Database Design

### Contents
* [About the Project](#1-about-the-project)
* [How to Run the App](#2-how-to-run-the-app)

## 1. About the Project
Read the original proposal [here](link), and read the final report [here](link)

## 2. How to Run the App
Clone this repository or unpack the zip archive from the `final-submission` tag, and then run the following commands.
I would recommend running the frontend and backend commands in two separate shells.
This guide assumes that you have a running MySQL instance with an imported schema of the Corpalizer database. 
If you do not have this dump, feel free to contact me at [s.xifaras999@gmail.com](mailto:s.xifaras999@gmail.com). 

In `backend/`:
1. If you would like to create a virtual environment, run the following, if not, skip to step 4
1. `python -m venv venv`
1. `source ./venv/bin/activate`. To deactivate the virtual environment later, run `deactivate` in the same terminal.
1. `pip install -r requirements.txt`
1. `cp src/config.example.py src/config.py`
1. Open up the newly created `src/config.py` and fill in the credentials to connect to your MySQL instance
1. Run the app with `python src/main.py`, and keep an eye out for the like that looks like this: `* Running on http://127.0.0.1:<port_number>/ (Press CTRL+C to quit)`. The port number will probably be 5000. Save this information for the frontend setup.

In `frontend/`:
1. `npm i` installs dependencies, or if you have yarn, `yarn` also works.
1. `cp .env.example .env`
1. Populate the newly created `.env` file with the scheme, host, and port information from the last step of the backend setup.
1. Run the app with `npm run start` or `yarn start`.
