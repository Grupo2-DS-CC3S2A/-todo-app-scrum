package pe.edu.uni.firma.signature.dto;

import java.time.Instant;

public record DocumentMetadataResponse(
        Long id,
        String dni,
        String originalFileName,
        String signedFileName,
        String contentType,
        long fileSizeBytes,
        long signedFileSizeBytes,
        String hashHex,
        boolean pdfStamped,
        Instant createdAt
) {}
