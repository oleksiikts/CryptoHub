create database College
use College
CREATE TABLE Students (
StudentID INT PRIMARY KEY AUTO_INCREMENT,
FirstName VARCHAR(50),
LastName VARCHAR(50),
BirthDate DATE
);

CREATE TABLE Courses (
CourseID INT PRIMARY KEY AUTO_INCREMENT,
CourseName VARCHAR(100),
Credits INT
);

INSERT INTO Students (FirstName, LastName, BirthDate)
VALUES
('Ivan', 'Petrov', '2001-05-12'),
('Anna', 'Kovalenko', '1999-11-15'),
('Oleg', 'Ivanov', '2000-07-30');


INSERT INTO Courses (CourseName, Credits)
VALUES
('Mathematics', 5),
('Computer Science', 4),
('History', 3);


SELECT * FROM Students;
SELECT FirstName, LastName FROM Students;

SELECT * FROM Courses WHERE Credits >= 4;

UPDATE Students
SET LastName = 'Ivanov'
WHERE StudentID = 1;

DELETE FROM Students
WHERE StudentID = 3;
