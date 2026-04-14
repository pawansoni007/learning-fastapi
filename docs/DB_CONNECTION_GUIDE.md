# How Database Connection Works in FastAPI + SQLModel

---

## Pre-requisites

### 1. What is `yield`?

A normal function runs and returns — it's done:

```python
def make_tea():
    boil_water()
    return tea  # done
```

A function with `yield` pauses, gives you something, and resumes after you're done:

```python
def make_tea():
    boil_water()
    yield tea       # pause here, give tea to whoever asked
    clean_cup()     # runs AFTER the caller is done using the tea
```

`yield` = "here, take this, I'll wait. When you're done, I'll clean up."

---

### 2. What is `lifespan`?

`lifespan` is a hook FastAPI gives you to run code at **startup** and **shutdown** of the app.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP: runs once when app starts ---
    create_db_and_tables()
    yield
    # --- SHUTDOWN: runs once when app stops ---
    # cleanup code here (if any)

app = FastAPI(lifespan=lifespan)
```

Everything **before** `yield` = startup.  
Everything **after** `yield` = shutdown.

You pass it to `FastAPI()` so it knows to use it.

---

## Step-by-Step: Database Connection

### Step 1 — Define your model with `table=True`

```python
from sqlmodel import SQLModel, Field

class Campaign(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    due_date: str
```

`table=True` tells SQLModel: "this is a real database table, not just a validation model."  
SQLModel automatically registers this class internally in `SQLModel.metadata`.

---

### Step 2 — Create the engine

```python
from sqlmodel import create_engine

sqlite_filename = "database.db"
sql_url = f"sqlite:///{sqlite_filename}"

connect_args = {"check_same_thread": False}

engine = create_engine(sql_url, connect_args=connect_args)
```

- `sql_url` — tells the engine where the database file is and which protocol to use (`sqlite:///`)
- `check_same_thread: False` — SQLite restricts connections to the thread that created them. FastAPI handles multiple requests concurrently, so we disable this restriction and let SQLModel handle thread safety itself
- `engine` — the core gateway object. Every read/write to the database goes through it

---

### Step 3 — Create tables at startup

```python
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

- `SQLModel.metadata` — the internal list of all models registered with `table=True`
- `create_all(engine)` — looks at that list and runs `CREATE TABLE IF NOT EXISTS` for each one
- This is safe to call every time the app starts — it won't recreate tables that already exist

---

### Step 4 — Wire it into lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # create tables before app accepts any requests
    yield

app = FastAPI(lifespan=lifespan)
```

This guarantees tables exist before the first request hits any endpoint.

---

### Step 5 — Create a session

A **session** is a temporary conversation with the database. You open it, do your reads/writes, then close it. Each request gets its own session.

```python
from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session   # give the session to the endpoint
                        # after the endpoint finishes, session closes automatically
```

- `Session(engine)` — opens a connection using the engine
- `yield session` — hands the session to whoever needs it (the endpoint)
- After the endpoint returns, the `with` block exits and closes the session automatically

---

### Step 6 — Dependency Injection with `Depends`

FastAPI has a built-in DI system. You tell it "this endpoint needs a session" and FastAPI calls `get_session()` automatically for every request.

```python
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[Session, Depends(get_session)]
```

- `Depends(get_session)` — tells FastAPI: "call `get_session()` and inject the result"
- `Annotated[Session, ...]` — wraps it with type info so your editor knows it's a `Session`
- `SessionDep` — just a shortcut alias so you don't repeat `Annotated[Session, Depends(get_session)]` in every endpoint

---

### Step 7 — Use the session in endpoints

```python
@app.post("/campaigns")
def create_campaign(body: Campaign, session: SessionDep):
    session.add(body)       # stage the new record
    session.commit()        # write to the database
    session.refresh(body)   # fetch the updated record back (e.g. auto-generated id)
    return body

@app.get("/campaigns/{id}")
def get_campaign(id: int, session: SessionDep):
    campaign = session.get(Campaign, id)  # read by primary key
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
```

FastAPI sees `session: SessionDep` in the parameter, calls `get_session()`, and passes the session in. You never call `get_session()` yourself.

---

## Full Flow (top to bottom)

```
1. App starts
        ↓
2. lifespan runs → create_db_and_tables()
        ↓
3. SQLModel.metadata.create_all(engine) → tables created in database.db
        ↓
4. App is ready, accepting requests
        ↓
5. Request comes in to an endpoint that has `session: SessionDep`
        ↓
6. FastAPI calls get_session() → opens Session(engine) → yields session
        ↓
7. Endpoint receives the session, uses it to read/write data
        ↓
8. Endpoint returns response
        ↓
9. get_session() resumes after yield → session closes automatically
```

---

## Quick Reference

| Thing | What it does |
|---|---|
| `engine` | Gateway to the database file |
| `create_db_and_tables()` | Creates tables from your models |
| `lifespan` | Runs startup/shutdown code |
| `Session` | A single conversation with the DB |
| `get_session()` | Opens a session, yields it, closes it after use |
| `Depends(get_session)` | Tells FastAPI to inject the session automatically |
| `SessionDep` | Shortcut alias for the above |
