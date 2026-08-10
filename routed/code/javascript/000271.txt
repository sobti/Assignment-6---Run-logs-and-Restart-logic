let controller = require("../controller/queryController");
let express = require("express");
let databaseController = require("../controller/databaseController");

let routes = express.Router();

//Read
routes.post("/", databaseController.conn, controller.runQuery);

module.exports = routes;
