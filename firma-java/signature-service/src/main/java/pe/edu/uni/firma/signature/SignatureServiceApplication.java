package pe.edu.uni.firma.signature;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

/**
 * Microservicio de firma y documentos.
 *
 * Se excluye DataSourceAutoConfiguration para evitar que Spring Boot intente
 * crear un DataSource Hikari automático. Este servicio usa JDBC explícito
 * mediante SignatureDbConnectionFactory.
 */
@SpringBootApplication(
        scanBasePackages = "pe.edu.uni.firma",
        exclude = DataSourceAutoConfiguration.class
)
public class SignatureServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(SignatureServiceApplication.class, args);
    }
}
