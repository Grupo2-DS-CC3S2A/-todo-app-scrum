package pe.edu.uni.firma.signature.db;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Factory JDBC directo para BD3: documentos firmados y auditoría.
 * No usa HikariCP ni DataSource automático.
 */
@Component
public class SignatureDbConnectionFactory {
    private static final String DEFAULT_SIGNED_DB_URL = "jdbc:h2:file:./data/signed-documents-db;AUTO_SERVER=FALSE";

    private final String signedDbUrl;

    public SignatureDbConnectionFactory(@Value("${signature.signed-db-url:}") String signedDbUrlProperty) {
        this.signedDbUrl = resolve("SIGNED_DB_URL", signedDbUrlProperty, DEFAULT_SIGNED_DB_URL);
        loadH2Driver();
        System.out.println("[signature-service] BD3 documentos firmados = " + this.signedDbUrl);
    }

    private static String resolve(String envName, String propertyValue, String defaultValue) {
        String envValue = System.getenv(envName);
        if (envValue != null && !envValue.isBlank()) {
            return envValue.trim();
        }
        if (propertyValue != null && !propertyValue.isBlank()) {
            return propertyValue.trim();
        }
        return defaultValue;
    }

    private static void loadH2Driver() {
        try {
            Class.forName("org.h2.Driver");
        } catch (ClassNotFoundException ex) {
            throw new IllegalStateException("No se encontró el driver org.h2.Driver", ex);
        }
    }

    public Connection connection() throws SQLException {
        return DriverManager.getConnection(signedDbUrl, "sa", "");
    }
}
