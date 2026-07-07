package pe.edu.uni.firma.signature.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {
    @Bean
    OpenAPI openAPI() {
        return new OpenAPI().info(new Info()
                .title("UNI Signature Service")
                .version("1.0.0")
                .description("Microservicio de firma, almacenamiento de documentos firmados y auditoría."));
    }
}
