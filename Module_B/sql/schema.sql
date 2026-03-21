-- ============================================================================
-- College Social Media Platform - Database Schema
-- CS 432 - Databases Assignment 1
-- ============================================================================

CREATE DATABASE IF NOT EXISTS college_social_media;
USE college_social_media;

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
CREATE INDEX idx_member_role ON Member(Role);
CREATE INDEX idx_post_member ON Post(MemberID);
CREATE INDEX idx_post_date ON Post(PostDate DESC);
CREATE INDEX idx_comment_post ON Comment(PostID);
CREATE INDEX idx_comment_member ON Comment(MemberID);
CREATE INDEX idx_like_target ON `Like`(TargetType, TargetID);
CREATE INDEX idx_follow_follower ON Follow(FollowerID);
CREATE INDEX idx_follow_following ON Follow(FollowingID);
CREATE INDEX idx_report_status ON Report(Status);
CREATE INDEX idx_message_receiver ON Message(ReceiverID);
CREATE INDEX idx_notification_member ON Notification(MemberID);
CREATE INDEX idx_activitylog_member ON ActivityLog(MemberID);
CREATE INDEX idx_activitylog_timestamp ON ActivityLog(`Timestamp` DESC);
CREATE INDEX idx_apiwritelog_time ON ApiWriteLog(ChangeTime DESC);
CREATE INDEX idx_apiwritelog_auth ON ApiWriteLog(IsAuthorized, SourceType);

-- ============================================================================
-- TRIGGERS for Business Rule Enforcement
-- Note: These triggers replace CHECK constraints that conflict with foreign key
--       CASCADE actions (MySQL Error 3823)
-- ============================================================================

-- Trigger 1: Prevent self-follow on INSERT
DELIMITER //
CREATE TRIGGER trg_follow_no_self_follow_insert
BEFORE INSERT ON Follow
FOR EACH ROW
BEGIN
    IF NEW.FollowerID = NEW.FollowingID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A user cannot follow themselves';
    END IF;
END//
DELIMITER ;

-- Trigger 2: Prevent self-follow on UPDATE
DELIMITER //
CREATE TRIGGER trg_follow_no_self_follow_update
BEFORE UPDATE ON Follow
FOR EACH ROW
BEGIN
    IF NEW.FollowerID = NEW.FollowingID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A user cannot follow themselves';
    END IF;
END//
DELIMITER ;

-- Trigger 3: Prevent self-message on INSERT
DELIMITER //
CREATE TRIGGER trg_message_no_self_message_insert
BEFORE INSERT ON Message
FOR EACH ROW
BEGIN
    IF NEW.SenderID = NEW.ReceiverID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A user cannot send a message to themselves';
    END IF;
END//
DELIMITER ;

-- Trigger 4: Prevent self-message on UPDATE
DELIMITER //
CREATE TRIGGER trg_message_no_self_message_update
BEFORE UPDATE ON Message
FOR EACH ROW
BEGIN
    IF NEW.SenderID = NEW.ReceiverID THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A user cannot send a message to themselves';
    END IF;
END//
DELIMITER ;

