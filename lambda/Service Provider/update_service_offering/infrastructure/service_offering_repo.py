from domain.service_offering import ServiceOffering
from shared.db import get_connection
import pymysql


class ServiceOfferingRepository:
    """
    Handles persistence of ServiceOffering entities
    """

    # ==============================
    # CREATE
    # ==============================
    def create(self, offering: ServiceOffering) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(
                    sql,
                    (
                        offering.service_offering_id,
                        offering.provider_id,
                        offering.title,
                        offering.description,
                        offering.category.value,
                        offering.price,
                        offering.pricing_type.value,
                        offering.rating,
                        offering.main_image_url,
                        offering.is_active,
                        offering.created_at,
                    ),
                )

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to create Service Offering: {e}")

        finally:
            connection.close()

    # ==============================
    # READ (for ownership checks)
    # ==============================
    def get_by_id(self, service_offering_id: str) -> dict | None:
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM service_offerings
                    WHERE service_offering_id = %s
                    LIMIT 1
                """
                cursor.execute(sql, (service_offering_id,))
                return cursor.fetchone()

        except pymysql.MySQLError as e:
            raise RuntimeError(f"Failed to fetch Service Offering: {e}")

        finally:
            connection.close()

    # ==============================
    # UPDATE
    # ==============================
    def update(self, offering: ServiceOffering) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE service_offerings
                    SET
                        title = %s,
                        description = %s,
                        category = %s,
                        price = %s,
                        pricing_type = %s,
                        main_image_url = %s,
                        is_active = %s
                    WHERE service_offering_id = %s
                """

                cursor.execute(
                    sql,
                    (
                        offering.title,
                        offering.description,
                        offering.category.value,
                        offering.price,
                        offering.pricing_type.value,
                        offering.main_image_url,
                        offering.is_active,
                        offering.service_offering_id,
                    ),
                )

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to update Service Offering: {e}")

        finally:
            connection.close()

    # ==============================
    # SOFT DELETE (recommended)
    # ==============================
    def soft_delete(self, service_offering_id: str) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE service_offerings
                    SET is_active = 0
                    WHERE service_offering_id = %s
                """
                cursor.execute(sql, (service_offering_id,))

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to delete Service Offering: {e}")

        finally:
            connection.close()

    # ==============================
    # HARD DELETE (optional)
    # ==============================
    def hard_delete(self, service_offering_id: str) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    DELETE FROM service_offerings
                    WHERE service_offering_id = %s
                """
                cursor.execute(sql, (service_offering_id,))

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            r
