import pymysql
from shared.db import get_connection
from domain.provider_certification import ProviderCertification


class ProviderCertificationRepository:
    """
    Handles persistence for provider_certifications table
    """

    def create(self, certification: ProviderCertification) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO provider_certifications (
                        certification_id,
                        provider_id,
                        certification_s3_key,
                        certification_type,
                        verification_status,
                        uploaded_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                cursor.execute(
                    sql,
                    (
                        certification.certification_id,
                        certification.provider_id,
                        certification.certification_s3_key,
                        certification.certification_type,
                        certification.verification_status,
                        certification.uploaded_at,
                    ),
                )

            connection.commit()

        except pymysql.MySQLError:
            connection.rollback()
            raise

        finally:
            connection.close()

    # --------------------------------------------------

    def get_by_id(self, certification_id: str) -> dict | None:
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM provider_certifications
                    WHERE certification_id = %s
                """
                cursor.execute(sql, (certification_id,))
                return cursor.fetchone()

        finally:
            connection.close()

    # --------------------------------------------------

    def list_by_provider(self, provider_id: str) -> list[dict]:
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM provider_certifications
                    WHERE provider_id = %s
                    ORDER BY uploaded_at DESC
                """
                cursor.execute(sql, (provider_id,))
                return cursor.fetchall()

        finally:
            connection.close()

    # --------------------------------------------------

    def update_status(self, certification_id: str, status: str) -> None:
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE provider_certifications
                    SET verification_status = %s
                    WHERE certification_id = %s
                """
                cursor.execute(sql, (status, certification_id))

            connection.commit()

        except pymysql.MySQLError:
            connection.rollback()
            raise

        finally:
            connection.close()
