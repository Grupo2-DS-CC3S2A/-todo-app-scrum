package pe.edu.uni.firma.identity.config;

/**
 * Esta clase se mantiene solo para documentar una decisión de diseño.
 *
 * Versión anterior: usaba dos DataSource/HikariCP y fallaba en Docker con:
 * "jdbcUrl is required with driverClassName".
 *
 * Versión actual: identity-key-service usa JDBC explícito mediante
 * IdentityDbConnectionFactory. No se declara ningún DataSource en este servicio.
 */
final class DataSourceConfig {
    private DataSourceConfig() {
    }
}
