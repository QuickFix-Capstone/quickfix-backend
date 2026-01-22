from domain.ServiceProvider import ServiceProvider
from shared.db import get_connection
import pymysql
from datetime import datetime


class ServiceProviderRepository:
    """
    Handles persistence of ServiceProvider entities.
    Role-agnostic (used by Admin, Service Provider, Customer flows).
    """

    # =====================================================
    # CREATE
    # =====================================================
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
                        phone_number,
                        business_name,
                        address_line,
                        city,
                        province,
                        postal_code,
                        bio,
                        certification_url,
                        verification_status,
                        is_active,
                        created_at,
                        updated_at,
                        total_rating_points,
                        total_review_count,
                        average_rating
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """

                cursor.execute(sql, (
                    provider.provider_id,
                    provider.cognito_sub,
                    provider.name,
                    provider.email,
                    provider.phone_number,
                    provider.business_name,
                    provider.address_line,
                    provider.city,
                    provider.province,
                    provider.postal_code,
                    provider.bio,
                    provider.certification_url,
                    provider.verification_status,
                    provider.is_active,
                    provider.created_at,
                    provider.updated_at,
                    provider.total_rating_points,
                    provider.total_review_count,
                    provider.average_rating,
                ))

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to create ServiceProvider: {e}")

        finally:
            connection.close()

    # =====================================================
    # READ (Single)
    # =====================================================
    def get_by_provider_id(self, provider_id):
        return self._get_single("provider_id = %s", (provider_id,))

    def get_by_cognito_sub(self, cognito_sub):
        return self._get_single("cognito_sub = %s", (cognito_sub,))

    def get_by_email(self, email):
        return self._get_single("email = %s", (email,))

    # =====================================================
    # READ (Admin Lists)
    # =====================================================
    def get_all(self, limit=50, offset=0):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT *
                    FROM service_providers
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(sql, (limit, offset))
                return cursor.fetchall()

        finally:
            connection.close()

    # =====================================================
    # SEARCH (Admin)
    # =====================================================
    def search(self, filters: dict):
        """
        Supported filters:
        provider_id, email, phone_number, business_name,
        city, province, verification_status, is_active
        """
        connection = get_connection()

        conditions = []
        values = []

        allowed_fields = {
            "provider_id",
            "email",
            "phone_number",
            "business_name",
            "city",
            "province",
            "verification_status",
            "is_active",
        }

        for field, value in filters.items():
            if field in allowed_fields:
                conditions.append(f"{field} = %s")
                values.append(value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
            SELECT *
            FROM service_providers
            WHERE {where_clause}
            ORDER BY created_at DESC
        """

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, tuple(values))
                return cursor.fetchall()

        finally:
            connection.close()

    # =====================================================
    # ADMIN – VERIFICATION
    # =====================================================
    def approve(self, provider_id):
        self._update_fields(provider_id, {
            "verification_status": "APPROVED",
            "is_active": True,
            "updated_at": datetime.utcnow(),
        })

    def reject(self, provider_id):
        self._update_fields(provider_id, {
            "verification_status": "REJECTED",
            "is_active": False,
            "updated_at": datetime.utcnow(),
        })

    def reset_verification(self, provider_id):
        self._update_fields(provider_id, {
            "verification_status": "PENDING",
            "is_active": False,
            "updated_at": datetime.utcnow(),
        })

    # =====================================================
    # ADMIN – MODERATION
    # =====================================================
    def suspend(self, provider_id):
        self._update_fields(provider_id, {
            "is_active": False,
            "updated_at": datetime.utcnow(),
        })

    def reactivate(self, provider_id):
        self._update_fields(provider_id, {
            "is_active": True,
            "updated_at": datetime.utcnow(),
        })

    def get_unverified(self, limit=50, offset=0):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT *
                FROM service_providers
                WHERE verification_status = 'PENDING'
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (limit, offset))
            return cursor.fetchall()

        finally:
            connection.close()

    # =====================================================
    # PROFILE UPDATE
    # =====================================================
    def update_profile(self, provider_id, updates: dict):
        allowed_fields = {
            "name",
            "phone_number",
            "business_name",
            "address_line",
            "city",
            "province",
            "postal_code",
            "bio",
        }

        clean_updates = {
            k: v for k, v in updates.items() if k in allowed_fields
        }

        if not clean_updates:
            return

        clean_updates["updated_at"] = datetime.utcnow()
        self._update_fields(provider_id, clean_updates)

    # =====================================================
    # RATINGS
    # =====================================================
    def update_rating_aggregate(self, provider_id, rating_value: int):
        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE service_providers
                    SET
                        total_rating_points = total_rating_points + %s,
                        total_review_count = total_review_count + 1,
                        average_rating =
                            (total_rating_points + %s) / (total_review_count + 1),
                        updated_at = %s
                    WHERE provider_id = %s
                """
                cursor.execute(sql, (
                    rating_value,
                    rating_value,
                    datetime.utcnow(),
                    provider_id,
                ))

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to update rating: {e}")

        finally:
            connection.close()

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================
    def _get_single(self, condition, values):
        connection = get_connection()

        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = f"""
                    SELECT *
                    FROM service_providers
                    WHERE {condition}
                """
                cursor.execute(sql, values)
                return cursor.fetchone()

        finally:
            connection.close()

    def _update_fields(self, provider_id, fields: dict):
        connection = get_connection()

        set_clause = ", ".join(f"{k} = %s" for k in fields.keys())
        values = list(fields.values()) + [provider_id]

        try:
            with connection.cursor() as cursor:
                sql = f"""
                    UPDATE service_providers
                    SET {set_clause}
                    WHERE provider_id = %s
                """
                cursor.execute(sql, values)

            connection.commit()

        except pymysql.MySQLError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to update ServiceProvider: {e}")

        finally:
            connection.close()
