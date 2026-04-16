USE maaps;

-- Keep only shard 0 records: MemberID % 3 = 0
DELETE FROM Comment WHERE (MemberID % 3) <> 0;
DELETE FROM Post    WHERE (MemberID % 3) <> 0;
DELETE FROM Member  WHERE (MemberID % 3) <> 0;

-- Verification
SELECT 'Member' AS TableName, COUNT(*) AS RowCount FROM Member
UNION ALL
SELECT 'Post', COUNT(*) FROM Post
UNION ALL
SELECT 'Comment', COUNT(*) FROM Comment;

SELECT @@hostname AS Hostname;
