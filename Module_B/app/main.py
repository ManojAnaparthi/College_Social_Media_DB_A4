import datetime
import json
import os
from typing import Literal

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from pydantic import BaseModel
from database import DatabaseQueryError, execute_query

app = FastAPI()

SECRET_KEY = "your_secret_key"  # In production, use a secure method to store this
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), "audit.log")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(DatabaseQueryError)
async def database_error_handler(_: Request, __: DatabaseQueryError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable or credentials are incorrect. Update DB settings and try again."
        },
    )

# Pydantic model for login request
class LoginRequest(BaseModel):
    username: str
    password: str


class PortfolioUpdate(BaseModel):
    bio: str | None = None
    contact_number: str | None = None
    department: str | None = None


class PostCreate(BaseModel):
    content: str
    media_url: str | None = None
    media_type: Literal["Image", "Video", "Document", "None"] = "None"
    visibility: Literal["Public", "Followers", "Private"] = "Public"


class PostUpdate(BaseModel):
    content: str | None = None
    media_url: str | None = None
    media_type: Literal["Image", "Video", "Document", "None"] | None = None
    visibility: Literal["Public", "Followers", "Private"] | None = None


class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


class AdminMemberCreate(BaseModel):
    name: str
    email: str
    contact_number: str
    college_id: str
    role: Literal["Student", "Faculty", "Staff", "Admin"] = "Student"
    department: str
    bio: str | None = None
    password: str


class GroupMemberManage(BaseModel):
    member_id: int
    role: Literal["Admin", "Moderator", "Member"] = "Member"


def _append_audit_entry(entry: dict) -> None:
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(entry, default=str) + "\n")


def _audit_log(
    *,
    action: str,
    actor_id: int | None,
    actor_role: str | None,
    endpoint: str,
    method: str,
    table: str,
    target_id: int | None,
    outcome: Literal["success", "denied", "failed"],
    details: str,
) -> None:
    entry = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action,
        "actor_member_id": actor_id,
        "actor_role": actor_role,
        "endpoint": endpoint,
        "method": method,
        "table": table,
        "target_id": target_id,
        "outcome": outcome,
        "details": details,
    }
    _append_audit_entry(entry)


def _require_admin(request: Request, current_user: dict) -> None:
    if current_user.get("role") != "Admin":
        _audit_log(
            action="admin_access_attempt",
            actor_id=current_user.get("member_id"),
            actor_role=current_user.get("role"),
            endpoint=str(request.url.path),
            method=request.method,
            table="N/A",
            target_id=None,
            outcome="denied",
            details="Non-admin attempted admin-only endpoint",
        )
        raise HTTPException(status_code=403, detail="Admin access required")


def _verify_password(plain_password: str, stored_hash: str) -> bool:
    # Supports assignment sample data while still enabling real bcrypt checks.
    if stored_hash.startswith("$2b$12$DUMMY_HASH_"):
        return plain_password == "password123"
    try:
        return pwd_context.verify(plain_password, stored_hash)
    except ValueError:
        return False


def _is_allowed_to_view_profile(viewer_id: int, viewer_role: str, target_member_id: int) -> bool:
    if viewer_role == "Admin" or viewer_id == target_member_id:
        return True

    follows_target = execute_query(
        """
        SELECT 1
        FROM Follow
        WHERE FollowerID = %s AND FollowingID = %s
        """,
        (viewer_id, target_member_id),
        fetchone=True,
    )
    return follows_target is not None


def _get_visible_post(post_id: int, member_id: int):
    return execute_query(
        """
        SELECT
            p.PostID,
            p.MemberID,
            p.IsActive,
            p.Visibility
        FROM Post p
        WHERE p.PostID = %s
          AND p.IsActive = TRUE
          AND (
              p.Visibility = 'Public'
              OR p.MemberID = %s
              OR (
                  p.Visibility = 'Followers'
                  AND EXISTS (
                      SELECT 1
                      FROM Follow f
                      WHERE f.FollowerID = %s AND f.FollowingID = p.MemberID
                  )
              )
          )
        """,
        (post_id, member_id, member_id),
        fetchone=True,
    )
    
# Dependency: Session validation
def verify_session_token(session_token: str = Header(None, alias="session-token")):
    if not session_token:
        raise HTTPException(status_code=401, detail="Missing parameters")
    try:
        payload = jwt.decode(session_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Return the decoded payload for use in endpoints
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token" )
    
@app.get("/", include_in_schema=False)
def ui_home():
    """Serve the local web UI."""
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))


