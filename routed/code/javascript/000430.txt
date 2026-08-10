// Dependencies
const Sequelize = require('sequelize');
require('dotenv').config();

let sequelize;

// If the database is being completed live, use JAWSDB, otherwise, 
// if seeded locally, use local credentials to access MySQL Workbench
if (process.env.JAWSDB_URL) {
  sequelize = new Sequelize(process.env.JAWSDB_URL);
} else {
  sequelize = new Sequelize(
    process.env.DB_NAME,
    process.env.DB_USER,
    process.env.DB_PASSWORD,
    {
      host: 'localhost',
      dialect: 'mysql',
      port: 3306
    }
  );
}

// Export module
module.exports = sequelize;