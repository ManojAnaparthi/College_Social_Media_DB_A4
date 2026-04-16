USE maaps;

-- Keep only shard 1 records: MemberID % 3 = 1
DELETE FROM Comment WHERE (MemberID % 3) <> 1;
DELETE FROM Post    WHERE (MemberID % 3) <> 1;
DELETE FROM Member  WHERE (MemberID % 3) <> 1;

-- Verification
SELECT 'Member' AS TableName, COUNT(*) AS RowCount FROM Member
UNION ALL
SELECT 'Post', COUNT(*) FROM Post
UNION ALL
SELECT 'Comment', COUNT(*) FROM Comment;

SELECT @@hostname AS Hostname;
