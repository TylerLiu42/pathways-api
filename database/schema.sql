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