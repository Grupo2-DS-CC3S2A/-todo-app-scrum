package pe.edu.uni.firma.identity.db;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Factory JDBC para Supabase/PostgreSQL local.
 *
 * En la versión anterior se usaban dos BD H2:
 * - private-db
 * - public-db
 *
 * En esta integración se usa una sola instancia PostgreSQL de Supabase local,
 * separada lógicamente en dos esquemas:
 *
 * - public.citizens
 * - firma_publica.citizens
 */
@Component
public class IdentityDbConnectionFactory {

    private final String jdbcUrl;
    private final String username;
    private final String password;

    public IdentityDbConnectionFactory(
            @Value("${identity.supabase-jdbc-url}") String jdbcUrl,
            @Value("${identity.supabase-db-user}") String username,
            @Value("${identity.supabase-db-password}") String password
    ) {
        this.jdbcUrl = jdbcUrl;
        this.username = username;
        this.password = password;

        System.out.println("[identity-key-service] Supabase JDBC = " + this.jdbcUrl);
    }

    public Connection privateConnection() throws SQLException {
        return DriverManager.getConnection(jdbcUrl, username, password);
    }

    public Connection publicConnection() throws SQLException {
        return DriverManager.getConnection(jdbcUrl, username, password);
    }
}