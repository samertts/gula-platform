const { Client } = require("pg");

const client = new Client({
  user: "postgres",
  host: "localhost",
  database: "nhop_db",
  password: "123456",
  port: 5432,
});

client.connect()
  .then(() => console.log("Database connected ✅"))
  .catch(err => console.error("DB connection error", err));

module.exports = client;
