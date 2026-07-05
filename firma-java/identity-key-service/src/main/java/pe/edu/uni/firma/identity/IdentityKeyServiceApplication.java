package pe.edu.uni.firma.identity;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

/**
 * Microservicio de identidad y llaves.
 *
 * Se excluye DataSourceAutoConfiguration porque este servicio maneja dos bases H2
 * independientes mediante JDBC explícito:
 *   - BD1 privada: private-db
 *   - BD2 pública: public-db
 *
 * Esta decisión evita que Spring Boot intente crear un único DataSource automático
 * con HikariCP y elimina el error: "jdbcUrl is required with driverClassName".
 */
@SpringBootApplication(
        scanBasePackages = "pe.edu.uni.firma",
        exclude = DataSourceAutoConfiguration.class
)
public class IdentityKeyServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(IdentityKeyServiceApplication.class, args);
    }
}
