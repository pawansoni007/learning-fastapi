from datetime import datetime
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel 


class Campaign(BaseModel):
    campaign_id: str
    name: str
    due_date: datetime
    created_at: datetime

class CampaignUpdate(BaseModel): 
    name: Optional[str] = None
    due_date: Optional[datetime] = None

# region Data
data: Any = [
    {
        "campaign_id": "123",
        "name": "Radha naam kirtan",
        "due_date": "23-04-2026",
        "created_at": datetime.now(),
    },
    {
        "campaign_id": "124",
        "name": "Bhagavad Gita Paath",
        "due_date": "10-05-2026",
        "created_at": datetime.now(),
    },
    {
        "campaign_id": "125",
        "name": "Hanuman Chalisa Recitation",
        "due_date": "15-07-2026",
        "created_at": datetime.now(),
    },
    {
        "campaign_id": "126",
        "name": "Shiva Rudrabhishek Yagna",
        "due_date": "01-08-2026",
        "created_at": datetime.now(),
    },
]
# endregion Data

app = FastAPI(root_path="/api/v1")

@app.get("/")
async def root():
    return "Shree Harivansh <3"

@app.get("/campaigns")
async def read_campaigns():
    return {"campaigns": data}

"""
Get campaign by ID
"""
@app.get("/campaigns/{id}")
async def get_campaign_by_id(id: str):
    for d in data:
        if d.get("campaign_id") == id:
            return {"campaign": d}
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.post('/campaigns')
async def create_campaign(body: Campaign): 
    new_data = {
        "campaign_id": body.campaign_id,
        "name": body.name,
        "due_data": body.due_date,
        "created_at": body.created_at
    }

    data.append(new_data)
    return {"campaign": new_data}

@app.patch("/campaigns/{id}")
async def patch_campaign(id: str, body: CampaignUpdate):
    for d in data: 
        if d.get("campaign_id") == id: 
            if body.name is not None: 
                d['name'] = body.name
            if body.due_date is not None: 
                d['due_date'] = body.due_date
            return {"campaign": d}
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.delete('/campaigns/{id}')
async def delete_campaign(id: str): 
    for d in data: 
        if d.get('campaign_id') == id: 
            data.remove(d)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Campaign not found")