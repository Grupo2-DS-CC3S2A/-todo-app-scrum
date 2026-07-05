package pe.edu.uni.firma.signature.container;

/**
 * Certificado lógico embebido dentro del contenedor firmado.
 * Para una PKI real se reemplazaría por un certificado X.509/PAdES.
 */
public record EmbeddedCertificate(
        String type,
        String subjectDni,
        String subjectName,
        String subjectUbigeo,
        String publicKeyAlgorithm,
        String publicKeyBase64,
        String issuer,
        String serialNumber,
        String issuedAt,
        String expiresAt
) {}
