CREATE TABLE Users (
	userID varchar(50) not null,
	name varchar(50),
	role ENUM('applicant', 'employer', 'mentor'),
	PRIMARY KEY (userID)
);

CREATE TABLE Employer (
	userID varchar(50) not null,
	company varchar(100),
	PRIMARY KEY (userID),
	FOREIGN KEY (userID) references Users(userID)
);

CREATE TABLE ForumPost (
	postID varchar(100) not null,
	topic ENUM('html', 'css', 'java', 'ml', 'api', 'ai', 'python'),
	score int,
	author varchar(50),
	title varchar(1000),
	date_created datetime,
	content varchar(10000),
	PRIMARY KEY (postID),
	FOREIGN KEY (author) references Users(userID)
);

CREATE TABLE ForumReply (
	replyID varchar(100) not null,
	postID varchar(100),
	author varchar(100),
	score int,
	date_created datetime,
	content varchar(10000),
	PRIMARY KEY (replyID),
	FOREIGN KEY (postID) references ForumPost(postID),
	FOREIGN KEY (author) references Users(userID)
);

CREATE TABLE PostRating (
	postID varchar(100) not null,
	userID varchar(100) not null,
	rating ENUM('up', 'down'),
	PRIMARY KEY (postID, userID),
	FOREIGN KEY (postID) references ForumPost(postID),
	FOREIGN KEY (userID) references Users(userID)
);

CREATE TABLE ReplyRating (
	replyID varchar(100) not null,
	userID varchar(100) not null,
	rating ENUM('up', 'down'),
	PRIMARY KEY (replyID, userID),
	FOREIGN KEY (replyID) references ForumReply(replyID),
	FOREIGN KEY (userID) references Users(userID)
);

CREATE TABLE JobPost (
    jobID varchar(100) not null,
    userID varchar(100) not null,
    title varchar(1000),
    description varchar(1000),
    content varchar(8000),
    tags varchar(1000),
    remote boolean,
    address varchar(1000),
    external_link varchar(1000),
    expiry_date datetime,
    date_created datetime,
    company varchar(100),
    PRIMARY KEY (jobID),
    FOREIGN KEY (userID) references Users(userID)
);

CREATE TABLE AppliedJob (
    jobID varchar(100) not null,
    userID varchar(100) not null,
    date_applied datetime,
    interview_selected boolean,
    resume mediumblob,
    resume_extension varchar(10),
    PRIMARY KEY (jobID, userID),
    FOREIGN KEY (userID) references Users(userID),
    FOREIGN KEY (jobID) references JobPost(jobID)
);

CREATE TABLE JobReview (
	reviewID varchar(100) not null,
	jobID varchar(100) not null,
	userID varchar(100),
	content varchar(10000),
	date_created datetime,
	sentiment_score float,
	flagged boolean,
	stars ENUM('1', '2', '3', '4', '5'),
	PRIMARY KEY (reviewID),
	FOREIGN KEY (jobID) references JobPost(jobID),
	FOREIGN KEY (userID) references Users(userID)
);

CREATE TABLE Course(
	courseID varchar(100) not null,
	courseAuthorId varchar(100),
	courseTitle varchar(1000),
	PRIMARY KEY (courseID),
	FOREIGN KEY (courseAuthorID) references Users(userID)
);

CREATE TABLE Quiz(
	questionID varchar(100) not null,
	quizID int not null,
	courseID varchar(100),
	answer varchar(1000),
	question_string varchar(1000),
	PRIMARY KEY (questionID, quizID, courseID),
	FOREIGN KEY (courseID) references Course(courseID)
);

CREATE TABLE QuestionOption(
	questionID varchar(100) not null,
	optionID int not null,
	courseID varchar(100) not null,
	quizID int not null,
	option_string varchar(1000),
	PRIMARY KEY (questionID, optionID, courseID, quizID),
	FOREIGN KEY (questionID, quizID, courseID) references Quiz(questionID, quizID, courseID)
);

CREATE TABLE CourseUser(
	userID varchar(100) not null,
	courseID varchar(100) not null,
	quizID int not null,
	completed boolean,
	grade decimal(3,2),
	PRIMARY KEY (userID, courseID, quizID),
	FOREIGN KEY (userID) references Users(userID),
	FOREIGN KEY (courseID) references Course(courseID),
	CONSTRAINT grade_check_min CHECK (grade >= 0),
	CONSTRAINT grade_check_max CHECK (grade <= 1)
);
