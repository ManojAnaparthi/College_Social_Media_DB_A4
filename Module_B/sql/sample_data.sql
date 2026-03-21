-- ============================================================================
-- College Social Media Platform - Sample Data
-- CS 432 - Databases Assignment 1
-- ============================================================================

-- ============================================================================
-- Insert Sample Data into Member Table (20 rows)
-- ============================================================================
USE college_social_media;

INSERT INTO Member (Name, Email, ContactNumber, Image, CollegeID, Role, Department, Age, IsVerified, Bio) VALUES
('Rahul Sharma', 'rahul.sharma@iitgn.ac.in', '9876543210', 'rahul.jpg', 'IITGN2023001', 'Student', 'Computer Science', 21, TRUE, 'CS undergrad | AI enthusiast | Love coding'),
('Priya Patel', 'priya.patel@iitgn.ac.in', '9876543211', 'priya.jpg', 'IITGN2024002', 'Student', 'Electrical Engineering', 20, TRUE, 'EE sophomore | Robotics club member'),
('Dr. Amit Kumar', 'amit.kumar@iitgn.ac.in', '9876543212', 'amit.jpg', 'IITGN2010FAC01', 'Faculty', 'Computer Science', 42, TRUE, 'Associate Professor | Database Systems'),
('Sneha Gupta', 'sneha.gupta@iitgn.ac.in', '9876543213', 'sneha.jpg', 'IITGN2022003', 'Student', 'Mechanical Engineering', 22, TRUE, 'Mech senior | Formula student team captain'),
('Arjun Reddy', 'arjun.reddy@iitgn.ac.in', '9876543214', 'arjun.jpg', 'IITGN2021004', 'Student', 'Chemical Engineering', 23, TRUE, 'ChemE | Research enthusiast | Photography'),
('Ananya Singh', 'ananya.singh@iitgn.ac.in', '9876543215', 'ananya.jpg', 'IITGN2023005', 'Student', 'Computer Science', 21, TRUE, 'CS junior | Web dev | Open source contributor'),
('Vikram Joshi', 'vikram.joshi@iitgn.ac.in', '9876543216', 'vikram.jpg', 'IITGN2024006', 'Student', 'Civil Engineering', 19, TRUE, 'Civil sophomore | Debate club | Music'),
('Dr. Meera Shah', 'meera.shah@iitgn.ac.in', '9876543217', 'meera.jpg', 'IITGN2015FAC02', 'Faculty', 'Mathematics', 38, TRUE, 'Assistant Professor | Applied Mathematics'),
('Karan Malhotra', 'karan.malhotra@iitgn.ac.in', '9876543218', 'karan.jpg', 'IITGN2022007', 'Student', 'Electrical Engineering', 22, TRUE, 'EE | Embedded systems | IoT projects'),
('Neha Desai', 'neha.desai@iitgn.ac.in', '9876543219', 'neha.jpg', 'IITGN2023008', 'Student', 'Computer Science', 21, TRUE, 'CS | ML researcher | Hackathon winner'),
('Rohan Kapoor', 'rohan.kapoor@iitgn.ac.in', '9876543220', 'rohan.jpg', 'IITGN2021009', 'Student', 'Mechanical Engineering', 23, TRUE, 'Mech | CAD design | 3D printing'),
('Ishita Agarwal', 'ishita.agarwal@iitgn.ac.in', '9876543221', 'ishita.jpg', 'IITGN2024010', 'Student', 'Chemical Engineering', 18, TRUE, 'ChemE freshman | Coding club'),
('Aditya Verma', 'aditya.verma@iitgn.ac.in', '9876543222', 'aditya.jpg', 'IITGN2022011', 'Student', 'Computer Science', 22, TRUE, 'CS | Cybersecurity | CTF player'),
('Pooja Rao', 'pooja.rao@iitgn.ac.in', '9876543223', 'pooja.jpg', 'IITGN2023012', 'Student', 'Civil Engineering', 21, TRUE, 'Civil | Architecture | Sustainability'),
('Siddharth Mishra', 'siddharth.mishra@iitgn.ac.in', '9876543224', 'siddharth.jpg', 'IITGN2024013', 'Student', 'Electrical Engineering', 19, TRUE, 'EE | Electronics | Circuit design'),
('Divya Nair', 'divya.nair@iitgn.ac.in', '9876543225', 'divya.jpg', 'IITGN2021014', 'Student', 'Computer Science', 24, TRUE, 'CS senior | Full stack dev | Placement coordinator'),
('Abhishek Pandey', 'abhishek.pandey@iitgn.ac.in', '9876543226', 'abhishek.jpg', 'IITGN2022015', 'Student', 'Mechanical Engineering', 22, TRUE, 'Mech | Thermodynamics | Sports enthusiast'),
('Sakshi Jain', 'sakshi.jain@iitgn.ac.in', '9876543227', 'sakshi.jpg', 'IITGN2023016', 'Student', 'Chemical Engineering', 21, TRUE, 'ChemE | Process design | Dance team'),
('Varun Saxena', 'varun.saxena@iitgn.ac.in', '9876543228', 'varun.jpg', 'IITGN2018STAFF01', 'Staff', 'Administration', 34, TRUE, 'Network Administrator | IT Support'),
('Kavya Krishnan', 'kavya.krishnan@iitgn.ac.in', '9876543229', 'kavya.jpg', 'IITGN2024017', 'Student', 'Computer Science', 18, TRUE, 'CS freshman | AI/ML | Competitive programmer');

