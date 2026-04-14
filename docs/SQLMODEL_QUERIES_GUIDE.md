# SQLModel CRUD Query Patterns

---

## The 5 Core Operations

### 1. INSERT — add a new row

```python
from models.models import Campaign

@app.post("/campaigns")
def create_campaign(body: CampaignCreate, session: SessionDep):
    campaign = Campaign.model_validate(body)  # CampaignCreate → Campaign (DB model)
    session.add(campaign)     # stage it
    session.commit()          # write to DB
    session.refresh(campaign) # pull back saved record (gets the auto id)
    return campaign
```

---

### 2. SELECT ALL — get every row

```python
from sqlmodel import select

@app.get("/campaigns")
def get_campaigns(session: SessionDep):
    campaigns = session.exec(select(Campaign)).all()
    return campaigns
```

- `select(Campaign)` = `SELECT * FROM campaign`
- `.exec()` runs the query
- `.all()` returns a list of all rows

---

### 3. SELECT ONE — get by ID

```python
@app.get("/campaigns/{id}")
def get_campaign(id: int, session: SessionDep):
    campaign = session.get(Campaign, id)  # fetches by primary key directly
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")
    return campaign
```

- `session.get(Model, id)` is the shortcut for fetching by primary key — no `select` needed.

---

### 4. UPDATE — partial update (PATCH)

```python
@app.patch("/campaigns/{id}")
def patch_campaign(id: int, body: CampaignUpdate, session: SessionDep):
    campaign = session.get(Campaign, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")

    update_data = body.model_dump(exclude_unset=True)  # only fields the user sent
    campaign.sqlmodel_update(update_data)              # apply changes
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign
```

- `exclude_unset=True` — skips fields not sent in the request (critical for PATCH, so you don't overwrite existing values with None)

---

### 5. DELETE

```python
@app.delete("/campaigns/{id}")
def delete_campaign(id: int, session: SessionDep):
    campaign = session.get(Campaign, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(campaign)
    session.commit()
    return Response(status_code=204)
```

---

## The Universal Pattern

```
READ   → session.get(Model, id)  or  session.exec(select(Model)).all()
WRITE  → session.add(obj) → session.commit() → session.refresh(obj)
DELETE → session.delete(obj) → session.commit()
```

---

## Quick Reference

| Operation | Code |
|---|---|
| Fetch by primary key | `session.get(Campaign, id)` |
| Fetch all rows | `session.exec(select(Campaign)).all()` |
| Fetch one with filter | `session.exec(select(Campaign).where(Campaign.name == "x")).first()` |
| Insert | `session.add(obj)` → `commit()` → `refresh()` |
| Update | `obj.sqlmodel_update(data)` → `add()` → `commit()` → `refresh()` |
| Delete | `session.delete(obj)` → `commit()` |
| Only sent fields (PATCH) | `body.model_dump(exclude_unset=True)` |
