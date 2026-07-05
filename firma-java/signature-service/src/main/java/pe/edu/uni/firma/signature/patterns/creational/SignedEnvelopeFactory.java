package pe.edu.uni.firma.signature.patterns.creational;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.UUID;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.signature.container.EmbeddedCertificate;
import pe.edu.uni.firma.signature.container.SignatureMetadata;
import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;
import pe.edu.uni.firma.signature.dto.CitizenPublicDto;
import pe.edu.uni.firma.signature.patterns.behavioral.PreparedDocument;

/** Patrón Factory Method: crea la metadata criptográfica embebida del contenedor firmado. */
@Component
public class SignedEnvelopeFactory {
    public static final String ENVELOPE_VERSION = "UNI-SIGNED-1.0";
    public static final String ISSUER = "UNI Demo Certification Authority";

    public SignatureMetadata createMetadata(PreparedDocument prepared,
                                            CitizenPrivateDto signer,
                                            CitizenPublicDto publicIdentity,
                                            String hashHex,
                                            String signatureBase64,
                                            String algorithm,
                                            Instant signedAt) {
        EmbeddedCertificate certificate = new EmbeddedCertificate(
                "UNI-DEMO-CERTIFICATE",
                signer.dni(),
                signer.apellidosNombres(),
                signer.ubigeo(),
                "RSA",
                publicIdentity.publicKeyBase64(),
                ISSUER,
                UUID.nameUUIDFromBytes((signer.dni() + publicIdentity.publicKeyBase64()).getBytes()).toString(),
                signedAt.toString(),
                signedAt.plus(365, ChronoUnit.DAYS).toString()
        );
        return new SignatureMetadata(
                ENVELOPE_VERSION,
                prepared.fileName(),
                payloadEntryName(prepared.fileName()),
                prepared.contentType(),
                prepared.content().length,
                prepared.pdfStamped(),
                signer.dni(),
                signer.apellidosNombres(),
                signer.ubigeo(),
                hashHex,
                signatureBase64,
                algorithm,
                signedAt.toString(),
                certificate
        );
    }

    public String signedFileName(String originalFileName) {
        String base = safeFileName(originalFileName == null || originalFileName.isBlank() ? "documento.bin" : originalFileName);
        return base + ".uni-signed";
    }

    public String payloadEntryName(String originalFileName) {
        return "payload/" + safeFileName(originalFileName == null || originalFileName.isBlank() ? "documento.bin" : originalFileName);
    }

    private String safeFileName(String fileName) {
        String onlyName = fileName.replace('\\', '/');
        int slash = onlyName.lastIndexOf('/');
        if (slash >= 0) onlyName = onlyName.substring(slash + 1);
        return onlyName.replaceAll("[^a-zA-Z0-9._ -]", "_");
    }
}
