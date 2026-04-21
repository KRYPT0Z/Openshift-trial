from app import app
from models import db, Product

with app.app_context():
    db.drop_all()
    db.create_all()

    products = [
        Product(
            name="Emotional Baggage",
            description="Heavy duty, distressed leather luggage designed to be carried around for years. Features a reinforced handle for complex situations and a built in lock to keep everyone out",
            price=1450.00,
            image="emotional_baggage.jpg",
            impact=250.5
        ),
        Product(
            name="Can of Worms",
            description="A beautifully tinned selection of messy, complicated situations. Best opened at family dinners or unprompted corporate strategy meetings. Once opened, cannot be resealed",
            price=18.50,
            image="can_of_worms.jpg",
            impact=999.9
        ),
        Product(
            name="Clean Slate",
            description="A completely blank, untreated slab of metamorphic rock. Visually wipes away past mistakes, burnt bridges and poor decisions. Requires heavy daily maintenance",
            price=120.00,
            image="clean_slate.jpg",
            impact=0.0
        ),
        Product(
            name="Borrowed Time",
            description="Exactly 45 extra minutes, encased in a sleek, hand blown hourglass. Must be paid back with interest. Perfect for impossibly tight deadlines",
            price=500.00,
            image="borrowed_time.jpg",
            impact=60.0
        ),
        Product(
            name="The Last Straw",
            description="The final, definitive breaking point. A single, elegantly crafted glass drinking straw that is mathematically guaranteed to shatter the exact moment your tolerance runs out",
            price=8.99,
            image="last_straw.jpg",
            impact=1.0
        )
    ]

    db.session.add_all(products)
    db.session.commit()

    print("Database seeded successfully")