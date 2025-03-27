from typing import List, Optional
import sqlalchemy.orm
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from task_manager import models, schemas, auth
from task_manager.database import engine, get_db

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome, write /docs!"}


models.Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user_data: schemas.UserCreate, db: sqlalchemy.orm.Session = Depends(get_db)):
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(username=user_data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlalchemy.orm.Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(task_data: schemas.TaskCreate, db: sqlalchemy.orm.Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    new_task = models.Task(**task_data.model_dump(), owner_id=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/tasks/", response_model=List[schemas.TaskResponse])
def read_tasks(skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, search: Optional[str] = None,
               top_priority: Optional[int] = None, db: sqlalchemy.orm.Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.Task).filter(models.Task.owner_id == current_user.id)

    if search:
        query = query.filter((models.Task.title.contains(search)) | (models.Task.description.contains(search)))

    if top_priority:
        query = query.order_by(models.Task.priority.desc()).limit(top_priority)

    if sort_by:
        if sort_by == "title":
            query = query.order_by(models.Task.title)
        elif sort_by == "status":
            query = query.order_by(models.Task.status)
        elif sort_by == "created_at":
            query = query.order_by(models.Task.created_at)

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_data: schemas.TaskUpdate, db: sqlalchemy.orm.Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: sqlalchemy.orm.Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}
