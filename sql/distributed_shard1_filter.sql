USE maaps;

-- Keep only shard 1 records: CRC32(str(MemberID)) % 3 = 1
DELETE FROM Comment WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 1;
DELETE FROM Post    WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 1;
DELETE FROM Member  WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 1;

-- Verification
SELECT 'Member' AS TableName, COUNT(*) AS RowCount FROM Member
UNION ALL
SELECT 'Post', COUNT(*) FROM Post
UNION ALL
SELECT 'Comment', COUNT(*) FROM Comment;

SELECT @@hostname AS Hostname;
