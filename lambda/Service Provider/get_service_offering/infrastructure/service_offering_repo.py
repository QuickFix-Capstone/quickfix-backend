from domain.service_offering import ServiceOffering
from shared.db import get_connection
import pymysql


class ServiceOfferingRepository:
    """
    Handles persistence of ServiceOffering entities
    """

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

    def get_by_provider_id(self, provider_id: str):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT
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
                    FROM service_offerings
                    WHERE provider_id = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(sql, (provider_id,))
                return cursor.fetchall()

        except pymysql.MySQLError as e:
            raise RuntimeError(f"Failed to fetch offerings: {e}")

        finally:
            connection.close()

    def get_all(self):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT
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
                    FROM service_offerings
                    ORDER BY created_at DESC
                """
                cursor.execute(sql)
                return cursor.fetchall()

        except pymysql.MySQLError as e:
            raise RuntimeError(f"Failed to fetch all service offerings: {e}")

        finally:
            connection.close()

