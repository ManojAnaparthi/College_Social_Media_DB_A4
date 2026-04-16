-- ============================================================================
-- College Social Media Platform - Database Schema
-- CS 432 - Databases Assignment 1
-- ============================================================================

USE maaps;

-- Drop existing tables if they exist (in reverse order to respect foreign keys)
DROP TABLE IF EXISTS ApiWriteLog;
DROP TABLE IF EXISTS ActivityLog;
DROP TABLE IF EXISTS Notification;
DROP TABLE IF EXISTS Message;
DROP TABLE IF EXISTS GroupMember;
DROP TABLE IF EXISTS `Group`;
DROP TABLE IF EXISTS Report;
DROP TABLE IF EXISTS `Like`;
DROP TABLE IF EXISTS Comment;
DROP TABLE IF EXISTS Post;
DROP TABLE IF EXISTS Follow;
DROP TABLE IF EXISTS AuthCredential;
DROP TABLE IF EXISTS Member;

-- ============================================================================
-- Table 1: Member
-- Core user table with verification and profile information
-- ============================================================================
CREATE TABLE Member (
    MemberID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    ContactNumber VARCHAR(15) NOT NULL,
    Image VARCHAR(255) DEFAULT 'default_avatar.jpg',
    CollegeID VARCHAR(20) NOT NULL UNIQUE,
    Role ENUM('Student', 'Faculty', 'Staff', 'Admin') NOT NULL DEFAULT 'Student',
    Department VARCHAR(50) NOT NULL,
    Age INT,
    IsVerified BOOLEAN NOT NULL DEFAULT FALSE,
    JoinDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastLogin DATETIME,
    Bio TEXT,
    CONSTRAINT chk_email_format CHECK (Email LIKE '%@%.%'),
    CONSTRAINT chk_member_age CHECK (Age IS NULL OR Age BETWEEN 16 AND 100)
);

