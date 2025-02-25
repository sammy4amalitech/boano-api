from fastcrud import FastCRUD

from ..models.user import User, UserCreateInternal, UserDelete, UserUpdate, UserUpdateInternal, UserRead

CRUDUser = FastCRUD[User, UserCreateInternal, UserUpdate, UserUpdateInternal, UserDelete, UserRead]
crud_users = CRUDUser(User)