-- Trigger 5: Enforce report review logic on INSERT
DELIMITER //
CREATE TRIGGER trg_report_review_logic_insert
BEFORE INSERT ON Report
FOR EACH ROW
BEGIN
    IF (NEW.Status = 'Pending' AND NEW.ReviewedBy IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Pending reports cannot have a reviewer assigned';
    END IF;
    IF (NEW.Status != 'Pending' AND NEW.ReviewedBy IS NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Non-pending reports must have a reviewer assigned';
    END IF;
END//
DELIMITER ;

-- Trigger 6: Enforce report review logic on UPDATE
DELIMITER //
CREATE TRIGGER trg_report_review_logic_update
BEFORE UPDATE ON Report
FOR EACH ROW
BEGIN
    IF (NEW.Status = 'Pending' AND NEW.ReviewedBy IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Pending reports cannot have a reviewer assigned';
    END IF;
    IF (NEW.Status != 'Pending' AND NEW.ReviewedBy IS NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Non-pending reports must have a reviewer assigned';
    END IF;
END//
DELIMITER ;

-- Trigger 7: Track Post INSERT source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_post_insert
AFTER INSERT ON Post
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Post',
            'INSERT',
            CAST(NEW.PostID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Post insert by MemberID=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 8: Track Post UPDATE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_post_update
AFTER UPDATE ON Post
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Post',
            'UPDATE',
            CAST(NEW.PostID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Post update by MemberID=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 9: Track Post DELETE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_post_delete
AFTER DELETE ON Post
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Post',
            'DELETE',
            CAST(OLD.PostID AS CHAR),
            COALESCE(@api_actor_id, OLD.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Post delete by MemberID=', OLD.MemberID)
        );
END//
DELIMITER ;

-- Trigger 10: Track Comment INSERT source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_comment_insert
AFTER INSERT ON Comment
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Comment',
            'INSERT',
            CAST(NEW.CommentID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Comment insert by MemberID=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 11: Track Comment UPDATE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_comment_update
AFTER UPDATE ON Comment
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Comment',
            'UPDATE',
            CAST(NEW.CommentID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Comment update by MemberID=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 12: Track Comment DELETE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_comment_delete
AFTER DELETE ON Comment
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Comment',
            'DELETE',
            CAST(OLD.CommentID AS CHAR),
            COALESCE(@api_actor_id, OLD.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Comment delete by MemberID=', OLD.MemberID)
        );
END//
DELIMITER ;

-- Trigger 13: Track Member INSERT source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_member_insert
AFTER INSERT ON Member
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Member',
            'INSERT',
            CAST(NEW.MemberID AS CHAR),
            @api_actor_id,
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Member insert for ', NEW.Email)
        );
END//
DELIMITER ;

-- Trigger 14: Track Member UPDATE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_member_update
AFTER UPDATE ON Member
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Member',
            'UPDATE',
            CAST(NEW.MemberID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Member update for MemberID=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 15: Track Member DELETE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_member_delete
AFTER DELETE ON Member
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'Member',
            'DELETE',
            CAST(OLD.MemberID AS CHAR),
            @api_actor_id,
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('Member delete for ', OLD.Email)
        );
END//
DELIMITER ;

-- Trigger 16: Track GroupMember INSERT source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_groupmember_insert
AFTER INSERT ON GroupMember
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'GroupMember',
            'INSERT',
            CAST(NEW.GroupMemberID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('GroupMember insert: group=', NEW.GroupID, ', member=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 17: Track GroupMember UPDATE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_groupmember_update
AFTER UPDATE ON GroupMember
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'GroupMember',
            'UPDATE',
            CAST(NEW.GroupMemberID AS CHAR),
            COALESCE(@api_actor_id, NEW.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('GroupMember update: group=', NEW.GroupID, ', member=', NEW.MemberID)
        );
END//
DELIMITER ;

-- Trigger 18: Track GroupMember DELETE source (API vs direct DB)
DELIMITER //
CREATE TRIGGER trg_apiwritelog_groupmember_delete
AFTER DELETE ON GroupMember
FOR EACH ROW
BEGIN
    INSERT INTO ApiWriteLog
        (TableName, OperationType, RecordID, ActorMemberID, SourceType, IsAuthorized, ActionName, Endpoint, HttpMethod, Details)
    VALUES
        (
            'GroupMember',
            'DELETE',
            CAST(OLD.GroupMemberID AS CHAR),
            COALESCE(@api_actor_id, OLD.MemberID),
            IF(@api_authorized = 1, 'API', 'DIRECT_DB'),
            IF(@api_authorized = 1, TRUE, FALSE),
            @api_action,
            @api_endpoint,
            @api_method,
            CONCAT('GroupMember delete: group=', OLD.GroupID, ', member=', OLD.MemberID)
        );
END//
DELIMITER ;

-- ============================================================================
-- End of Schema
-- ============================================================================