@app.get("/health")
def health_check(_: dict = Depends(verify_session_token)):
    """Simple health endpoint to test the API."""
    return {"message": "College Social Media API is running."}

@app.post("/login")
def login(request: LoginRequest):
    """Authenticates a user and returns a session token."""
    query = """
        SELECT m.MemberID, m.Email, m.Role, m.Name, a.PasswordHash 
        FROM Member m
        JOIN AuthCredential a ON m.MemberID = a.MemberID
        WHERE m.Email = %s
    """
    user_record = execute_query(query, (request.username,), fetchone=True)
    
    if not user_record:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not _verify_password(request.password, user_record["PasswordHash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create JWT token
    expiry_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    token_payload = {
        "member_id": user_record["MemberID"],
        "Email": user_record["Email"],
        "role": user_record["Role"],
        "name": user_record["Name"],
        "exp": int(expiry_time.timestamp()),
    }
    
    token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "message": "Login successful",
        "session_token": token
    }
    
@app.get("/isAuth")
def is_auth(current_user: dict = Depends(verify_session_token)):
    """Endpoint to check if the session token is valid."""
    expiry_dt = datetime.datetime.fromtimestamp(current_user.get("exp"))
    return {
        "message": "Session is valid",
        "member_id": current_user.get("member_id"),
        "email": current_user.get("Email"),
        "role": current_user.get("role"),
        "expires_at": expiry_dt.isoformat()
    }


@app.post("/logout")
def logout(_: dict = Depends(verify_session_token)):
    """Client clears token locally; this endpoint confirms logout intent."""
    return {"message": "Logout successful"}

# --- CRUD Endpoints for Member Portfolio ---

@app.get("/portfolio/{member_id}")
def get_portfolio(member_id: int, current_user: dict = Depends(verify_session_token)):
    """
    Retrieves portfolio details.
    RBAC: Users can only view their own profile unless they are an Admin.
    """
    # 1. Enforce Role-Based Access Control (RBAC)
    viewer_id = current_user.get("member_id")
    viewer_role = current_user.get("role")

    if viewer_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if not _is_allowed_to_view_profile(viewer_id, viewer_role, member_id):
        raise HTTPException(status_code=403, detail="You do not have permission to view this portfolio.")
        
    # 2. Fetch data from MySQL
    query = """
        SELECT Name, Email, ContactNumber, Department, Bio, JoinDate, Role
        FROM Member
        WHERE MemberID = %s
    """
    portfolio = execute_query(query, (member_id,), fetchone=True)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Member not found.")
        
    return {"message": "Portfolio retrieved successfully", "data": portfolio}

@app.put("/portfolio/{member_id}")
def update_portfolio(
    member_id: int,
    update_data: PortfolioUpdate,
    request: Request,
    current_user: dict = Depends(verify_session_token),
):
    """
    Updates portfolio details (Bio, Contact Number, Department).
    RBAC: Users can only modify their own profile unless they are an Admin.
    """
    # 1. Enforce Role-Based Access Control (RBAC)
    is_admin = current_user.get("role") == "Admin"
    is_self = current_user.get("member_id") == member_id
    
    if not (is_admin or is_self):
        _audit_log(
            action="portfolio_update",
            actor_id=current_user.get("member_id"),
            actor_role=current_user.get("role"),
            endpoint=str(request.url.path),
            method=request.method,
            table="Member",
            target_id=member_id,
            outcome="denied",
            details="User attempted to update another member profile",
        )
        raise HTTPException(status_code=403, detail="You do not have permission to modify this portfolio.")
        
    # 2. Build the update query dynamically based on provided fields
    updates = []
    params = []
    if update_data.bio is not None:
        updates.append("Bio = %s")
        params.append(update_data.bio)
    if update_data.contact_number is not None:
        updates.append("ContactNumber = %s")
        params.append(update_data.contact_number)
    if update_data.department is not None:
        updates.append("Department = %s")
        params.append(update_data.department)
        
    if not updates:
        return {"message": "No data provided to update."}
        
    # Append the WHERE clause parameter
    query = f"UPDATE Member SET {', '.join(updates)} WHERE MemberID = %s"
    params.append(member_id)
    
    # 3. Execute the update
    execute_query(query, tuple(params))
    _audit_log(
        action="portfolio_update",
        actor_id=current_user.get("member_id"),
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Member",
        target_id=member_id,
        outcome="success",
        details=f"Updated fields: {', '.join(updates)}",
    )
    
    return {"message": f"Portfolio for member {member_id} updated successfully."}


# --- CRUD Endpoints for Post (project-specific table) ---

@app.post("/posts")
def create_post(post_data: PostCreate, request: Request, current_user: dict = Depends(verify_session_token)):
    """Create a new post for the authenticated member."""
    member_id = current_user.get("member_id")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if not post_data.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    query = """
        INSERT INTO Post (MemberID, Content, MediaURL, MediaType, Visibility)
        VALUES (%s, %s, %s, %s, %s)
    """
    new_post_id = execute_query(
        query,
        (member_id, post_data.content.strip(), post_data.media_url, post_data.media_type, post_data.visibility),
    )
    _audit_log(
        action="post_create",
        actor_id=member_id,
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Post",
        target_id=new_post_id,
        outcome="success",
        details="Post created",
    )
    return {"message": "Post created successfully", "post_id": new_post_id}


@app.get("/posts")
def list_posts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(verify_session_token),
):
    """Read all active posts for the authenticated user session."""
    if current_user.get("member_id") is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    query = """
        SELECT
            p.PostID,
            p.MemberID,
            m.Name AS AuthorName,
            p.Content,
            p.MediaURL,
            p.MediaType,
            p.PostDate,
            p.LastEditDate,
            p.Visibility,
            p.LikeCount,
            p.CommentCount
        FROM Post p
        JOIN Member m ON p.MemberID = m.MemberID
        WHERE p.IsActive = TRUE
        ORDER BY p.PostDate DESC
        LIMIT %s OFFSET %s
    """
    posts = execute_query(query, (limit, offset), fetchall=True)
    return {"message": "Posts retrieved successfully", "count": len(posts), "data": posts}


