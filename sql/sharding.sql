-- ============================================================================
-- CS 432 Assignment 4 – Sub-Task 2: Data Partitioning (Sharding)
-- Strategy : Hash-based sharding — shard_id = MemberID % 3
-- Tables   : Member, Post, Comment  (the three tables most frequently
--             touched by Assignment 2 API endpoints)
-- Shards   : shard_0_*, shard_1_*, shard_2_*
-- ============================================================================

USE college_social_media;

-- ============================================================================
-- STEP 1: Clean up any previous shard tables (idempotent re-run)
-- ============================================================================

DROP TABLE IF EXISTS shard_2_comment;
DROP TABLE IF EXISTS shard_1_comment;
DROP TABLE IF EXISTS shard_0_comment;

DROP TABLE IF EXISTS shard_2_post;
DROP TABLE IF EXISTS shard_1_post;
DROP TABLE IF EXISTS shard_0_post;

DROP TABLE IF EXISTS shard_2_member;
DROP TABLE IF EXISTS shard_1_member;
DROP TABLE IF EXISTS shard_0_member;

-- ============================================================================
-- STEP 2: Create shard tables for Member
-- Note: Foreign-key constraints are intentionally omitted – in a real
--       distributed system each node is isolated; FK references would be
--       cross-node and unenforceable.
-- ============================================================================

CREATE TABLE shard_0_member (
    MemberID        INT PRIMARY KEY,
    Name            VARCHAR(100)  NOT NULL,
    Email           VARCHAR(100)  NOT NULL,
    ContactNumber   VARCHAR(15)   NOT NULL,
    Image           VARCHAR(255)  DEFAULT 'default_avatar.jpg',
    CollegeID       VARCHAR(20)   NOT NULL,
    Role            ENUM('Student','Faculty','Staff','Admin') NOT NULL DEFAULT 'Student',
    Department      VARCHAR(50)   NOT NULL,
    Age             INT,
    IsVerified      BOOLEAN       NOT NULL DEFAULT FALSE,
    JoinDate        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastLogin       DATETIME,
    Bio             TEXT,
    ShardID         TINYINT       NOT NULL DEFAULT 0  -- bookkeeping column
);

CREATE TABLE shard_1_member LIKE shard_0_member;
ALTER TABLE shard_1_member MODIFY ShardID TINYINT NOT NULL DEFAULT 1;

CREATE TABLE shard_2_member LIKE shard_0_member;
ALTER TABLE shard_2_member MODIFY ShardID TINYINT NOT NULL DEFAULT 2;

-- ============================================================================
-- STEP 3: Create shard tables for Post
-- Shard key: MemberID (owner of the post)
-- ============================================================================

CREATE TABLE shard_0_post (
    PostID          INT           NOT NULL,
    MemberID        INT           NOT NULL,
    Content         TEXT          NOT NULL,
    MediaURL        VARCHAR(255),
    MediaType       ENUM('Image','Video','Document','None') NOT NULL DEFAULT 'None',
    PostDate        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastEditDate    DATETIME,
    Visibility      ENUM('Public','Followers','Private') NOT NULL DEFAULT 'Public',
    IsActive        BOOLEAN       NOT NULL DEFAULT TRUE,
    LikeCount       INT           NOT NULL DEFAULT 0,
    CommentCount    INT           NOT NULL DEFAULT 0,
    ShardID         TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (PostID)
);

CREATE TABLE shard_1_post LIKE shard_0_post;
ALTER TABLE shard_1_post MODIFY ShardID TINYINT NOT NULL DEFAULT 1;

CREATE TABLE shard_2_post LIKE shard_0_post;
ALTER TABLE shard_2_post MODIFY ShardID TINYINT NOT NULL DEFAULT 2;

-- ============================================================================
-- STEP 4: Create shard tables for Comment
-- Shard key: MemberID (author of the comment)
-- ============================================================================