-- ============================================================================
-- Table 1B: AuthCredential
-- Stores authentication credentials (never store plaintext passwords)
-- One-to-one with Member via MemberID (PK + FK)
-- ============================================================================
CREATE TABLE AuthCredential (
    MemberID INT PRIMARY KEY,
    PasswordHash VARCHAR(255) NOT NULL,
    PasswordAlgo VARCHAR(30) NOT NULL DEFAULT 'bcrypt',
    PasswordUpdatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================================
-- Table 2: Follow
-- Manages follower-following relationships between members
-- ============================================================================
CREATE TABLE Follow (
    FollowID INT PRIMARY KEY AUTO_INCREMENT,
    FollowerID INT NOT NULL,
    FollowingID INT NOT NULL,
    FollowDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (FollowerID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (FollowingID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(FollowerID, FollowingID)
    -- Note: Self-follow prevention enforced by trigger trg_follow_no_self_follow_insert/update
);

-- ============================================================================
-- Table 3: Post
-- Stores user posts and updates
-- ============================================================================
CREATE TABLE Post (
    PostID INT PRIMARY KEY AUTO_INCREMENT,
    MemberID INT NOT NULL,
    Content TEXT NOT NULL,
    MediaURL VARCHAR(255),
    MediaType ENUM('Image', 'Video', 'Document', 'None') NOT NULL DEFAULT 'None',
    PostDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastEditDate DATETIME,
    Visibility ENUM('Public', 'Followers', 'Private') NOT NULL DEFAULT 'Public',
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    LikeCount INT NOT NULL DEFAULT 0 CHECK (LikeCount >= 0),
    CommentCount INT NOT NULL DEFAULT 0 CHECK (CommentCount >= 0),
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_content_not_empty CHECK (CHAR_LENGTH(TRIM(Content)) > 0)
);

-- ============================================================================
-- Table 4: Comment
-- Stores comments on posts
-- ============================================================================
CREATE TABLE Comment (
    CommentID INT PRIMARY KEY AUTO_INCREMENT,
    PostID INT NOT NULL,
    MemberID INT NOT NULL,
    Content TEXT NOT NULL,
    CommentDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastEditDate DATETIME,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    LikeCount INT NOT NULL DEFAULT 0 CHECK (LikeCount >= 0),
    FOREIGN KEY (PostID) REFERENCES Post(PostID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_comment_not_empty CHECK (CHAR_LENGTH(TRIM(Content)) > 0)
);

-- ============================================================================
-- Table 5: Like
-- Stores likes on posts and comments
-- ============================================================================
CREATE TABLE `Like` (
    LikeID INT PRIMARY KEY AUTO_INCREMENT,
    MemberID INT NOT NULL,
    TargetType ENUM('Post', 'Comment') NOT NULL,
    TargetID INT NOT NULL,
    LikeDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(MemberID, TargetType, TargetID)
);

-- ============================================================================
-- Table 6: Report
-- Manages content moderation and user reports
-- ============================================================================
CREATE TABLE Report (
    ReportID INT PRIMARY KEY AUTO_INCREMENT,
    ReporterID INT NOT NULL,
    ReportedItemType ENUM('Post', 'Comment', 'Member') NOT NULL,
    ReportedItemID INT NOT NULL,
    Reason TEXT NOT NULL,
    Status ENUM('Pending', 'Reviewed', 'Resolved', 'Dismissed') NOT NULL DEFAULT 'Pending',
    ReportDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ReviewedBy INT,
    ReviewDate DATETIME,
    Action VARCHAR(255),
    FOREIGN KEY (ReporterID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (ReviewedBy) REFERENCES Member(MemberID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_reason_not_empty CHECK (CHAR_LENGTH(TRIM(Reason)) > 0),
    -- Note: Review logic enforced by trigger trg_report_review_logic_insert/update
    CONSTRAINT chk_report_chronology CHECK (ReviewDate IS NULL OR ReviewDate >= ReportDate)
);

-- ============================================================================
-- Table 7: Group
-- Campus groups and communities
-- ============================================================================
CREATE TABLE `Group` (
    GroupID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Description TEXT NOT NULL,
    CreatorID INT NOT NULL,
    CreateDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    Category ENUM('Academic', 'Sports', 'Cultural', 'Tech', 'Other') NOT NULL DEFAULT 'Other',
    MemberCount INT NOT NULL DEFAULT 0 CHECK (MemberCount >= 0),
    FOREIGN KEY (CreatorID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_name_not_empty CHECK (CHAR_LENGTH(TRIM(Name)) > 0)
);

-- ============================================================================
-- Table 8: GroupMember
-- Manages group membership
-- ============================================================================
CREATE TABLE GroupMember (
    GroupMemberID INT PRIMARY KEY AUTO_INCREMENT,
    GroupID INT NOT NULL,
    MemberID INT NOT NULL,
    Role ENUM('Admin', 'Moderator', 'Member') NOT NULL DEFAULT 'Member',
    JoinDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (GroupID) REFERENCES `Group`(GroupID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(GroupID, MemberID)
);

-- ============================================================================
-- Table 9: Message
-- Direct messages between users
-- ============================================================================
CREATE TABLE Message (
    MessageID INT PRIMARY KEY AUTO_INCREMENT,
    SenderID INT NOT NULL,
    ReceiverID INT NOT NULL,
    Content TEXT NOT NULL,
    SendDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    IsRead BOOLEAN NOT NULL DEFAULT FALSE,
    ReadDate DATETIME,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (SenderID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (ReceiverID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_message_not_empty CHECK (CHAR_LENGTH(TRIM(Content)) > 0),
    -- Note: Self-message prevention enforced by trigger trg_message_no_self_message_insert/update
    CONSTRAINT chk_read_date_logic CHECK (
        (IsRead = FALSE AND ReadDate IS NULL) OR
        (IsRead = TRUE AND ReadDate IS NOT NULL)
    ),
    CONSTRAINT chk_message_chronology CHECK (ReadDate IS NULL OR ReadDate >= SendDate)
);

-- ============================================================================
-- Table 10: Notification
-- User notifications for various activities
-- ============================================================================
CREATE TABLE Notification (
    NotificationID INT PRIMARY KEY AUTO_INCREMENT,
    MemberID INT NOT NULL,
    Type ENUM('Like', 'Comment', 'Follow', 'Mention', 'GroupInvite', 'Report') NOT NULL,
    Content TEXT NOT NULL,
    ReferenceID INT,
    IsRead BOOLEAN NOT NULL DEFAULT FALSE,
    CreateDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ReadDate DATETIME,
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_notification_not_empty CHECK (CHAR_LENGTH(TRIM(Content)) > 0),
    CONSTRAINT chk_notification_read_date_logic CHECK (
        (IsRead = FALSE AND ReadDate IS NULL) OR
        (IsRead = TRUE AND ReadDate IS NOT NULL)
    ),
    CONSTRAINT chk_notification_chronology CHECK (ReadDate IS NULL OR ReadDate >= CreateDate)
);

-- ============================================================================
-- Table 11: ActivityLog
-- Tracks user activities for security and analytics
-- ============================================================================
CREATE TABLE ActivityLog (
    LogID INT PRIMARY KEY AUTO_INCREMENT,
    MemberID INT NOT NULL,
    ActivityType ENUM('Login', 'Logout', 'Post', 'Comment', 'Like', 'Report', 'ProfileUpdate') NOT NULL,
    Details TEXT NOT NULL,
    IPAddress VARCHAR(45),
    `Timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================================
-- Table 12: ApiWriteLog
-- Tracks all DB write operations and distinguishes API-authorized writes from
-- direct database modifications.
-- ============================================================================
CREATE TABLE ApiWriteLog (
    LogID INT PRIMARY KEY AUTO_INCREMENT,
    TableName VARCHAR(50) NOT NULL,
    OperationType ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    RecordID VARCHAR(64),
    ActorMemberID INT,
    SourceType ENUM('API', 'DIRECT_DB') NOT NULL,
    IsAuthorized BOOLEAN NOT NULL,
    ActionName VARCHAR(100),
    Endpoint VARCHAR(255),
    HttpMethod VARCHAR(10),
    ChangeTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Details TEXT
);

-- ============================================================================
-- Indexes for Performance Optimization
-- ============================================================================
-- Baseline FK-support indexes.
CREATE INDEX idx_post_member ON Post(MemberID);
CREATE INDEX idx_comment_post ON Comment(PostID);
CREATE INDEX idx_comment_member ON Comment(MemberID);
-- 2) Comment listing query: WHERE PostID = ? AND IsActive = TRUE ORDER BY CommentDate ASC
CREATE INDEX idx_comment_post_active_date ON Comment(PostID, IsActive, CommentDate ASC);
CREATE INDEX idx_post_active_postdate_postid ON Post(IsActive, PostDate DESC, PostID DESC);

-- Triggers removed for remote shard environment (no SUPER privilege).
-- Core tables and indexes remain intact for sharding tasks.

-- ============================================================================
-- End of Schema
-- ============================================================================
