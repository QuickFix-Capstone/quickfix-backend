USE quickfix;
-- Insert Realistic Customers
INSERT INTO customers (
        first_name,
        last_name,
        email,
        phone,
        address,
        city,
        state,
        postal_code
    )
VALUES (
        'Michael',
        'Andrews',
        'm.andrews91@gmail.com',
        '416-555-1020',
        '14 Creekside Dr',
        'Toronto',
        'ON',
        'M4C 1A1'
    ),
    (
        'Sophia',
        'Patel',
        'sophia.patel23@yahoo.com',
        '647-555-2881',
        '221 Mapleview Cres',
        'Mississauga',
        'ON',
        'L5M 4Y8'
    ),
    (
        'Daniel',
        'Nguyen',
        'd.nguyen88@hotmail.com',
        '905-555-5523',
        '88 Riverbank Rd',
        'Brampton',
        'ON',
        'L6P 2S4'
    ),
    (
        'Emily',
        'Bennett',
        'e.bennett@gmail.com',
        '289-555-4421',
        '301 Lakeshore Rd',
        'Oakville',
        'ON',
        'L6J 3A1'
    );