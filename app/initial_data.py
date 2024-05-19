from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate
from app.utils import get_password_hash

def init_db(engine):
    """
    Initialise la base de données en créant le superutilisateur.
    """
    from app.database import Base
    Base.metadata.create_all(bind=engine)

    db = Session(engine)

    user = db.query(User).filter(User.is_superuser == True).first()
    if not user:
        user_in = UserCreate(
            email=os.getenv("FIRST_SUPERUSER_EMAIL"),
            password=os.getenv("FIRST_SUPERUSER_PASSWORD"),
            is_superuser=True,
        )
        user = User(
            **user_in.dict(exclude={"password"}),
            hashed_password=get_password_hash(user_in.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)