CREATE TABLE shard_0_comment (
    CommentID       INT           NOT NULL,
    PostID          INT           NOT NULL,
    MemberID        INT           NOT NULL,
    Content         TEXT          NOT NULL,
    CommentDate     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastEditDate    DATETIME,
    IsActive        BOOLEAN       NOT NULL DEFAULT TRUE,
    LikeCount       INT           NOT NULL DEFAULT 0,
    ShardID         TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (CommentID)
);

CREATE TABLE shard_1_comment LIKE shard_0_comment;
ALTER TABLE shard_1_comment MODIFY ShardID TINYINT NOT NULL DEFAULT 1;

CREATE TABLE shard_2_comment LIKE shard_0_comment;
ALTER TABLE shard_2_comment MODIFY ShardID TINYINT NOT NULL DEFAULT 2;

-- ============================================================================
-- STEP 5: Migrate Member data into the correct shard
--         shard_id = MemberID % 3
-- ============================================================================

INSERT INTO shard_0_member (MemberID, Name, Email, ContactNumber, Image, CollegeID,
                             Role, Department, Age, IsVerified, JoinDate, LastLogin, Bio)
SELECT MemberID, Name, Email, ContactNumber, Image, CollegeID,
       Role, Department, Age, IsVerified, JoinDate, LastLogin, Bio
FROM   Member
WHERE  (MemberID % 3) = 0;

INSERT INTO shard_1_member (MemberID, Name, Email, ContactNumber, Image, CollegeID,
                             Role, Department, Age, IsVerified, JoinDate, LastLogin, Bio)
SELECT MemberID, Name, Email, ContactNumber, Image, CollegeID,
       Role, Department, Age, IsVerified, JoinDate, LastLogin, Bio
FROM   Member
WHERE  (MemberID % 3) = 1;

INSERT INTO shard_2_member (MemberID, Name, Email, ContactNumber, Image, CollegeID,
                             Role, Department, Age, IsVerified, JoinDate, LastLogin, Bio)
SELECT MemberID, Name, Email, ContactNumber, Image, CollegeID,
       Role, Department, Age, IsVerified, JoinDate, LastLogin, Bio
FROM   Member
WHERE  (MemberID % 3) = 2;

-- ============================================================================
-- STEP 6: Migrate Post data into the correct shard
-- ============================================================================

INSERT INTO shard_0_post (PostID, MemberID, Content, MediaURL, MediaType,
                           PostDate, LastEditDate, Visibility, IsActive, LikeCount, CommentCount)
SELECT PostID, MemberID, Content, MediaURL, MediaType,
       PostDate, LastEditDate, Visibility, IsActive, LikeCount, CommentCount
FROM   Post
WHERE  (MemberID % 3) = 0;

INSERT INTO shard_1_post (PostID, MemberID, Content, MediaURL, MediaType,
                           PostDate, LastEditDate, Visibility, IsActive, LikeCount, CommentCount)
SELECT PostID, MemberID, Content, MediaURL, MediaType,
       PostDate, LastEditDate, Visibility, IsActive, LikeCount, CommentCount
FROM   Post
WHERE  (MemberID % 3) = 1;

INSERT INTO shard_2_post (PostID, MemberID, Content, MediaURL, MediaType,
                           PostDate, LastEditDate, Visibility, IsActive, LikeCount, CommentCount)
SELECT PostID, MemberID, Content, MediaURL, MediaType,
       PostDate, LastEditDate, Visibility, IsActive, LikeCount, CommentCount
FROM   Post
WHERE  (MemberID % 3) = 2;

-- ============================================================================
-- STEP 7: Migrate Comment data into the correct shard
-- ============================================================================

INSERT INTO shard_0_comment (CommentID, PostID, MemberID, Content,
                              CommentDate, LastEditDate, IsActive, LikeCount)
SELECT CommentID, PostID, MemberID, Content,
       CommentDate, LastEditDate, IsActive, LikeCount
FROM   Comment
WHERE  (MemberID % 3) = 0;

INSERT INTO shard_1_comment (CommentID, PostID, MemberID, Content,
                              CommentDate, LastEditDate, IsActive, LikeCount)