-- ============================================================================
-- Insert Sample Data into AuthCredential Table (20 rows)
-- NOTE: Sample credentials are bcrypt hashes for password123.
-- ============================================================================
INSERT INTO AuthCredential (MemberID, PasswordHash) VALUES
(1, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(2, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(3, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(4, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(5, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(6, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(7, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(8, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(9, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(10, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(11, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(12, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(13, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(14, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(15, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(16, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(17, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(18, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(19, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.'),
(20, '$2b$12$ZlrjAqIhjysU8/Z2DSHfceI56lty5MluK3gvjNdSvPkRTe.Yh3.D.');

-- ============================================================================
-- Insert Sample Data into Follow Table (20 rows)
-- ============================================================================
INSERT INTO Follow (FollowerID, FollowingID) VALUES
(1, 2), (1, 3), (1, 6), (1, 10),
(2, 1), (2, 6), (2, 9),
(4, 1), (4, 5), (4, 11),
(6, 1), (6, 10), (6, 13),
(10, 1), (10, 6),
(3, 1), (5, 2), (7, 4), (8, 1), (12, 6);

-- ============================================================================
-- Insert Sample Data into Post Table (20 rows)
-- ============================================================================
INSERT INTO Post (MemberID, Content, MediaURL, MediaType, Visibility, LikeCount, CommentCount) VALUES
(1, 'Just finished my database assignment! Really enjoyed designing the schema for our college social media platform. 🎓', 'post1.jpg', 'Image', 'Public', 3, 3),
(2, 'Excited to share that our robotics team qualified for the national competition! Hard work pays off! 🤖', 'robot.jpg', 'Image', 'Public', 2, 2),
(3, 'Reminder: Database Systems midterm exam on February 15th. Office hours this Friday 2-4 PM.', NULL, 'None', 'Public', 1, 3),
(4, 'Our Formula Student car testing went amazingly well today! Can''t wait for the competition season.', 'car_test.mp4', 'Video', 'Public', 1, 2),
(5, 'Published my research paper on catalytic reactions! Link in bio. Thank you to all my lab mates! 📚', 'paper.pdf', 'Document', 'Public', 1, 1),
(6, 'Working on a new web application using React and Node.js. Open source project coming soon! 💻', 'webapp.jpg', 'Image', 'Public', 2, 2),
(7, 'Won the inter-college debate competition! Topic: AI Ethics and Regulation. Great experience!', 'debate.jpg', 'Image', 'Public', 0, 1),
(8, 'New course announcement: Advanced Topics in Applied Mathematics - Spring 2026. Registration open!', NULL, 'None', 'Public', 1, 2),
(9, 'Built an IoT-based smart irrigation system for our campus garden. Sustainability matters! 🌱', 'iot.jpg', 'Image', 'Public', 0, 0),
(10, 'Won first place at the National Hackathon with my ML-based healthcare prediction model! 🏆', 'hackathon.jpg', 'Image', 'Public', 3, 3),
(11, 'CAD model of our new mechanical project. 3D printing starts tomorrow!', 'cad.jpg', 'Image', 'Followers', 0, 0),
(1, 'Anyone interested in forming a study group for algorithms? DM me!', NULL, 'None', 'Public', 0, 0),
(13, 'Participated in my first CTF competition. Cybersecurity is fascinating!', NULL, 'None', 'Public', 0, 0),
(14, 'Campus sustainability initiative: Join us for tree plantation this Sunday!', 'trees.jpg', 'Image', 'Public', 0, 0),
(6, 'Just deployed my portfolio website. Check it out and give feedback! Link in bio.', NULL, 'None', 'Public', 0, 0),
(16, 'Placement season tips: Start preparing early, practice DSA daily, and network effectively!', NULL, 'None', 'Public', 1, 0),
(4, 'Engineering is not just about calculations, it''s about creativity and problem solving! 💡', NULL, 'None', 'Public', 0, 0),
(10, 'Research paper accepted at ICML 2026! Dreams do come true with hard work! 🎉', 'acceptance.jpg', 'Image', 'Public', 0, 1),
(20, 'Learning Python for data science. Any good resource recommendations?', NULL, 'None', 'Public', 0, 0),
(2, 'Circuit design workshop this Saturday in EE lab. All departments welcome!', 'circuit.jpg', 'Image', 'Public', 0, 0);

-- ============================================================================
-- Insert Sample Data into Comment Table (20 rows)
-- ============================================================================
INSERT INTO Comment (PostID, MemberID, Content, LikeCount) VALUES
(1, 2, 'Great work Rahul! Your schema design looks solid!', 3),
(1, 6, 'Can you share your ER diagram? Would love to see it!', 2),
(1, 10, 'Database design is so interesting! Good job!', 1),
(2, 1, 'Congratulations Priya! Your team deserves it!', 5),
(2, 9, 'Amazing achievement! Best of luck for nationals!', 4),
(3, 1, 'Thank you sir! Will attend office hours.', 2),
(3, 6, 'What topics should we focus on for the exam?', 8),
(3, 13, 'Is the exam open book or closed book?', 3),
(4, 1, 'That''s awesome! Formula Student is so cool!', 4),
(4, 11, 'Great job team! The car looks fantastic!', 3),
(5, 3, 'Excellent research Arjun! Congratulations!', 6),
(6, 1, 'Looking forward to the open source project!', 2),
(6, 10, 'Which tech stack are you using?', 4),
(7, 2, 'Well done Vikram! You spoke brilliantly!', 3),
(8, 1, 'Will definitely register for this course!', 5),
(8, 6, 'What are the prerequisites for this course?', 4),
(10, 1, 'Incredible Neha! You''re an inspiration!', 7),
(10, 6, 'Wow! Can you share details about your model?', 5),
(10, 13, 'Congratulations! Healthcare + ML is the future!', 6),
(18, 1, 'Congratulations Neha! ICML is prestigious!', 9);

-- ============================================================================
-- Insert Sample Data into Like Table (20 rows)
-- ============================================================================
INSERT INTO `Like` (MemberID, TargetType, TargetID) VALUES
(1, 'Post', 2), (1, 'Post', 3), (1, 'Post', 10),
(2, 'Post', 1), (2, 'Post', 4), (2, 'Post', 6),
(3, 'Post', 5), (3, 'Post', 8), (3, 'Post', 10),
(6, 'Post', 1), (6, 'Post', 2), (6, 'Post', 10),
(10, 'Post', 1), (10, 'Post', 6), (10, 'Post', 16),
(1, 'Comment', 1), (2, 'Comment', 4), (6, 'Comment', 7),
(10, 'Comment', 17), (13, 'Comment', 19);

-- ============================================================================
-- Insert Sample Data into Report Table (15 rows) - Explicit ReportDates included
-- ============================================================================
INSERT INTO Report (ReporterID, ReportedItemType, ReportedItemID, Reason, Status, ReportDate, ReviewedBy, ReviewDate, Action) VALUES
(2, 'Post', 13, 'Spam content with irrelevant links', 'Resolved', '2026-02-01 09:30:00', 3, '2026-02-01 10:30:00', 'Post removed'),
(6, 'Comment', 8, 'Inappropriate language used', 'Resolved', '2026-02-01 13:20:00', 3, '2026-02-01 14:20:00', 'Comment deleted'),
(10, 'Member', 15, 'Fake profile using someone else''s photo', 'Reviewed', '2026-02-02 08:15:00', 3, '2026-02-02 09:15:00', 'Under investigation'),
(1, 'Post', 7, 'Misleading information about exam dates', 'Dismissed', '2026-02-02 15:45:00', 3, '2026-02-02 16:45:00', 'Verified as accurate'),
(4, 'Comment', 12, 'Harassment and bullying', 'Resolved', '2026-02-03 10:00:00', 8, '2026-02-03 11:00:00', 'User warned'),
(9, 'Post', 15, 'Advertisement of external services', 'Pending', '2026-02-03 12:00:00', NULL, NULL, NULL),
(13, 'Member', 7, 'Creating multiple fake accounts', 'Pending', '2026-02-03 14:00:00', NULL, NULL, NULL),
(14, 'Post', 19, 'Copyright violation - using others'' work', 'Reviewed', '2026-02-03 14:30:00', 3, '2026-02-03 15:30:00', 'Asked for attribution'),
(6, 'Comment', 15, 'Off-topic spam comments', 'Resolved', '2026-02-04 07:20:00', 8, '2026-02-04 08:20:00', 'Comment removed'),
(1, 'Post', 11, 'Sensitive personal information shared', 'Resolved', '2026-02-04 09:00:00', 3, '2026-02-04 10:00:00', 'Post edited'),
(10, 'Comment', 19, 'Hate speech and discrimination', 'Pending', '2026-02-04 11:00:00', NULL, NULL, NULL),
(16, 'Member', 20, 'Impersonating faculty member', 'Reviewed', '2026-02-04 11:15:00', 3, '2026-02-04 12:15:00', 'Profile verification required'),
(11, 'Post', 3, 'Duplicate announcement content', 'Dismissed', '2026-02-05 11:00:00', 3, '2026-02-05 12:00:00', 'No issue found'),
(12, 'Comment', 5, 'Uncivil tone in discussion', 'Resolved', '2026-02-05 12:30:00', 8, '2026-02-05 13:30:00', 'Comment removed'),
(15, 'Post', 2, 'Suspicious links in post', 'Pending', '2026-02-05 14:00:00', NULL, NULL, NULL);

-- ============================================================================
-- Insert Sample Data into Group Table (15 rows)
-- ============================================================================
INSERT INTO `Group` (Name, Description, CreatorID, Category, MemberCount) VALUES
('Coding Club IITGN', 'A community for programming enthusiasts. Weekly coding sessions and hackathons.', 1, 'Tech', 45),
('Robotics Club', 'Building robots, competing in national events, and learning automation.', 2, 'Tech', 32),
('Formula Student Team', 'Designing and building formula-style race cars for international competitions.', 4, 'Tech', 28),
('Machine Learning Study Group', 'Discussing ML algorithms, research papers, and working on AI projects.', 10, 'Academic', 38),
('Debate Society', 'Enhancing public speaking and critical thinking through debates and MUNs.', 7, 'Cultural', 41),
('Photography Club', 'Campus photography, workshops, and exhibitions.', 5, 'Cultural', 35),
('CS Department Forum', 'Academic discussions, doubt clearing, and resource sharing for CS students.', 6, 'Academic', 67),
('Sustainability Initiative', 'Environmental awareness, tree plantation, and green campus initiatives.', 14, 'Other', 52),
('Math Circle', 'Problem solving sessions, math competitions, and research discussions.', 8, 'Academic', 29),
('Dance Team', 'Cultural performances, choreography, and dance competitions.', 18, 'Cultural', 44),
('Placement Preparation', 'Interview preparation, mock tests, and placement strategies.', 16, 'Academic', 89),
('Sports Enthusiasts', 'Organizing sports events, tournaments, and fitness activities.', 17, 'Sports', 56),
('IoT Makers', 'Building IoT projects, smart devices, and embedded systems.', 9, 'Tech', 24),
('Open Source Contributors', 'Contributing to open source projects and learning collaborative development.', 6, 'Tech', 31),
('Research Scholars', 'Research paper discussions, collaboration opportunities, and academic writing.', 5, 'Academic', 22);

-- ============================================================================
-- Insert Sample Data into GroupMember Table (20 rows)
-- ============================================================================
INSERT INTO GroupMember (GroupID, MemberID, Role) VALUES
(1, 1, 'Admin'), (1, 6, 'Moderator'), (1, 10, 'Member'), (1, 13, 'Member'), (1, 20, 'Member'),
(2, 2, 'Admin'), (2, 9, 'Moderator'), (2, 15, 'Member'),
(3, 4, 'Admin'), (3, 11, 'Moderator'), (3, 17, 'Member'),
(4, 10, 'Admin'), (4, 1, 'Member'), (4, 6, 'Member'), (4, 20, 'Member'),
(5, 7, 'Admin'), (5, 2, 'Member'),
(7, 6, 'Admin'), (7, 1, 'Moderator'), (7, 10, 'Member');

-- ============================================================================
-- Insert Sample Data into Message Table (20 rows) - Explicit SendDates included
-- ============================================================================
INSERT INTO Message (SenderID, ReceiverID, Content, SendDate, IsRead, ReadDate) VALUES
(1, 2, 'Hey Priya! Congratulations on the robotics competition qualification!', '2026-02-01 10:00:00', TRUE, '2026-02-01 10:15:00'),
(2, 1, 'Thanks Rahul! How is your database assignment going?', '2026-02-01 10:20:00', TRUE, '2026-02-01 10:30:00'),
(6, 1, 'Can you help me with the normalization concepts? I''m a bit confused.', '2026-02-02 14:00:00', TRUE, '2026-02-02 14:20:00'),
(1, 6, 'Sure! Let''s meet in the library at 4 PM today.', '2026-02-02 14:30:00', TRUE, '2026-02-02 14:35:00'),
(10, 1, 'Hey! Want to team up for the upcoming hackathon?', '2026-02-02 18:00:00', TRUE, '2026-02-02 18:45:00'),
(1, 10, 'Absolutely! Your ML skills + my backend development = winning combo!', '2026-02-02 18:50:00', TRUE, '2026-02-02 19:00:00'),
(4, 11, 'The CAD files for the new chassis are ready. Check your email.', '2026-02-03 09:00:00', TRUE, '2026-02-03 09:30:00'),
(13, 1, 'Any resources for learning penetration testing?', '2026-02-03 10:00:00', FALSE, NULL),
(14, 4, 'Are you joining the sustainability event this Sunday?', '2026-02-03 16:00:00', TRUE, '2026-02-03 16:20:00'),
(6, 10, 'I checked out your ML model. Impressive accuracy! Can we collaborate?', '2026-02-04 08:30:00', TRUE, '2026-02-04 08:40:00'),
(10, 6, 'Thanks! Yes, let''s work on a project together.', '2026-02-04 09:00:00', TRUE, '2026-02-04 09:10:00'),
(16, 1, 'Need any help with placement preparation? I can share some resources.', '2026-02-04 10:00:00', FALSE, NULL),
(7, 5, 'Great research paper! Can I cite it in my presentation?', '2026-02-04 11:00:00', TRUE, '2026-02-04 11:25:00'),
(9, 2, 'Want to collaborate on an IoT project for the smart campus?', '2026-02-04 12:00:00', FALSE, NULL),
(20, 10, 'I''m new to ML. Can you suggest some beginner-friendly projects?', '2026-02-04 13:00:00', FALSE, NULL),
(2, 6, 'Are you joining the ML study group this week?', '2026-02-04 14:00:00', FALSE, NULL),
(5, 1, 'Can you review my draft before submission?', '2026-02-05 09:00:00', FALSE, NULL),
(3, 10, 'Please share the rubric for Assignment 1.', '2026-02-05 09:30:00', TRUE, '2026-02-05 10:00:00'),
(8, 4, 'Math Circle meeting tomorrow at 5 PM in the seminar room.', '2026-02-05 17:00:00', TRUE, '2026-02-05 17:15:00'),
(11, 4, 'Great CAD model! Can you send the STL file?', '2026-02-05 18:00:00', FALSE, NULL);

-- ============================================================================
-- Insert Sample Data into Notification Table (20 rows) - Explicit CreateDates included
-- ============================================================================
INSERT INTO Notification (MemberID, Type, Content, ReferenceID, CreateDate, IsRead, ReadDate) VALUES
(1, 'Like', 'Priya Patel liked your post about database assignment', 1, '2026-02-01 09:00:00', TRUE, '2026-02-01 09:15:00'),
(1, 'Comment', 'Ananya Singh commented on your post', 1, '2026-02-01 09:15:00', TRUE, '2026-02-01 09:30:00'),
(1, 'Follow', 'Neha Desai started following you', 10, '2026-02-01 10:00:00', TRUE, '2026-02-01 11:00:00'),
(2, 'Like', 'Rahul Sharma liked your post about robotics competition', 2, '2026-02-01 12:00:00', TRUE, '2026-02-01 12:20:00'),
(6, 'Comment', 'Rahul Sharma commented on your post', 6, '2026-02-02 10:00:00', TRUE, '2026-02-02 10:45:00'),
(10, 'Like', 'Multiple people liked your hackathon achievement post', 10, '2026-02-02 15:00:00', TRUE, '2026-02-02 15:30:00'),
(3, 'Comment', 'Students commented on your exam announcement', 3, '2026-02-01 15:00:00', TRUE, '2026-02-01 16:00:00'),
(4, 'Like', 'Rohan Kapoor liked your Formula Student post', 4, '2026-02-02 09:00:00', FALSE, NULL),
(5, 'Comment', 'Dr. Amit Kumar commented on your research paper', 5, '2026-02-02 08:00:00', TRUE, '2026-02-02 08:15:00'),
(6, 'Follow', 'Kavya Krishnan started following you', 20, '2026-02-02 10:00:00', FALSE, NULL),
(7, 'Like', 'Priya Patel liked your debate competition post', 7, '2026-02-02 14:00:00', TRUE, '2026-02-02 14:40:00'),
(1, 'GroupInvite', 'You have been invited to join Machine Learning Study Group', 4, '2026-02-03 09:00:00', FALSE, NULL),
(10, 'Mention', 'Rahul Sharma mentioned you in a comment', 12, '2026-02-03 09:30:00', TRUE, '2026-02-03 09:50:00'),
(16, 'Comment', 'Multiple students commented on your placement tips post', 16, '2026-02-03 17:00:00', TRUE, '2026-02-03 17:20:00'),
(1, 'Like', 'Neha Desai liked your comment', 16, '2026-02-04 09:00:00', FALSE, NULL),
(6, 'Comment', 'Neha Desai commented on your web application post', 6, '2026-02-04 10:00:00', TRUE, '2026-02-04 10:15:00'),
(14, 'Like', 'Multiple people liked your sustainability post', 14, '2026-02-04 11:00:00', FALSE, NULL),
(2, 'Comment', 'Vikram Saxena commented on your circuit workshop post', 20, '2026-02-04 12:00:00', FALSE, NULL),
(10, 'Like', 'Everyone is congratulating you on ICML acceptance!', 18, '2026-02-04 11:30:00', TRUE, '2026-02-04 11:45:00'),
(20, 'Comment', 'Students shared Python learning resources', 19, '2026-02-04 14:00:00', FALSE, NULL);

-- ============================================================================
-- Insert Sample Data into ActivityLog Table (20 rows)
-- ============================================================================
INSERT INTO ActivityLog (MemberID, ActivityType, Details, IPAddress, `Timestamp`) VALUES
(1, 'Login', 'User logged in successfully', '192.168.1.101', '2026-02-01 08:00:00'),
(1, 'Post', 'Created new post about database assignment', '192.168.1.101', '2026-02-01 09:00:00'),
(2, 'Login', 'User logged in successfully', '192.168.1.102', '2026-02-01 08:30:00'),
(2, 'Post', 'Created post about robotics competition', '192.168.1.102', '2026-02-01 09:45:00'),
(3, 'Login', 'User logged in successfully', '192.168.1.103', '2026-02-01 10:00:00'),
(3, 'Post', 'Posted exam reminder announcement', '192.168.1.103', '2026-02-01 10:15:00'),
(6, 'Login', 'User logged in successfully', '192.168.1.106', '2026-02-01 14:00:00'),
(6, 'Comment', 'Commented on post ID 1', '192.168.1.106', '2026-02-01 14:10:00'),
(10, 'Login', 'User logged in successfully', '192.168.1.110', '2026-02-02 07:30:00'),
(10, 'Post', 'Shared hackathon achievement', '192.168.1.110', '2026-02-02 08:00:00'),
(1, 'Like', 'Liked multiple posts', '192.168.1.101', '2026-02-02 09:30:00'),
(6, 'ProfileUpdate', 'Updated bio and profile picture', '192.168.1.106', '2026-02-02 15:20:00'),
(13, 'Login', 'User logged in successfully', '192.168.1.113', '2026-02-03 08:45:00'),
(13, 'Post', 'Posted about CTF competition', '192.168.1.113', '2026-02-03 09:00:00'),
(14, 'Post', 'Created sustainability initiative post', '192.168.1.114', '2026-02-03 10:30:00'),
(2, 'Report', 'Reported spam content', '192.168.1.102', '2026-02-01 10:30:00'),
(16, 'Post', 'Shared placement preparation tips', '192.168.1.116', '2026-02-03 16:00:00'),
(10, 'Login', 'User logged in successfully', '192.168.1.110', '2026-02-04 07:15:00'),
(10, 'Post', 'Announced ICML paper acceptance', '192.168.1.110', '2026-02-04 08:00:00'),
(1, 'Logout', 'User logged out', '192.168.1.101', '2026-02-04 18:00:00');

-- ============================================================================
-- End of Sample Data
-- ============================================================================
