USE maaps;

-- Keep only shard 2 records: MemberID % 3 = 2
DELETE FROM Comment WHERE (MemberID % 3) <> 2;
DELETE FROM Post    WHERE (MemberID % 3) <> 2;
DELETE FROM Member  WHERE (MemberID % 3) <> 2;

-- Verification
SELECT 'Member' AS TableName, COUNT(*) AS RowCount FROM Member
UNION ALL
SELECT 'Post', COUNT(*) FROM Post
UNION ALL
SELECT 'Comment', COUNT(*) FROM Comment;

SELECT @@hostname AS Hostname;