SELECT CommentID, PostID, MemberID, Content,
       CommentDate, LastEditDate, IsActive, LikeCount
FROM   Comment
WHERE  (MemberID % 3) = 1;

INSERT INTO shard_2_comment (CommentID, PostID, MemberID, Content,
                              CommentDate, LastEditDate, IsActive, LikeCount)
SELECT CommentID, PostID, MemberID, Content,
       CommentDate, LastEditDate, IsActive, LikeCount
FROM   Comment
WHERE  (MemberID % 3) = 2;

-- ============================================================================
-- STEP 8: Verification – confirm total row counts match source tables
--         and that no duplicates exist across shards.
-- ============================================================================

-- Member verification
SELECT 'Member - Source total' AS Label, COUNT(*) AS RowCount FROM Member
UNION ALL
SELECT 'shard_0_member', COUNT(*) FROM shard_0_member
UNION ALL
SELECT 'shard_1_member', COUNT(*) FROM shard_1_member
UNION ALL
SELECT 'shard_2_member', COUNT(*) FROM shard_2_member
UNION ALL
SELECT 'Member - Shard union total',
       (SELECT COUNT(*) FROM shard_0_member) +
       (SELECT COUNT(*) FROM shard_1_member) +
       (SELECT COUNT(*) FROM shard_2_member);

-- Post verification
SELECT 'Post - Source total' AS Label, COUNT(*) AS RowCount FROM Post
UNION ALL
SELECT 'shard_0_post', COUNT(*) FROM shard_0_post
UNION ALL
SELECT 'shard_1_post', COUNT(*) FROM shard_1_post
UNION ALL
SELECT 'shard_2_post', COUNT(*) FROM shard_2_post
UNION ALL
SELECT 'Post - Shard union total',
       (SELECT COUNT(*) FROM shard_0_post) +
       (SELECT COUNT(*) FROM shard_1_post) +
       (SELECT COUNT(*) FROM shard_2_post);

-- Comment verification
SELECT 'Comment - Source total' AS Label, COUNT(*) AS RowCount FROM Comment
UNION ALL
SELECT 'shard_0_comment', COUNT(*) FROM shard_0_comment
UNION ALL
SELECT 'shard_1_comment', COUNT(*) FROM shard_1_comment
UNION ALL
SELECT 'shard_2_comment', COUNT(*) FROM shard_2_comment
UNION ALL
SELECT 'Comment - Shard union total',
       (SELECT COUNT(*) FROM shard_0_comment) +
       (SELECT COUNT(*) FROM shard_1_comment) +
       (SELECT COUNT(*) FROM shard_2_comment);

-- Cross-shard duplicate check (should return 0 rows for each pair)
SELECT 'Member cross-shard duplicate pairs' AS Check_label,
       COUNT(*) AS Duplicates
FROM (
    SELECT MemberID FROM shard_0_member
    UNION ALL
    SELECT MemberID FROM shard_1_member
    UNION ALL
    SELECT MemberID FROM shard_2_member
) all_ids
GROUP BY MemberID
HAVING COUNT(*) > 1;

SELECT 'Post cross-shard duplicate pairs' AS Check_label,
       COUNT(*) AS Duplicates
FROM (
    SELECT PostID FROM shard_0_post
    UNION ALL
    SELECT PostID FROM shard_1_post
    UNION ALL
    SELECT PostID FROM shard_2_post
) all_post_ids
GROUP BY PostID
HAVING COUNT(*) > 1;

SELECT 'Comment cross-shard duplicate pairs' AS Check_label,
       COUNT(*) AS Duplicates
FROM (
    SELECT CommentID FROM shard_0_comment
    UNION ALL
    SELECT CommentID FROM shard_1_comment
    UNION ALL
    SELECT CommentID FROM shard_2_comment
) all_comment_ids
GROUP BY CommentID
HAVING COUNT(*) > 1;

-- ============================================================================
-- End of Sub-Task 2
-- ============================================================================
