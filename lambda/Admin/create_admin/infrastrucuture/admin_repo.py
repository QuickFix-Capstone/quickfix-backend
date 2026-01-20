from shared.db import get_connection
import pymysql
from datetime import datetime


class AdminRepository:
    """
    Handles persistence of Admin entities.
    """

    # =========================
    # CREATE
    # =========================
    def create(self, admin) -> None:
        """
        Creates a new admin record.
        """
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO admins (
                        admin_id,
                        cognito_sub,
                        name,
                        email,
                        is_active,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(sql, (
                    admin.admin_id,
                    admin.cognito_sub,
                    admin.name,
                    admin.email,
                    admin.is_active,
                    admin.created_at,
                    admin.updated_at,
                ))

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to create Admin: {e}")

        finally:
            connection.close()

    # =========================
    # READ
    # =========================
    def get_by_cognito_sub(self, cognito_sub):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM admins
                    WHERE cognito_sub = %s
                """
                cursor.execute(sql, (cognito_sub,))
                return cursor.fetchone()

        finally:
            connection.close()

    def get_by_email(self, email):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM admins
                    WHERE email = %s
                """
                cursor.execute(sql, (email,))
                return cursor.fetchone()

        finally:
            connection.close()

    def get_all(self):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM admins
                    ORDER BY created_at DESC
                """
                cursor.execute(sql)
                return cursor.fetchall()

        finally:
            connection.close()

    # =========================
    # ADMIN MANAGEMENT
    # =========================
    def update_active_status(self, admin_id, is_active: bool):
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE admins
                    SET
                        is_active = %s,
                        updated_at = %s
                    WHERE admin_id = %s
                """
                cursor.execute(sql, (
                    is_active,
                    datetime.utcnow(),
                    admin_id,
                ))

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to update Admin status: {e}")

        finally:
            connection.close()