@app.get("/posts/{post_id}")
def get_post(post_id: int, current_user: dict = Depends(verify_session_token)):
    """Read one post if it is visible to the authenticated member."""
    member_id = current_user.get("member_id")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    visible_post = _get_visible_post(post_id, member_id)
    if not visible_post:
        raise HTTPException(status_code=404, detail="Post not found or not visible")

    query = """
        SELECT
            p.PostID,
            p.MemberID,
            m.Name AS AuthorName,
            p.Content,
            p.MediaURL,
            p.MediaType,
            p.PostDate,
            p.LastEditDate,
            p.Visibility,
            p.LikeCount,
            p.CommentCount,
            p.IsActive
        FROM Post p
        JOIN Member m ON p.MemberID = m.MemberID
        WHERE p.PostID = %s
          AND p.IsActive = TRUE
          AND (
              p.Visibility = 'Public'
              OR p.MemberID = %s
              OR (
                  p.Visibility = 'Followers'
                  AND EXISTS (
                      SELECT 1
                      FROM Follow f
                      WHERE f.FollowerID = %s AND f.FollowingID = p.MemberID
                  )
              )
          )
    """
    post = execute_query(query, (post_id, member_id, member_id), fetchone=True)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not visible")
    return {"message": "Post retrieved successfully", "data": post}


@app.post("/posts/{post_id}/comments")
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    request: Request,
    current_user: dict = Depends(verify_session_token),
):
    """Create a comment on a visible post."""
    member_id = current_user.get("member_id")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if not _get_visible_post(post_id, member_id):
        raise HTTPException(status_code=404, detail="Post not found or not visible")

    if not comment_data.content.strip():
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")

    comment_id = execute_query(
        """
        INSERT INTO Comment (PostID, MemberID, Content)
        VALUES (%s, %s, %s)
        """,
        (post_id, member_id, comment_data.content.strip()),
    )
    _audit_log(
        action="comment_create",
        actor_id=member_id,
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Comment",
        target_id=comment_id,
        outcome="success",
        details=f"Comment created on post {post_id}",
    )
    return {"message": "Comment created successfully", "comment_id": comment_id}


