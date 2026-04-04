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
from pydantic import BaseModel, Field
from database import DatabaseQueryError, execute_query, execute_transaction

app = FastAPI()

# Require JWT secret from environment; fail fast if missing.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is required. Set it in your environment before starting the API.")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
MODULE_B_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(MODULE_B_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
AUDIT_LOG_PATH = os.path.join(LOG_DIR, "audit.log")
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


class SignupRequest(BaseModel):
    name: str
    email: str
    contact_number: str
    college_id: str
    department: str
    age: int | None = Field(default=None, ge=16, le=100)
    bio: str | None = None
    password: str


class PortfolioUpdate(BaseModel):
    bio: str | None = None
    contact_number: str | None = None
    department: str | None = None
    age: int | None = Field(default=None, ge=16, le=100)


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
    age: int | None = Field(default=None, ge=16, le=100)
    bio: str | None = None
    password: str


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


def _db_audit_context(*, action: str, current_user: dict, request: Request) -> dict:
    return {
        "actor_id": current_user.get("member_id"),
        "action": action,
        "endpoint": str(request.url.path),
        "method": request.method,
    }


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
    # Strict hash-only verification.
    try:
        return pwd_context.verify(plain_password, stored_hash)
    except ValueError:
        return False


def _is_following(follower_id: int, following_id: int) -> bool:
    row = execute_query(
        """
        SELECT 1
        FROM Follow
        WHERE FollowerID = %s AND FollowingID = %s
        """,
        (follower_id, following_id),
        fetchone=True,
    )
    return row is not None


def _get_follow_counts(member_id: int) -> tuple[int, int]:
    followers = execute_query(
        "SELECT COUNT(*) AS c FROM Follow WHERE FollowingID = %s",
        (member_id,),
        fetchone=True,
    )
    following = execute_query(
        "SELECT COUNT(*) AS c FROM Follow WHERE FollowerID = %s",
        (member_id,),
        fetchone=True,
    )
    return int(followers["c"]), int(following["c"])


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
    user_record = execute_query(query, (request.username.strip(),), fetchone=True)
    
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


@app.post("/signup")
def signup(request: SignupRequest):
    """Public signup for demo purposes; new members are always created as Student."""
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    email = request.email.strip()
    college_id = request.college_id.strip()
    existing = execute_query(
        "SELECT MemberID FROM Member WHERE Email = %s OR CollegeID = %s",
        (email, college_id),
        fetchone=True,
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email or CollegeID already exists")

    password_hash = pwd_context.hash(request.password)

    def _signup_tx(cursor):
        cursor.execute(
            """
            INSERT INTO Member (Name, Email, ContactNumber, CollegeID, Role, Department, Age, Bio)
            VALUES (%s, %s, %s, %s, 'Student', %s, %s, %s)
            """,
            (
                request.name.strip(),
                email,
                request.contact_number.strip(),
                college_id,
                request.department.strip(),
                request.age,
                request.bio,
            ),
        )
        new_member_id = int(cursor.lastrowid)
        cursor.execute(
            """
            INSERT INTO AuthCredential (MemberID, PasswordHash, PasswordAlgo)
            VALUES (%s, %s, 'bcrypt')
            """,
            (new_member_id, password_hash),
        )
        return new_member_id

    try:
        member_id = execute_transaction(
            _signup_tx,
            audit_context={
                "actor_id": None,
                "action": "public_signup",
                "endpoint": "/signup",
                "method": "POST",
            },
        )
    except DatabaseQueryError as exc:
        if exc.error_code == 1062:
            raise HTTPException(status_code=400, detail="Email or CollegeID already exists")
        raise

    _audit_log(
        action="public_signup",
        actor_id=None,
        actor_role="Public",
        endpoint="/signup",
        method="POST",
        table="Member,AuthCredential",
        target_id=member_id,
        outcome="success",
        details="Public signup created Student account",
    )
    return {"message": "Signup successful. Please login.", "member_id": member_id}
    
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
    Any authenticated user can view portfolios (read-only).
    """
    viewer_id = current_user.get("member_id")
    if viewer_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    query = """
        SELECT MemberID, Name, Email, ContactNumber, Department, Age, Bio, JoinDate, Role
        FROM Member
        WHERE MemberID = %s
    """
    portfolio = execute_query(query, (member_id,), fetchone=True)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Member not found.")

    follower_count, following_count = _get_follow_counts(member_id)
    is_self = viewer_id == member_id
    viewer_is_following = False if is_self else _is_following(viewer_id, member_id)

    portfolio["FollowerCount"] = follower_count
    portfolio["FollowingCount"] = following_count
    portfolio["ViewerIsFollowing"] = viewer_is_following
    portfolio["ViewerCanFollow"] = not is_self
        
    return {"message": "Portfolio retrieved successfully", "data": portfolio}


@app.get("/members/search")
def search_members(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(verify_session_token),
):
    """Search members by name or email for authenticated users."""
    if current_user.get("member_id") is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    term = f"%{q.strip()}%"
    rows = execute_query(
        """
        SELECT MemberID, Name, Email, Department, Role, Bio
        FROM Member
        WHERE Name LIKE %s OR Email LIKE %s
        ORDER BY Name ASC, MemberID ASC
        LIMIT %s
        """,
        (term, term, limit),
        fetchall=True,
    )
    return {
        "message": "Members retrieved successfully",
        "query": q,
        "count": len(rows),
        "data": rows,
    }


@app.get("/members/{member_id}/followers")
def list_followers(
    member_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(verify_session_token),
):
    """List followers of a member for authenticated users."""
    if current_user.get("member_id") is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    member_exists = execute_query("SELECT MemberID FROM Member WHERE MemberID = %s", (member_id,), fetchone=True)
    if not member_exists:
        raise HTTPException(status_code=404, detail="Member not found")

    rows = execute_query(
        """
        SELECT f.FollowID, f.FollowDate, m.MemberID, m.Name, m.Email, m.Department, m.Role
        FROM Follow f
        JOIN Member m ON m.MemberID = f.FollowerID
        WHERE f.FollowingID = %s
        ORDER BY f.FollowDate DESC
        LIMIT %s
        """,
        (member_id, limit),
        fetchall=True,
    )
    return {"message": "Followers retrieved successfully", "count": len(rows), "data": rows}


@app.get("/members/{member_id}/following")
def list_following(
    member_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(verify_session_token),
):
    """List members followed by the given member for authenticated users."""
    if current_user.get("member_id") is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    member_exists = execute_query("SELECT MemberID FROM Member WHERE MemberID = %s", (member_id,), fetchone=True)
    if not member_exists:
        raise HTTPException(status_code=404, detail="Member not found")

    rows = execute_query(
        """
        SELECT f.FollowID, f.FollowDate, m.MemberID, m.Name, m.Email, m.Department, m.Role
        FROM Follow f
        JOIN Member m ON m.MemberID = f.FollowingID
        WHERE f.FollowerID = %s
        ORDER BY f.FollowDate DESC
        LIMIT %s
        """,
        (member_id, limit),
        fetchall=True,
    )
    return {"message": "Following list retrieved successfully", "count": len(rows), "data": rows}


@app.post("/members/{member_id}/follow")
def follow_member(member_id: int, request: Request, current_user: dict = Depends(verify_session_token)):
    """Follow a member. Authenticated users can follow anyone except themselves."""
    follower_id = current_user.get("member_id")
    if follower_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if follower_id == member_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    target = execute_query("SELECT MemberID FROM Member WHERE MemberID = %s", (member_id,), fetchone=True)
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    audit_context = _db_audit_context(action="follow_create", current_user=current_user, request=request)

    def _follow_tx(cursor):
        cursor.execute(
            "INSERT IGNORE INTO Follow (FollowerID, FollowingID) VALUES (%s, %s)",
            (follower_id, member_id),
        )
        created = cursor.rowcount > 0
        cursor.execute(
            "SELECT FollowID FROM Follow WHERE FollowerID = %s AND FollowingID = %s",
            (follower_id, member_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to resolve follow relationship after write")
        return int(row["FollowID"]), created

    follow_id, created = execute_transaction(_follow_tx, audit_context=audit_context)

    _audit_log(
        action="follow_create" if created else "follow_create_noop",
        actor_id=follower_id,
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Follow",
        target_id=follow_id,
        outcome="success",
        details=(
            f"Member {follower_id} followed member {member_id}"
            if created
            else f"Member {follower_id} already followed member {member_id}"
        ),
    )
    return {
        "message": "Followed member successfully" if created else "Already following this member",
        "follow_id": follow_id,
        "created": created,
    }


@app.delete("/members/{member_id}/follow")
def unfollow_member(member_id: int, request: Request, current_user: dict = Depends(verify_session_token)):
    """Unfollow a member. Authenticated users can only remove their own follow edge."""
    follower_id = current_user.get("member_id")
    if follower_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    follow_row = execute_query(
        "SELECT FollowID FROM Follow WHERE FollowerID = %s AND FollowingID = %s",
        (follower_id, member_id),
        fetchone=True,
    )
    if not follow_row:
        raise HTTPException(status_code=404, detail="Follow relationship not found")

    execute_query(
        "DELETE FROM Follow WHERE FollowID = %s",
        (follow_row["FollowID"],),
        audit_context=_db_audit_context(action="follow_delete", current_user=current_user, request=request),
    )
    _audit_log(
        action="follow_delete",
        actor_id=follower_id,
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Follow",
        target_id=follow_row["FollowID"],
        outcome="success",
        details=f"Member {follower_id} unfollowed member {member_id}",
    )
    return {"message": "Unfollowed member successfully"}

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
    if update_data.age is not None:
        updates.append("Age = %s")
        params.append(update_data.age)
        
    if not updates:
        return {"message": "No data provided to update."}
        
    # Append the WHERE clause parameter
    query = f"UPDATE Member SET {', '.join(updates)} WHERE MemberID = %s"
    params.append(member_id)
    
    # 3. Execute the update
    execute_query(
        query,
        tuple(params),
        audit_context=_db_audit_context(action="portfolio_update", current_user=current_user, request=request),
    )
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
        audit_context=_db_audit_context(action="post_create", current_user=current_user, request=request),
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
    member_id = current_user.get("member_id")
    if member_id is None:
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
            p.CommentCount,
            EXISTS (
                SELECT 1
                FROM `Like` l
                WHERE l.MemberID = %s
                  AND l.TargetType = 'Post'
                  AND l.TargetID = p.PostID
            ) AS ViewerHasLiked
        FROM Post p
        JOIN Member m ON p.MemberID = m.MemberID
        WHERE p.IsActive = TRUE
          AND (
              p.Visibility = 'Public'
              OR p.MemberID = %s
              OR (
                  p.Visibility = 'Followers'
                  AND EXISTS (
                      SELECT 1
                      FROM Follow f
                      WHERE f.FollowerID = %s
                        AND f.FollowingID = p.MemberID
                  )
              )
          )
        ORDER BY p.PostDate DESC, p.PostID DESC
        LIMIT %s OFFSET %s
    """
    posts = execute_query(query, (member_id, member_id, member_id, limit, offset), fetchall=True)
    return {"message": "Posts retrieved successfully", "count": len(posts), "data": posts}


@app.get("/members/{member_id}/posts")
def list_member_posts(
    member_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(verify_session_token),
):
    """List posts authored by a member, filtered by viewer visibility rules."""
    viewer_id = current_user.get("member_id")
    viewer_role = current_user.get("role")
    if viewer_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    member_exists = execute_query(
        "SELECT MemberID FROM Member WHERE MemberID = %s",
        (member_id,),
        fetchone=True,
    )
    if not member_exists:
        raise HTTPException(status_code=404, detail="Member not found")

    if viewer_role == "Admin" or viewer_id == member_id:
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
                EXISTS (
                    SELECT 1
                    FROM `Like` l
                    WHERE l.MemberID = %s
                      AND l.TargetType = 'Post'
                      AND l.TargetID = p.PostID
                ) AS ViewerHasLiked
            FROM Post p
            JOIN Member m ON p.MemberID = m.MemberID
            WHERE p.MemberID = %s
              AND p.IsActive = TRUE
            ORDER BY p.PostDate DESC, p.PostID DESC
            LIMIT %s OFFSET %s
        """
        posts = execute_query(query, (viewer_id, member_id, limit, offset), fetchall=True)
    else:
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
                EXISTS (
                    SELECT 1
                    FROM `Like` l
                    WHERE l.MemberID = %s
                      AND l.TargetType = 'Post'
                      AND l.TargetID = p.PostID
                ) AS ViewerHasLiked
            FROM Post p
            JOIN Member m ON p.MemberID = m.MemberID
            WHERE p.MemberID = %s
              AND p.IsActive = TRUE
              AND (
                    p.Visibility = 'Public'
                    OR (
                        p.Visibility = 'Followers'
                        AND EXISTS (
                            SELECT 1
                            FROM Follow f
                            WHERE f.FollowerID = %s
                              AND f.FollowingID = p.MemberID
                        )
                    )
                  )
            ORDER BY p.PostDate DESC, p.PostID DESC
            LIMIT %s OFFSET %s
        """
        posts = execute_query(query, (viewer_id, member_id, viewer_id, limit, offset), fetchall=True)

    return {
        "message": "Member posts retrieved successfully",
        "count": len(posts),
        "data": posts,
    }


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
                        p.IsActive,
                        EXISTS (
                                SELECT 1
                                FROM `Like` l
                                WHERE l.MemberID = %s
                                    AND l.TargetType = 'Post'
                                    AND l.TargetID = p.PostID
                        ) AS ViewerHasLiked
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
    post = execute_query(query, (member_id, post_id, member_id, member_id), fetchone=True)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not visible")
    return {"message": "Post retrieved successfully", "data": post}


@app.post("/posts/{post_id}/like/toggle")
def toggle_post_like(post_id: int, request: Request, current_user: dict = Depends(verify_session_token)):
    """Toggle like/unlike for a visible post using the Like table."""
    member_id = current_user.get("member_id")
    if member_id is None:
        raise HTTPException(status_code=401, detail="Invalid session payload")

    if not _get_visible_post(post_id, member_id):
        raise HTTPException(status_code=404, detail="Post not found or not visible")

    audit_context = _db_audit_context(action="post_like_toggle", current_user=current_user, request=request)

    def _toggle_like_tx(cursor):
        cursor.execute(
            "SELECT PostID FROM Post WHERE PostID = %s AND IsActive = TRUE FOR UPDATE",
            (post_id,),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Post not found")

        cursor.execute(
            """
            SELECT LikeID
            FROM `Like`
            WHERE MemberID = %s AND TargetType = 'Post' AND TargetID = %s
            FOR UPDATE
            """,
            (member_id, post_id),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute("DELETE FROM `Like` WHERE LikeID = %s", (existing["LikeID"],))
            cursor.execute(
                "UPDATE Post SET LikeCount = GREATEST(LikeCount - 1, 0) WHERE PostID = %s",
                (post_id,),
            )
            liked_state = False
            action = "post_unlike"
        else:
            cursor.execute(
                "INSERT INTO `Like` (MemberID, TargetType, TargetID) VALUES (%s, 'Post', %s)",
                (member_id, post_id),
            )
            cursor.execute("UPDATE Post SET LikeCount = LikeCount + 1 WHERE PostID = %s", (post_id,))
            liked_state = True
            action = "post_like"

        cursor.execute("SELECT LikeCount FROM Post WHERE PostID = %s", (post_id,))
        post_row = cursor.fetchone()
        like_total = int(post_row["LikeCount"]) if post_row else 0
        return liked_state, action, like_total

    liked, action_name, like_count = execute_transaction(_toggle_like_tx, audit_context=audit_context)

    _audit_log(
        action=action_name,
        actor_id=member_id,
        actor_role=current_user.get("role"),
        endpoint=str(request.url.path),
        method=request.method,
        table="Like,Post",
        target_id=post_id,
        outcome="success",
        details=f"Member {member_id} {'liked' if liked else 'unliked'} post {post_id}",
    )
    return {
        "message": "Post liked" if liked else "Post unliked",
        "liked": liked,
        "like_count": like_count,
    }


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

    audit_context = _db_audit_context(action="comment_create", current_user=current_user, request=request)

    def _create_comment_tx(cursor):
        cursor.execute(
            "SELECT PostID FROM Post WHERE PostID = %s AND IsActive = TRUE FOR UPDATE",
            (post_id,),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Post not found")

        cursor.execute(
            """
            INSERT INTO Comment (PostID, MemberID, Content)
            VALUES (%s, %s, %s)
            """,
            (post_id, member_id, comment_data.content.strip()),
        )
        new_comment_id = int(cursor.lastrowid)
        cursor.execute(
            "UPDATE Post SET CommentCount = CommentCount + 1 WHERE PostID = %s",
            (post_id,),
        )
        return new_comment_id

    comment_id = execute_transaction(_create_comment_tx, audit_context=audit_context)

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
        audit_context=_db_audit_context(action="comment_update", current_user=current_user, request=request),
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
        "SELECT CommentID, PostID, MemberID, IsActive FROM Comment WHERE CommentID = %s",
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

    audit_context = _db_audit_context(action="comment_delete", current_user=current_user, request=request)

    def _delete_comment_tx(cursor):
        cursor.execute(
            "UPDATE Comment SET IsActive = FALSE WHERE CommentID = %s AND IsActive = TRUE",
            (comment_id,),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Comment not found")
        cursor.execute(
            "UPDATE Post SET CommentCount = GREATEST(CommentCount - 1, 0) WHERE PostID = %s",
            (comment_owner["PostID"],),
        )

    execute_transaction(_delete_comment_tx, audit_context=audit_context)

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
    """Update post content/metadata. Only owner may modify."""
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

    if post_owner["MemberID"] != member_id:
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
    execute_query(
        query,
        tuple(params),
        audit_context=_db_audit_context(action="post_update", current_user=current_user, request=request),
    )
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

    execute_query(
        "UPDATE Post SET IsActive = FALSE WHERE PostID = %s",
        (post_id,),
        audit_context=_db_audit_context(action="post_delete", current_user=current_user, request=request),
    )
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

    password_hash = pwd_context.hash(payload.password)
    audit_context = _db_audit_context(action="admin_member_create", current_user=current_user, request=request)

    def _create_member_tx(cursor):
        cursor.execute(
            """
            INSERT INTO Member (Name, Email, ContactNumber, CollegeID, Role, Department, Age, Bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload.name.strip(),
                payload.email.strip(),
                payload.contact_number.strip(),
                payload.college_id.strip(),
                payload.role,
                payload.department.strip(),
                payload.age,
                payload.bio,
            ),
        )
        new_member_id = int(cursor.lastrowid)
        cursor.execute(
            """
            INSERT INTO AuthCredential (MemberID, PasswordHash, PasswordAlgo)
            VALUES (%s, %s, 'bcrypt')
            """,
            (new_member_id, password_hash),
        )
        return new_member_id

    try:
        member_id = execute_transaction(_create_member_tx, audit_context=audit_context)
    except DatabaseQueryError as exc:
        if exc.error_code == 1062:
            raise HTTPException(status_code=400, detail="Email or CollegeID already exists")
        raise

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

    execute_query(
        "DELETE FROM Member WHERE MemberID = %s",
        (member_id,),
        audit_context=_db_audit_context(action="admin_member_delete", current_user=current_user, request=request),
    )
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
        "log_path": AUDIT_LOG_PATH,
        "note": "Any DB change with no matching API audit record should be treated as unauthorized direct modification.",
    }


@app.get("/admin/db-change-log")
def get_db_change_log(
    request: Request,
    unauthorized_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(verify_session_token),
):
    """Admin-only: read DB-level write trace to identify direct unauthorized modifications."""
    _require_admin(request, current_user)

    where_clause = "WHERE IsAuthorized = FALSE" if unauthorized_only else ""
    rows = execute_query(
        f"""
        SELECT LogID, TableName, OperationType, RecordID, ActorMemberID, SourceType,
               IsAuthorized, ActionName, Endpoint, HttpMethod, ChangeTime, Details
        FROM ApiWriteLog
        {where_clause}
        ORDER BY ChangeTime DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )

    return {
        "message": "DB change log retrieved successfully",
        "count": len(rows),
        "unauthorized_only": unauthorized_only,
        "data": rows,
    }