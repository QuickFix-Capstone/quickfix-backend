from domain.service_provider import ServiceProvider
from shared.db import get_connection
import pymysql


class ServiceProviderRepository:
    """
    Handles persistence of ServiceProvider entities
    """

    def create(self, provider: ServiceProvider) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO service_providers (
                        provider_id,
                        cognito_sub,
                        name,
                        email,
                        address_line,
                        city,
                        province,
                        postal_code,
                        bio,
                        rating,
                        certification_url,
                        verification_status,
                        is_active,
                        created_at,
                        business_name
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """

                cursor.execute(
                    sql,
                    (
                        provider.provider_id,
                        provider.cognito_sub,
                        provider.name,
                        provider.email,
                        provider.address_line,
                        provider.city,
                        provider.province,
                        provider.postal_code,
                        provider.bio,
                        provider.rating,
                        provider.certification_url,
                        provider.verification_status.value,
                        provider.is_active,
                        provider.created_at,
                        provider.business_name,
                    ),
                )

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to create ServiceProvider: {e}")

        finally:
            connection.close()

    def get_by_provider_id(self, provider_id):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT
                        provider_id,
                        cognito_sub,
                        name,
                        email,
                        business_name,
                        address_line,
                        city,
                        province,
                        postal_code,
                        bio,
                        rating,
                        certification_url,
                        verification_status,
                        is_active,
                        created_at
                    FROM service_providers
                    WHERE provider_id = %s
                """

                cursor.execute(sql, (provider_id,))
                return cursor.fetchone()

        finally:
            connection.close()

    def get_by_cognito_sub(self, cognito_sub):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT
                        provider_id,
                        cognito_sub,
                        name,
                        email,
                        business_name,
                        address_line,
                        city,
                        province,
                        postal_code,
                        bio,
                        rating,
                        certification_url,
                        verification_status,
                        is_active,
                        created_at
                    FROM service_providers
                    WHERE cognito_sub = %s
                """

                cursor.execute(sql, (cognito_sub,))
                return cursor.fetchone()

        finally:
            connection.close()
