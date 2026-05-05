# Snickr

### Deployment & Launching

- Clone or download the project

- Create and activate a virtual environment

```bash
cd ~/Code/Snickr
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

- Install dependencies

```bash
pip install -r requirements.txt
```

- Create the PostgreSQL database

```bash
psql -U postgres
```

- Configure the environment variables (create `.env`)

```bash
SECRET_KEY=any-long-random-string
DEBUG=True
DB_NAME=snickr
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

- Create Django session and start the server

```bash
python manage.py migrate
python manage.py runserver
```