@app.get("/posts/{post_id}/comments")
def list_comments(post_id: int, current_user: dict = Depends(verify_session_token)):
    """Read comments for a visible post."""
    member_id = current_user.get("member_id")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if not _get_visible_post(post_id, member_id):
        raise HTTPException(status_code=404, detail="Post not found or not visible")

    comments = execute_query(
        """
        SELECT
            c.CommentID,
            c.PostID,
            c.MemberID,
            m.Name AS AuthorName,
            c.Content,
            c.CommentDate,
            c.LastEditDate,
            c.LikeCount,
            c.IsActive
        FROM Comment c
        JOIN Member m ON c.MemberID = m.MemberID
        WHERE c.PostID = %s AND c.IsActive = TRUE
        ORDER BY c.CommentDate ASC
        """,
        (post_id,),
        fetchall=True,
    )
    return {"message": "Comments retrieved successfully", "count": len(comments), "data": comments}


@app.put("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    update_data: CommentUpdate,
    request: Request,
    current_user: dict = Depends(verify_session_token),
):
    """Update a comment. Only owner or admin may modify."""
    member_id = current_user.get("member_id")
    role = current_user.get("role")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if not update_data.content.strip():
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")

    comment_owner = execute_query(
        "SELECT CommentID, MemberID, IsActive FROM Comment WHERE CommentID = %s",
        (comment_id,),
        fetchone=True,
    )
    if not comment_owner or not comment_owner["IsActive"]:
        raise HTTPException(status_code=404, detail="Comment not found")

    if role != "Admin" and comment_owner["MemberID"] != member_id:
        _audit_log(
            action="comment_update",
            actor_id=member_id,
            actor_role=role,
            endpoint=str(request.url.path),
            method=request.method,
            table="Comment",
            target_id=comment_id,
            outcome="denied",
            details="User attempted to update comment they do not own",
        )
        raise HTTPException(status_code=403, detail="You do not have permission to modify this comment")

    execute_query(
        """
        UPDATE Comment
        SET Content = %s, LastEditDate = CURRENT_TIMESTAMP
        WHERE CommentID = %s
        """,
        (update_data.content.strip(), comment_id),
    )
    _audit_log(
        action="comment_update",
        actor_id=member_id,
        actor_role=role,
        endpoint=str(request.url.path),
        method=request.method,
        table="Comment",
        target_id=comment_id,
        outcome="success",
        details="Comment updated",
    )
    return {"message": f"Comment {comment_id} updated successfully."}


@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, request: Request, current_user: dict = Depends(verify_session_token)):
    """Delete a comment via soft delete. Only owner or admin may delete."""
    member_id = current_user.get("member_id")
    role = current_user.get("role")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    comment_owner = execute_query(
        "SELECT CommentID, MemberID, IsActive FROM Comment WHERE CommentID = %s",
        (comment_id,),
        fetchone=True,
    )
    if not comment_owner or not comment_owner["IsActive"]:
        raise HTTPException(status_code=404, detail="Comment not found")

    if role != "Admin" and comment_owner["MemberID"] != member_id:
        _audit_log(
            action="comment_delete",
            actor_id=member_id,
            actor_role=role,
            endpoint=str(request.url.path),
            method=request.method,
            table="Comment",
            target_id=comment_id,
            outcome="denied",
            details="User attempted to delete comment they do not own",
        )
        raise HTTPException(status_code=403, detail="You do not have permission to delete this comment")

    execute_query("UPDATE Comment SET IsActive = FALSE WHERE CommentID = %s", (comment_id,))
    _audit_log(
        action="comment_delete",
        actor_id=member_id,
        actor_role=role,
        endpoint=str(request.url.path),
        method=request.method,
        table="Comment",
        target_id=comment_id,
        outcome="success",
        details="Comment soft-deleted",
    )
    return {"message": f"Comment {comment_id} deleted successfully."}


