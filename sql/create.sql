create database bookMG_db;

create table books (
    id int PRIMARY KEY auto_increment,
    title varchar(50),
    author varchar(20),
    ISBN varchar(13),
    imageLink varchar(120),
    des text,
    numbers int,
);

create table users (
    id int primary key,
    name varchar(20),
    hashed_pw varchar(128),
    salt varchar(8)
);

create table admins (
    id int primary key auto_increment,
    user_id varchar(50),
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

-- insert into admins (user_id,hashed_pw,salt) value (
--     "otsubo@morijyobi.ac.jp",
--     "eb1a5026ff2b2a254a711446610b703adf1deb96233dce7fec6839cbbc35d298355ce4a17291530595fa331e1734e773d4aebf8f7c3deb699070c9821ff1c4b9",
--     "morijobi"
-- )