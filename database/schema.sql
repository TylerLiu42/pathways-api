CREATE TABLE Users (
	userID varchar(50) not null,
	name varchar(50),
	role ENUM('applicant', 'employer', 'mentor'),
	PRIMARY KEY (userID)
)

CREATE TABLE Employer (
	userID varchar(50) not null,
	company varchar(100),
	PRIMARY KEY (userID),
	FOREIGN KEY (userID) references Users(userID)
)

CREATE TABLE ForumPost (
	postID varchar(100) not null,
	topic ENUM('HTML', 'CSS', 'Java', 'Machine Learning', 'API', 'Artificial Intelligence', 'Python'),
	score int,
	author varchar(50),
	title varchar(1000),
	date_created datetime,
	content varchar(10000),
	PRIMARY KEY (postID),
	FOREIGN KEY (author) references Users(userID)
)

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
)

CREATE TABLE PostRating (
	postID varchar(100) not null,
	userID varchar(100) not null,
	rating ENUM('up', 'down'),
	PRIMARY KEY (postID, userID),
	FOREIGN KEY (postID) references ForumPost(postID),
	FOREIGN KEY (userID) references Users(userID)
)

CREATE TABLE ReplyRating (
	replyID varchar(100) not null,
	userID varchar(100) not null,
	rating ENUM('up', 'down'),
	PRIMARY KEY (replyID, userID),
	FOREIGN KEY (replyID) references ForumReply(replyID),
	FOREIGN KEY (userID) references Users(userID)
)
