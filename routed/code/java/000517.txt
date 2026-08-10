package tasks;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class Pr02GetVillainsNames implements Executable {
    Connection connection;

    public Pr02GetVillainsNames(Connection connection) {
        this.connection = connection;
    }

    private void getVillainsNames() throws SQLException {
        String query =
                "SELECT v.name, COUNT(mv.minion_id) as cm FROM villains as v JOIN minions_villains as mv ON v.id = mv.villain_id" +
                        " GROUP BY mv.villain_id HAVING cm > ? ORDER BY cm DESC;";

        PreparedStatement preparedStatement =
                this.connection.prepareStatement(query);

        preparedStatement.setInt(1, 15);

        ResultSet resultSet = preparedStatement.executeQuery();

        while (resultSet.next()) {
            System.out.println(
                    String.format("%s %d", resultSet.getString("name"), resultSet.getInt("cm")));
        }
    }

    @Override
    public void execute() throws SQLException {
        this.getVillainsNames();
    }
}
