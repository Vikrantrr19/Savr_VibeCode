import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import iceberg, models, schemas


class IcebergOrderE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        models.Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        models.Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.db = self.TestingSessionLocal()

    def tearDown(self):
        self.db.close()

    def test_create_and_progress_iceberg_order(self):
        payload = schemas.IcebergOrderCreate(
            user_id="swe_trader_01",
            instrument="NIFTY 03JUL25700CE",
            exchange="NFO",
            side="BUY",
            product="NRML",
            order_type="LIMIT",
            limit_price=59.70,
            total_quantity=7500,
            lot_size=75,
            slices=10,
        )

        order = iceberg.create_iceberg_order(payload, self.db)
        self.assertEqual(order.status, "ACTIVE")
        self.assertEqual(order.revealed_quantity_per_slice, 750)
        self.assertEqual(len(order.legs), 10)
        self.assertEqual(order.legs[0].status, "OPEN")

        for _ in range(10):
            order = iceberg.fill_current_slice(order.id, self.db)

        self.assertEqual(order.status, "COMPLETED")
        self.assertEqual(order.filled_quantity, 7500)
        self.assertTrue(all(leg.status == "FILLED" for leg in order.legs))

        with self.assertRaises(Exception):
            iceberg.fill_current_slice(order.id, self.db)

    def test_rejects_invalid_slice_count_for_lot_structure(self):
        payload = schemas.IcebergOrderCreate(
            user_id="swe_trader_02",
            instrument="NIFTY 03JUL25700CE",
            side="BUY",
            order_type="LIMIT",
            limit_price=59.70,
            total_quantity=300,
            lot_size=75,
            slices=6,
        )

        with self.assertRaises(Exception):
            iceberg.create_iceberg_order(payload, self.db)


if __name__ == "__main__":
    unittest.main()