@app.put("/posts/{post_id}")
def update_post(post_id: int, update_data: PostUpdate, request: Request, current_user: dict = Depends(verify_session_token)):
    """Update post content/metadata. Only owner or admin may modify."""
    member_id = current_user.get("member_id")
    role = current_user.get("role")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    post_owner = execute_query(
        "SELECT PostID, MemberID, IsActive FROM Post WHERE PostID = %s",
        (post_id,),
        fetchone=True,
    )
    if not post_owner or not post_owner["IsActive"]:
        raise HTTPException(status_code=404, detail="Post not found")

    if role != "Admin" and post_owner["MemberID"] != member_id:
        _audit_log(
            action="post_update",
            actor_id=member_id,
            actor_role=role,
            endpoint=str(request.url.path),
            method=request.method,
            table="Post",
            target_id=post_id,
            outcome="denied",
            details="User attempted to update post they do not own",
        )
        raise HTTPException(status_code=403, detail="You do not have permission to modify this post")

    updates = []
    params = []

    if update_data.content is not None:
        if not update_data.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        updates.append("Content = %s")
        params.append(update_data.content.strip())
    if update_data.media_url is not None:
        updates.append("MediaURL = %s")
        params.append(update_data.media_url)
    if update_data.media_type is not None:
        updates.append("MediaType = %s")
        params.append(update_data.media_type)
    if update_data.visibility is not None:
        updates.append("Visibility = %s")
        params.append(update_data.visibility)

    if not updates:
        return {"message": "No data provided to update."}

    updates.append("LastEditDate = CURRENT_TIMESTAMP")
    query = f"UPDATE Post SET {', '.join(updates)} WHERE PostID = %s"
    params.append(post_id)
    execute_query(query, tuple(params))
    _audit_log(
        action="post_update",
        actor_id=member_id,
        actor_role=role,
        endpoint=str(request.url.path),
        method=request.method,
        table="Post",
        target_id=post_id,
        outcome="success",
        details=f"Updated fields: {', '.join(updates)}",
    )
    return {"message": f"Post {post_id} updated successfully."}


@app.delete("/posts/{post_id}")
def delete_post(post_id: int, request: Request, current_user: dict = Depends(verify_session_token)):
    """Delete a post via soft delete. Only owner or admin may delete."""
    member_id = current_user.get("member_id")
    role = current_user.get("role")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    post_owner = execute_query(
        "SELECT PostID, MemberID, IsActive FROM Post WHERE PostID = %s",
        (post_id,),
        fetchone=True,
    )
    if not post_owner or not post_owner["IsActive"]:
        raise HTTPException(status_code=404, detail="Post not found")

    if role != "Admin" and post_owner["MemberID"] != member_id:
        _audit_log(
            action="post_delete",
            actor_id=member_id,
            actor_role=role,
            endpoint=str(request.url.path),
            method=request.method,
            table="Post",
            target_id=post_id,
            outcome="denied",
            details="User attempted to delete post they do not own",
        )
        raise HTTPException(status_code=403, detail="You do not have permission to delete this post")

    execute_query("UPDATE Post SET IsActive = FALSE WHERE PostID = %s", (post_id,))
    _audit_log(
        action="post_delete",
        actor_id=member_id,
        actor_role=role,
        endpoint=str(request.url.path),
        method=request.method,
        table="Post",
        target_id=post_id,
        outcome="success",
        details="Post soft-deleted",
    )
    return {"message": f"Post {post_id} deleted successfully."}


@app.get("/admin/members")
def list_members_admin(request: Request, current_user: dict = Depends(verify_session_token)):
    """Admin-only list of members for administrative actions."""
    _require_admin(request, current_user)
    members = execute_query(
        """
        SELECT MemberID, Name, Email, Role, Department, IsVerified, JoinDate
        FROM Member
        ORDER BY MemberID ASC
        """,
        fetchall=True,
    )
    return {"message": "Members retrieved successfully", "count": len(members), "data": members}


