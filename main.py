from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated, Generic, TypeVar
from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, create_engine, select
from models.models import Campaign, CampaignCreate, CampaignUpdate

sqllite_filename = "database.db"
sql_url = f"sqlite:///{sqllite_filename}"

connnect_args = {"check_same_thread": False}

engine = create_engine(sql_url, connect_args=connnect_args)

def create_db_and_tables(): 
    SQLModel.metadata.create_all(engine) # bind = engine -> it means "what are you binding/connecting to?"

def get_session():
    with Session(engine) as session: 
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  
    with Session(engine) as session: 
        if not session.exec(select(Campaign)).first(): # Query the Campaign table.
            from datetime import datetime, timezone

            session.add_all([
                Campaign(
                    name="Bhagavad Gita Parayan", 
                    due_date=datetime.now(timezone.utc) + timedelta(days=2), 
                    created_at=datetime.now(timezone.utc)
                ),
                Campaign(
                    name="Ram Navami Seva", 
                    due_date=datetime.now(timezone.utc) + timedelta(days=2),
               
                    created_at=datetime.now(timezone.utc)
                )
            ])
            session.commit()
    yield 


app = FastAPI(root_path="/api/v1", lifespan=lifespan)

# Response body 
T = TypeVar('T')
class ResponseType(BaseModel, Generic[T]): 
    data: T

    
@app.get("/")
async def root():
    return "Shree Harivansh <3 :)"

@app.get('/campaigns', response_model=ResponseType[list[Campaign]])
async def get_campaigns(session: SessionDep): 
    data = session.exec(select(Campaign)).all()
    return {"data": data}

@app.get('/campaigns/{id}', response_model=ResponseType[Campaign])
async def get_campaign_by_id(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    return {"data": data}

@app.post('/campaign', response_model=ResponseType[Campaign])
async def create_campaign(body: CampaignCreate, session: SessionDep):
    campaign = Campaign.model_validate(body)
    session.add(campaign)
    session.commit()
    session.refresh(campaign) # pull back saved record(gets the auto id)

    return {"data": campaign}

@app.patch('/campaign/{id}', response_model=ResponseType[CampaignUpdate])
async def update_campaign(id: int, body: CampaignUpdate ,session: SessionDep):
    campaign = session.get(Campaign, id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = body.model_dump(exclude_unset=True) # Only update fields user sent.
    campaign.sqlmodel_update(update_data) # apply changes
    session.add(campaign)
    session.commit()
    session.refresh(campaign) # get updated data from db
    return {"data": campaign}

@app.delete('/campaign/{id}', status_code=204)
async def delete_campaign(id: int, session: SessionDep):
    campaign = session.get(Campaign, id)
    if not campaign: 
        raise HTTPException(status_code=404, detail="Not found")
    return Response(status_code=204)
