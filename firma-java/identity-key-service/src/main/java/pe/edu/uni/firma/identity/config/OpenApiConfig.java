package pe.edu.uni.firma.identity.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {
    @Bean
    OpenAPI openAPI() {
        return new OpenAPI().info(new Info()
                .title("UNI Identity Key Service")
                .version("1.0.0")
                .description("Microservicio que administra base privada y base pública de ciudadanos y llaves RSA."));
    }
}