@app.post("/admin/members")
def create_member_admin(payload: AdminMemberCreate, request: Request, current_user: dict = Depends(verify_session_token)):
    """Admin-only member creation across core tables Member and AuthCredential."""
    _require_admin(request, current_user)

    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    member_id = execute_query(
        """
        INSERT INTO Member (Name, Email, ContactNumber, CollegeID, Role, Department, Bio)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            payload.name.strip(),
            payload.email.strip(),
            payload.contact_number.strip(),
            payload.college_id.strip(),
            payload.role,
            payload.department.strip(),
            payload.bio,
        ),
    )
    password_hash = pwd_context.hash(payload.password)
    execute_query(
        """
        INSERT INTO AuthCredential (MemberID, PasswordHash, PasswordAlgo)
        VALUES (%s, %s, 'bcrypt')
        """,
        (member_id, password_hash),
    )
    _audit_log(
        action="admin_member_create",
        actor_id=current_user.get("member_id"),
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Member,AuthCredential",
        target_id=member_id,
        outcome="success",
        details=f"Admin created member with role {payload.role}",
    )
    return {"message": "Member created successfully", "member_id": member_id}


@app.delete("/admin/members/{member_id}")
def delete_member_admin(member_id: int, request: Request, current_user: dict = Depends(verify_session_token)):
    """Admin-only member deletion (cascades according to schema constraints)."""
    _require_admin(request, current_user)

    member = execute_query("SELECT MemberID FROM Member WHERE MemberID = %s", (member_id,), fetchone=True)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    execute_query("DELETE FROM Member WHERE MemberID = %s", (member_id,))
    _audit_log(
        action="admin_member_delete",
        actor_id=current_user.get("member_id"),
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Member",
        target_id=member_id,
        outcome="success",
        details="Admin deleted member",
    )
    return {"message": f"Member {member_id} deleted successfully"}


@app.post("/admin/groups/{group_id}/members")
def add_group_member_admin(
    group_id: int,
    payload: GroupMemberManage,
    request: Request,
    current_user: dict = Depends(verify_session_token),
):
    """Admin-only: add/reactivate a member in a group and set group role."""
    _require_admin(request, current_user)

    group_exists = execute_query("SELECT GroupID FROM `Group` WHERE GroupID = %s", (group_id,), fetchone=True)
    if not group_exists:
        raise HTTPException(status_code=404, detail="Group not found")

    member_exists = execute_query("SELECT MemberID FROM Member WHERE MemberID = %s", (payload.member_id,), fetchone=True)
    if not member_exists:
        raise HTTPException(status_code=404, detail="Member not found")

    current_entry = execute_query(
        "SELECT GroupMemberID, IsActive FROM GroupMember WHERE GroupID = %s AND MemberID = %s",
        (group_id, payload.member_id),
        fetchone=True,
    )

    if current_entry and current_entry["IsActive"]:
        raise HTTPException(status_code=400, detail="Member already active in this group")

    if current_entry:
        execute_query(
            """
            UPDATE GroupMember
            SET Role = %s, IsActive = TRUE
            WHERE GroupID = %s AND MemberID = %s
            """,
            (payload.role, group_id, payload.member_id),
        )
    else:
        execute_query(
            """
            INSERT INTO GroupMember (GroupID, MemberID, Role, IsActive)
            VALUES (%s, %s, %s, TRUE)
            """,
            (group_id, payload.member_id, payload.role),
        )

    _audit_log(
        action="admin_group_member_add",
        actor_id=current_user.get("member_id"),
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="GroupMember",
        target_id=payload.member_id,
        outcome="success",
        details=f"Added member {payload.member_id} to group {group_id} with role {payload.role}",
    )
    return {"message": "Group member updated successfully"}


@app.delete("/admin/groups/{group_id}/members/{member_id}")
def remove_group_member_admin(
    group_id: int,
    member_id: int,
    request: Request,
    current_user: dict = Depends(verify_session_token),
):
    """Admin-only: remove (soft deactivate) a member from group."""
    _require_admin(request, current_user)

    entry = execute_query(
        "SELECT GroupMemberID, IsActive FROM GroupMember WHERE GroupID = %s AND MemberID = %s",
        (group_id, member_id),
        fetchone=True,
    )
    if not entry or not entry["IsActive"]:
        raise HTTPException(status_code=404, detail="Active group membership not found")

    execute_query(
        "UPDATE GroupMember SET IsActive = FALSE WHERE GroupID = %s AND MemberID = %s",
        (group_id, member_id),
    )
    _audit_log(
        action="admin_group_member_remove",
        actor_id=current_user.get("member_id"),
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="GroupMember",
        target_id=member_id,
        outcome="success",
        details=f"Removed member {member_id} from group {group_id}",
    )
    return {"message": "Group member removed successfully"}


@app.get("/admin/audit-log")
def get_audit_log(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(verify_session_token),
):
    """Admin-only: fetch latest audit entries to review authorized API writes."""
    _require_admin(request, current_user)

    if not os.path.exists(AUDIT_LOG_PATH):
        return {
            "message": "Audit log not found yet; no data-modifying API operations logged",
            "count": 0,
            "data": [],
        }

    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as audit_file:
        lines = audit_file.readlines()

    data = []
    for line in lines[-limit:]:
        try:
            data.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return {
        "message": "Audit entries retrieved successfully",
        "count": len(data),
        "data": data,
        "note": "Any DB change with no matching API audit record should be treated as unauthorized direct modification.",
    }