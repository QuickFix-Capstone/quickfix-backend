INSERT INTO service_offerings (
        service_offering_id,
        provider_id,
        title,
        description,
        category,
        price,
        pricing_type,
        rating,
        main_image_url,
        is_active,
        created_at
    )
VALUES -- =====================
    -- SP-001
    -- =====================
    (
        'SO-SP001-1',
        'SP-001',
        'Emergency Plumbing Repair',
        '24/7 plumbing repairs for leaks and bursts.',
        'PLUMBING',
        150.00,
        'FIXED',
        4.8,
        'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAjk2AT-VSnr_lGW-AiP9dFV86KPBXG0DPgQ&s',
        1,
        NOW()
    ),
    (
        'SO-SP001-2',
        'SP-001',
        'Drain Cleaning',
        'Professional drain and pipe cleaning.',
        'PLUMBING',
        90.00,
        'FIXED',
        4.7,
        'https://media.istockphoto.com/id/157376761/photo/close-up-of-drain-pipe-leaking-water.jpg?s=1024x1024&w=is&k=20&c=FZOllkZ2bD8HUjyFeTJW_ulUjg6AcT-W3aw23oyx7jE=',
        1,
        NOW()
    ),
    -- =====================
    -- SP-002
    -- =====================
    (
        'SO-SP002-1',
        'SP-002',
        'Electrical Panel Upgrade',
        'Upgrade and replace electrical panels.',
        'ELECTRICAL',
        200.00,
        'FIXED',
        4.6,
        'https://electriciansserviceteam.com/wp-content/uploads/2024/01/before-and-after-electrical-panel-upgrade.jpeg',
        1,
        NOW()
    ),
    (
        'SO-SP002-2',
        'SP-002',
        'Outlet & Switch Repair',
        'Repair faulty outlets and switches.',
        'ELECTRICAL',
        75.00,
        'FIXED',
        4.5,
        'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxm19NHZLWFxy6UmGvczjzHhrtM5IGhR_c9Q&s',
        1,
        NOW()
    ),
    -- =====================
    -- SP-003
    -- =====================
    (
        'SO-SP003-1',
        'SP-003',
        'AC Repair',
        'Fast and reliable air conditioning repair.',
        'HVAC',
        120.00,
        'HOURLY',
        4.7,
        'https://shiptons.ca/wp-content/uploads/2023/05/Air-Conditioning-Maintenance-Service.webp',
        1,
        NOW()
    ),
    (
        'SO-SP003-2',
        'SP-003',
        'Furnace Maintenance',
        'Seasonal furnace inspection and maintenance.',
        'HVAC',
        100.00,
        'FIXED',
        4.6,
        'https://www.serviceexperts.ca/wp-content/uploads/2022/12/heating-FurnaceMaintenance-SupportingGD-1-1100x825-2.webp',
        1,
        NOW()
    ),
    -- =====================
    -- SP-004
    -- =====================
    (
        'SO-SP004-1',
        'SP-004',
        'Home Deep Cleaning',
        'Eco-friendly full home deep cleaning.',
        'CLEANING',
        140.00,
        'FIXED',
        4.9,
        'https://scrubnbubbles.com/wp-content/uploads/2022/05/cleaning-service.jpeg',
        1,
        NOW()
    ),
    (
        'SO-SP004-2',
        'SP-004',
        'Office Cleaning',
        'Professional office cleaning services.',
        'CLEANING',
        60.00,
        'HOURLY',
        4.8,
        'https://contentgrid.homedepot-static.com/hdus/en_US/DTCCOMNEW/Articles/Office-Cleaning-Hero.jpg',
        1,
        NOW()
    ),
    -- =====================
    -- SP-005
    -- =====================
    (
        'SO-SP005-1',
        'SP-005',
        'General Handyman Services',
        'Repairs, installations, and small renovations.',
        'HANDYMAN',
        85.00,
        'HOURLY',
        4.5,
        'https://gillespiehandyman.com/wp-content/uploads/2020/04/c82b0e2a-fe76-11e9-93f4-0242ac110002-jpg-thumbnail_image.jpeg',
        1,
        NOW()
    ),
    (
        'SO-SP005-2',
        'SP-005',
        'Furniture Assembly',
        'Assemble furniture quickly and safely.',
        'HANDYMAN',
        70.00,
        'FIXED',
        4.4,
        'https://images.ctfassets.net/vwt5n1ljn95x/3e1hJzjKMgT039qOZua4Le/55e9a93ced05255acccd3641a46526dc/SLP_Furniture_Assembly_390x182.jpg?w=3840&q=75&fm=webp',
        1,
        NOW()
    ),
    -- =====================
    -- SP-006
    -- =====================
    (
        'SO-SP006-1',
        'SP-006',
        'Pest Inspection',
        'Full home pest inspection service.',
        'PEST_CONTROL',
        95.00,
        'FIXED',
        4.7,
        'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHNKTIKlpSHz6PAr6_BXv7yNAEX6vHRrQ9FQ&s',
        1,
        NOW()
    ),
    (
        'SO-SP006-2',
        'SP-006',
        'Rodent Removal',
        'Safe and effective rodent removal.',
        'PEST_CONTROL',
        130.00,
        'FIXED',
        4.8,
        'https://www.ontariowildliferemoval.ca/wp-content/uploads/2025/06/mice-removal-kitchener.jpg',
        1,
        NOW()
    );