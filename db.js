import mysql from 'mysql2';
import dotenv from 'dotenv';
dotenv.config();

const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// Helper to use async/await or validation if needed, 
// though mysql2 works well with callbacks as used in the snippet.
// We export the pool directly or a wrapper. 
// The snippet uses db.query(sql, params, callback).
// mysql2 pool.query matches this signature.

export default pool;
