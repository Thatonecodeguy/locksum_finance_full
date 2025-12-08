from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models, schemas
from .auth import authenticate_user, create_access_token, hash_password, get_current_user
from .ai import build_ai_insights, build_debt_plan
from .plans import require_min_plan
from .plaid_integration import router as plaid_router
from .stripe_billing import router as billing_router
from .settings import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Locksum Finance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plaid_router)
app.include_router(billing_router)

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=user_in.email, password_hash=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=schemas.Token)
def login(form: schemas.UserCreate, db: Session = Depends(get_db)):
    user = authenticate_user(db, form.email, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserOut)
def me(user=Depends(get_current_user)):
    return user

# Transactions & budgets
@app.post("/transactions", response_model=schemas.TransactionOut)
def create_txn(txn: schemas.TransactionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = models.Transaction(user_id=user.id, **txn.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/transactions", response_model=list[schemas.TransactionOut])
def list_txns(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Transaction).filter(models.Transaction.user_id == user.id).all()

@app.post("/budgets", response_model=schemas.BudgetOut)
def create_budget(b: schemas.BudgetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = models.Budget(user_id=user.id, **b.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/budgets", response_model=list[schemas.BudgetOut])
def list_budgets(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Budget).filter(models.Budget.user_id == user.id).all()

# AI endpoints
@app.post("/ai/insights")
def ai_insights(
    payload: schemas.AIGoals | None = None,
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_min_plan(user, "plus")
    goals = payload.dict() if payload else None
    return build_ai_insights(db, user.id, days=days, goals=goals)

@app.post("/ai/debt-plan")
def ai_debt_plan(body: schemas.DebtPlanRequest):
    risk = body.risk if body.risk in {"low", "medium", "high"} else "medium"
    return build_debt_plan(body.total_debt, body.monthly_extra, risk=risk)
