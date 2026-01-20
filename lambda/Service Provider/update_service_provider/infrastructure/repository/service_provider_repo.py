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
                        created_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                    ),
                )

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to create ServiceProvider: {e}")

        finally:
            connection.close()

    # ==============================
    # ✅ NEW: GET PROVIDER BY COGNITO SUB
    # ==============================
    def get_by_cognito_sub(self, cognito_sub: str):
        """
        Returns a service provider record by Cognito sub.
        Used for role-based authorization.
        """
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM service_providers
                    WHERE cognito_sub = %s
                    LIMIT 1
                """
                cursor.execute(sql, (cognito_sub,))
                return cursor.fetchone()

        except pymysql.MySQLError as e:
            raise RuntimeError(f"Failed to fetch ServiceProvider by cognito_sub: {e}")

        finally:
            connection.close()

    def update(self, provider: ServiceProvider) -> None:
    """
    Updates an existing ServiceProvider profile.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                UPDATE service_providers
                SET
                    name = %s,
                    business_name = %s,
                    address_line = %s,
                    city = %s,
                    province = %s,
                    postal_code = %s,
                    bio = %s,
                    phone_number = %s,
                    updated_at = %s
                WHERE provider_id = %s
            """

            cursor.execute(
                sql,
                (
                    provider.name,
                    provider.business_name,
                    provider.address_line,
                    provider.city,
                    provider.province,
                    provider.postal_code,
                    provider.bio,
                    provider.phone_number,
                    provider.updated_at,
                    provider.provider_id,
                ),
            )

        connection.commit()

    except pymysql.MySQLError as e:
        connection.rollback()
        raise RuntimeError(f"Failed to update ServiceProvider: {e}")

    finally:
        connection.close()

