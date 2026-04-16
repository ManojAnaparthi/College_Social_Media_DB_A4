USE maaps;

-- Remove cross-shard foreign keys so filtering by MemberID does not cascade-delete
-- valid comments whose parent posts reside on another shard.

-- Drop FK(s) from Post
SET @fk_post := (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'Post'
      AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);
SET @sql := IF(
    @fk_post IS NULL,
    'SELECT ''No FK to drop on Post'' AS info',
    CONCAT('ALTER TABLE Post DROP FOREIGN KEY `', @fk_post, '`')
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Drop up to two FK(s) from Comment (PostID and MemberID refs)
SET @fk_comment := (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'Comment'
      AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);
SET @sql := IF(
    @fk_comment IS NULL,
    'SELECT ''No FK to drop on Comment (pass 1)'' AS info',
    CONCAT('ALTER TABLE Comment DROP FOREIGN KEY `', @fk_comment, '`')
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @fk_comment := (
    SELECT CONSTRAINT_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'Comment'
      AND REFERENCED_TABLE_NAME IS NOT NULL
    LIMIT 1
);
SET @sql := IF(
    @fk_comment IS NULL,
    'SELECT ''No FK to drop on Comment (pass 2)'' AS info',
    CONCAT('ALTER TABLE Comment DROP FOREIGN KEY `', @fk_comment, '`')
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Optional verification
SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('Post', 'Comment')
  AND REFERENCED_TABLE_NAME IS NOT NULL;
