package pe.edu.uni.firma.identity.controller;

import io.swagger.v3.oas.annotations.Operation;

import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import pe.edu.uni.firma.identity.dto.CitizenPrivateDto;
import pe.edu.uni.firma.identity.dto.CitizenPublicDto;
import pe.edu.uni.firma.identity.service.IdentityKeyService;

@RestController
@RequestMapping("/api/personas")
public class IdentityController {

    private final IdentityKeyService service;
    private final String internalToken;

    public IdentityController(
            IdentityKeyService service,
            @Value("${app.security.internal-token}") String internalToken
    ) {
        this.service = service;
        this.internalToken = internalToken;
    }

    @Operation(summary = "Lista ciudadanos públicos con llave pública")
    @GetMapping
    public List<CitizenPublicDto> list() {
        return service.listPublicCitizens();
    }

    @Operation(summary = "Obtiene datos públicos del ciudadano por DNI")
    @GetMapping("/{dni}")
    public CitizenPublicDto findPublic(@PathVariable("dni") String dni) {
        return service.findPublicByDni(dni);
    }

    @Operation(summary = "Obtiene la llave pública para verificación")
    @GetMapping("/{dni}/public-key")
    public CitizenPublicDto findPublicKey(@PathVariable("dni") String dni) {
        return service.findPublicByDni(dni);
    }

    @Operation(summary = "Obtiene la llave privada. Endpoint interno usado por signature-service")
    @GetMapping("/{dni}/private-key")
    public CitizenPrivateDto findPrivateKey(
            @PathVariable("dni") String dni,
            @RequestHeader(value = "X-Internal-Token", required = false) String token
    ) {
        validarToken(token);
        return service.findPrivateByDni(dni);
    }

    @Operation(summary = "Genera llaves RSA una sola vez para todos los ciudadanos")
    @PostMapping("/seed/once")
    public SeedResponse seedOnce(
            @RequestHeader(value = "X-Internal-Token", required = false) String token
    ) {
        validarToken(token);

        try {
            int total = service.seedKeysOnce();
            return new SeedResponse("Llaves RSA generadas correctamente.", total);
        } catch (IllegalStateException ex) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, ex.getMessage());
        }
    }

    private void validarToken(String token) {
        if (!internalToken.equals(token)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Token interno inválido.");
        }
    }

    public record SeedResponse(String message, int totalKeys) {
    }
}