CREATE TABLE Users (
	userID varchar(50) not null,
	name varchar(50),
	role ENUM('applicant', 'employer', 'mentor'),
	PRIMARY KEY (userID)
)