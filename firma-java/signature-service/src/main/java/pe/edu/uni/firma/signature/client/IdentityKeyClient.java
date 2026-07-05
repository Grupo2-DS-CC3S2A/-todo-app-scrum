package pe.edu.uni.firma.signature.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;
import pe.edu.uni.firma.signature.dto.CitizenPublicDto;

/** Patrón Proxy: encapsula la comunicación HTTP con identity-key-service. */
@Component
public class IdentityKeyClient {
    private final RestClient restClient;
    private final String token;

    public IdentityKeyClient(@Value("${app.identity-service.base-url}") String baseUrl,
                             @Value("${app.identity-service.internal-token}") String token) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
        this.token = token;
    }

    public CitizenPrivateDto getPrivateKey(String dni) {
        return restClient.get()
                .uri("/api/personas/{dni}/private-key", dni)
                .header("X-Internal-Token", token)
                .retrieve()
                .body(CitizenPrivateDto.class);
    }

    public CitizenPublicDto getPublicKey(String dni) {
        return restClient.get()
                .uri("/api/personas/{dni}/public-key", dni)
                .retrieve()
                .body(CitizenPublicDto.class);
    }
}
