package pe.edu.uni.firma.signature.container;

public record SignatureMetadata(
        String envelopeVersion,
        String originalFileName,
        String payloadEntryName,
        String originalContentType,
        long payloadSizeBytes,
        boolean pdfStamped,
        String dni,
        String apellidosNombres,
        String ubigeo,
        String hashHex,
        String signatureBase64,
        String algorithm,
        String signedAt,
        EmbeddedCertificate certificate
) {}
