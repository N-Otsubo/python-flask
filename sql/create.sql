create database bookMG_db;

create table books (
    id int PRIMARY KEY auto_increment,
    title varchar(50),
    author varchar(20),
    ISBN varchar(13),
    imageLink varchar(120),
    des text
);


create table users (
    id int primary key,
    name varchar(20),
    hashed_pw varchar(128),
    salt varchar(8)
);

create table lendings (
    book_id int,
    user_id int,
    loan_date date,
    primary key (book_id, user_id),
    foreign key (book_id) references books(id),
    foreign key (user_id) references users(id)
);
