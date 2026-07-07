package pe.edu.uni.firma.signature.dto;

import java.time.Instant;

public record SignedDocumentResponse(
        Long id,
        String dni,
        String apellidosNombres,
        String ubigeo,
        String originalFileName,
        String signedFileName,
        String contentType,
        long fileSizeBytes,
        long signedFileSizeBytes,
        String containerFormat,
        boolean pdfStamped,
        String algorithm,
        String hashHex,
        String signatureBase64,
        String certificateIssuer,
        String downloadSignedUrl,
        Instant createdAt
) {}
