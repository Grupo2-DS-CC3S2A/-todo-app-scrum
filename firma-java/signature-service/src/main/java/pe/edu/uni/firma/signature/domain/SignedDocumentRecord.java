package pe.edu.uni.firma.signature.domain;

import java.time.Instant;

public record SignedDocumentRecord(
        Long id,
        String dni,
        String apellidosNombres,
        String ubigeo,
        String originalFileName,
        String contentType,
        long fileSizeBytes,
        byte[] documentBytes,
        String signatureBase64,
        String hashHex,
        String algorithm,
        String signedFileName,
        String signedContentType,
        long signedFileSizeBytes,
        byte[] signedFileBytes,
        String certificateJson,
        boolean pdfStamped,
        Instant createdAt
) {}
